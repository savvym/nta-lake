"""worker 可调用的 RQ task 函数（spec rq-worker-skeleton-20260517 AC-5）。

设计要点：
- `run_ingest_job(job_id: str)` 是同步函数（RQ 默认）；内部 `asyncio.run` 包 async session
- 独立 async engine（不依赖 FastAPI session lifecycle；跨进程隔离）
- 异常 swallow + mark_failed；不 re-raise（MVP 不 retry）
"""

from __future__ import annotations

import asyncio
import logging
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# 触发内置 adapter / processor 注册（worker 进程不 import main.py；必须在 tasks
# 模块里显式 import，否则 Registry 空）
from dataplat_api import adapters as _adapters  # noqa: F401
from dataplat_api import processors as _processors  # noqa: F401
from dataplat_api.jobs.service import JobsService
from dataplat_api.models import RepositoryORM
from dataplat_api.runner.adapter_runner import AdapterRunner
from dataplat_api.runner.processor_runner import ProcessorRunner
from dataplat_api.schemas.ingest import IngestRequest
from dataplat_api.schemas.process import ProcessRequest
from dataplat_api.storage import get_blob_store

_logger = logging.getLogger("dataplat.jobs.tasks")

_DEFAULT_DB_URL = (
    "postgresql+asyncpg://dataplat:dataplat@localhost:5432/dataplat"
)


def _make_engine_factory() -> async_sessionmaker[AsyncSession]:
    """独立 async engine + sessionmaker；不复用 FastAPI 进程 engine。"""
    url = os.environ.get("DATAPLAT_DATABASE_URL", _DEFAULT_DB_URL)
    engine = create_async_engine(url, pool_pre_ping=True)
    return async_sessionmaker(bind=engine, expire_on_commit=False)


def run_ingest_job(job_id: str) -> None:
    """RQ worker 入口（同步函数；内部 asyncio.run 包 async 实现）。

    异常 swallow + mark_failed；不 re-raise（RQ 默认会把 failed 状态写入
    Redis，但 MVP 用业务表 jobs 持久化状态）。
    """
    try:
        asyncio.run(_run_ingest_job_async(job_id))
    except Exception as exc:  # noqa: BLE001
        _logger.exception("run_ingest_job %s 顶层未捕获异常", job_id)
        # 顶层兜底：尝试 mark_failed（再失败就只能依赖日志）
        try:
            asyncio.run(_mark_failed_sync_wrapper(job_id, str(exc)))
        except Exception:  # noqa: BLE001
            _logger.exception("mark_failed 兜底也失败 job=%s", job_id)


async def _mark_failed_sync_wrapper(job_id: str, error: str) -> None:
    factory = _make_engine_factory()
    async with factory() as session:
        await JobsService.mark_failed(session, job_id, error)


async def _run_ingest_job_async(job_id: str) -> None:
    factory = _make_engine_factory()
    store = get_blob_store()

    async with factory() as session:
        job = await JobsService.get_by_id(session, job_id)
        if job is None:
            _logger.warning("run_ingest_job %s 不存在", job_id)
            return

        await JobsService.mark_running(session, job_id)

        try:
            payload = job.payload
            owner = payload["owner"]
            name = payload["name"]
            request_data = payload["request"]
            ingest_request = IngestRequest.model_validate(request_data)

            # 查 repo
            stmt = select(RepositoryORM).where(
                RepositoryORM.owner == owner, RepositoryORM.name == name
            )
            repo = (await session.execute(stmt)).scalar_one_or_none()
            if repo is None:
                raise ValueError(f"Repository {owner}/{name} 不存在")

            commit, dedup, result = await AdapterRunner.run(
                session, store, repo.id, ingest_request
            )

            await JobsService.mark_succeeded(
                session,
                job_id,
                result={
                    "commit_hash": commit.hash,
                    "deduplicated": dedup,
                    "ingest_summary": {
                        "asset_count": result.asset_count,
                        "file_count": result.file_count,
                        "bytes_written": result.bytes_written,
                        "notes": result.notes,
                    },
                },
            )
        except Exception as exc:  # noqa: BLE001
            _logger.exception("run_ingest_job %s adapter 执行失败", job_id)
            await JobsService.mark_failed(session, job_id, str(exc))


def run_process_job(job_id: str) -> None:
    """RQ worker 入口；processor 任务（spec processor-framework AC-7）。"""
    try:
        asyncio.run(_run_process_job_async(job_id))
    except Exception as exc:  # noqa: BLE001
        _logger.exception("run_process_job %s 顶层未捕获异常", job_id)
        try:
            asyncio.run(_mark_failed_sync_wrapper(job_id, str(exc)))
        except Exception:  # noqa: BLE001
            _logger.exception("mark_failed 兜底也失败 job=%s", job_id)


