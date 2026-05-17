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

from dataplat_api.jobs.service import JobsService
from dataplat_api.models import RepositoryORM
from dataplat_api.runner.adapter_runner import AdapterRunner
from dataplat_api.schemas.ingest import IngestRequest
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


