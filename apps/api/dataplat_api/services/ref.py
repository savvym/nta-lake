"""RefService：ref 读写。

读：`get_by_name`（spec repo-files-tab-20260517 AC-2）。
写：`upsert_ref`（spec pipeline-orchestrator-mvp-20260518 T-0 v2 SHOULD #1）；
  原逻辑嵌在 CommitService.create_commit，本 change 抽公共 helper 供 orchestrator
  cache hit 分支复用。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.models import RefORM


class RefService:
    """无 state；静态方法。"""

    @staticmethod
    async def get_by_name(
        session: AsyncSession,
        repo_id: uuid.UUID,
        name: str,
    ) -> RefORM | None:
        stmt = select(RefORM).where(
            RefORM.repo_id == repo_id,
            RefORM.name == name,
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def upsert_ref(
        session: AsyncSession,
        repo_id: uuid.UUID,
        name: str,
        commit_hash: str,
    ) -> RefORM:
        existing = await RefService.get_by_name(session, repo_id, name)
        if existing is None:
            row = RefORM(
                id=uuid.uuid4(),
                repo_id=repo_id,
                name=name,
                commit_hash=commit_hash,
            )
            session.add(row)
            return row
        existing.commit_hash = commit_hash
        return existing