async def _run_process_job_async(job_id: str) -> None:
    factory = _make_engine_factory()
    store = get_blob_store()

    async with factory() as session:
        job = await JobsService.get_by_id(session, job_id)
        if job is None:
            _logger.warning("run_process_job %s 不存在", job_id)
            return

        await JobsService.mark_running(session, job_id)

        try:
            payload = job.payload
            process_request = ProcessRequest.model_validate(payload)

            # 查 source repo
            source_stmt = select(RepositoryORM).where(
                RepositoryORM.owner == process_request.source_owner,
                RepositoryORM.name == process_request.source_name,
            )
            source_repo = (
                await session.execute(source_stmt)
            ).scalar_one_or_none()
            if source_repo is None:
                raise ValueError(
                    f"Source repository {process_request.source_owner}/"
                    f"{process_request.source_name} 不存在"
                )

            # 解析 source commit_hash
            source_commit_hash = process_request.source_commit_hash
            if source_commit_hash is None and process_request.source_ref:
                # 通过 ref 查
                from dataplat_api.services.ref import RefService

                ref = await RefService.get_by_name(
                    session, source_repo.id, process_request.source_ref
                )
                if ref is None:
                    raise ValueError(
                        f"Source ref {process_request.source_ref} 在 "
                        f"{process_request.source_owner}/{process_request.source_name} 不存在"
                    )
                source_commit_hash = ref.commit_hash
            if source_commit_hash is None:
                raise ValueError("source_commit_hash 或 source_ref 必须提供其一")

            # 查 target repo
            target_stmt = select(RepositoryORM).where(
                RepositoryORM.owner == process_request.target_owner,
                RepositoryORM.name == process_request.target_name,
            )
            target_repo = (
                await session.execute(target_stmt)
            ).scalar_one_or_none()
            if target_repo is None:
                raise ValueError(
                    f"Target repository {process_request.target_owner}/"
                    f"{process_request.target_name} 不存在"
                )

            commit, dedup, result = await ProcessorRunner.run(
                session=session,
                store=store,
                source_repo_id=source_repo.id,
                source_commit_hash=source_commit_hash,
                target_repo_id=target_repo.id,
                processor_name=process_request.processor_name,
                processor_version=process_request.processor_version,
                config=process_request.config,
                author_id=process_request.author_id,
                message=process_request.message,
                ref=process_request.ref,
            )

            await JobsService.mark_succeeded(
                session,
                job_id,
                result={
                    "commit_hash": commit.hash,
                    "deduplicated": dedup,
                    "process_summary": {
                        "record_count": result.record_count,
                        "file_count": result.file_count,
                        "bytes_written": result.bytes_written,
                        "notes": result.notes,
                    },
                },
            )
        except Exception as exc:  # noqa: BLE001
            _logger.exception("run_process_job %s processor 执行失败", job_id)
            await JobsService.mark_failed(session, job_id, str(exc))


def run_pipeline_job(job_id: str) -> None:
    """RQ worker 入口；pipeline 任务（spec pipeline-orchestrator-mvp-20260518 T-6c，AC-10）。"""
    try:
        asyncio.run(_run_pipeline_job_async(job_id))
    except Exception as exc:  # noqa: BLE001
        _logger.exception("run_pipeline_job %s 顶层未捕获异常", job_id)
        try:
            asyncio.run(_mark_failed_sync_wrapper(job_id, str(exc)))
        except Exception:  # noqa: BLE001
            _logger.exception("mark_failed 兜底也失败 job=%s", job_id)


async def _run_pipeline_job_async(job_id: str) -> None:
    import uuid as _uuid

    from dataplat_api.runner.orchestrator import PipelineOrchestrator
    from dataplat_api.schemas.pipeline import Recipe

    factory = _make_engine_factory()
    store = get_blob_store()

    async with factory() as session:
        job = await JobsService.get_by_id(session, job_id)
        if job is None:
            _logger.warning("run_pipeline_job %s 不存在", job_id)
            return

        await JobsService.mark_running(session, job_id)

        try:
            payload = job.payload
            run_id = _uuid.UUID(payload["run_id"])
            recipe = Recipe.model_validate(payload["recipe"])
            author_id = str(payload["author_id"])

            run = await PipelineOrchestrator.run_pipeline(
                session=session,
                store=store,
                recipe=recipe,
                author_id=author_id,
                run_id=run_id,
            )

            await JobsService.mark_succeeded(
                session,
                job_id,
                result={
                    "run_id": str(run.id),
                    "status": run.status,
                    "error": run.error,
                },
            )
        except Exception as exc:  # noqa: BLE001
            _logger.exception("run_pipeline_job %s orchestrator 执行失败", job_id)
            await JobsService.mark_failed(session, job_id, str(exc))
