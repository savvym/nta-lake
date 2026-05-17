"""RefService：ref 查询（spec repo-files-tab-20260517 AC-2）。

ref 写操作（upsert / delete）由 CommitService.create_commit 已实现；本变更只加读。
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
