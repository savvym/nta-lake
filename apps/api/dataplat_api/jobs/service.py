"""JobsService：jobs 表 CRUD + RQ enqueue（spec rq-worker-skeleton-20260517 AC-4）。

事务模式：MVP 直接 commit 单次写；不显式 begin（与 commit-api-mvp 一致）。
RQ enqueue 失败时已 INSERT 的 row 会被 DELETE 回滚（一致性优先）。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.jobs.redis_client import get_queue
from dataplat_api.models import JobORM


class JobsService:
    """无 state；静态方法。"""

    # job_type → worker task 函数路径
    _TASK_DISPATCH = {
        "ingest": "dataplat_api.jobs.tasks.run_ingest_job",
        "process": "dataplat_api.jobs.tasks.run_process_job",
        "pipeline": "dataplat_api.jobs.tasks.run_pipeline_job",
    }

    @staticmethod
    async def enqueue(
        session: AsyncSession,
        job_type: str,
        payload: dict[str, Any],
    ) -> JobORM:
        """INSERT JobORM(status=queued) + RQ enqueue；失败 → DELETE + raise。"""
        task_path = JobsService._TASK_DISPATCH.get(job_type)
        if task_path is None:
            raise ValueError(f"未知 job_type: {job_type}")

        job = JobORM(
            id=uuid.uuid4(),
            type=job_type,
            status="queued",
            payload=payload,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)

        try:
            get_queue().enqueue(task_path, str(job.id))
        except Exception:
            await session.delete(job)
            await session.commit()
            raise
        return job

    @staticmethod
    async def get_by_id(
        session: AsyncSession, job_id: uuid.UUID | str
    ) -> JobORM | None:
        if isinstance(job_id, str):
            try:
                job_id = uuid.UUID(job_id)
            except ValueError:
                return None
        stmt = select(JobORM).where(JobORM.id == job_id)
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def mark_running(
        session: AsyncSession, job_id: uuid.UUID | str
    ) -> None:
        job = await JobsService.get_by_id(session, job_id)
        if job is None:
            return
        job.status = "running"
        job.started_at = datetime.now(UTC)
        await session.commit()

    @staticmethod
    async def mark_succeeded(
        session: AsyncSession,
        job_id: uuid.UUID | str,
        result: dict[str, Any],
    ) -> None:
        job = await JobsService.get_by_id(session, job_id)
        if job is None:
            return
        job.status = "succeeded"
        job.result = result
        job.completed_at = datetime.now(UTC)
        await session.commit()

    @staticmethod
    async def mark_failed(
        session: AsyncSession,
        job_id: uuid.UUID | str,
        error: str,
    ) -> None:
        job = await JobsService.get_by_id(session, job_id)
        if job is None:
            return
        job.status = "failed"
        job.error = error
        job.completed_at = datetime.now(UTC)
        await session.commit()
