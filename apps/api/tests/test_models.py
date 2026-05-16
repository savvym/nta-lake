"""ORM smoke test：依赖 docker-compose Postgres。

每个测试用 fresh engine + dispose，绕开 asyncpg + pytest-asyncio 跨测试
event loop 时序问题（详见 SQLAlchemy async docs §Using asyncio scoped session）。

需要先设置 `DATAPLAT_DATABASE_URL` 环境变量。
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Awaitable, Callable

import pytest
from dataplat_api.models import CommitORM, RepositoryORM
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _db_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not _db_url(),
    reason="DATAPLAT_DATABASE_URL 未设置；ORM smoke 测试跳过",
)


async def _with_session(body: Callable[[AsyncSession], Awaitable[None]]) -> None:
    """临时 engine + session；测试结束后立即 dispose。"""
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            await body(session)
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_repositories_crud() -> None:
    async def body(session: AsyncSession) -> None:
        repo = RepositoryORM(
            id=uuid.uuid4(),
            owner="test",
            name="repo-smoke-" + uuid.uuid4().hex[:8],
            layer="bronze",
            subtype="pdf",
            visibility="private",
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)
        assert repo.created_at is not None

        stmt = select(RepositoryORM).where(RepositoryORM.id == repo.id)
        result = (await session.execute(stmt)).scalar_one()
        assert result.owner == "test"
        assert result.layer == "bronze"

        await session.delete(result)
        await session.commit()

    await _with_session(body)


@pytest.mark.asyncio
async def test_commit_with_lineage_jsonb() -> None:
    async def body(session: AsyncSession) -> None:
        repo_id = uuid.uuid4()
        repo = RepositoryORM(
            id=repo_id,
            owner="test",
            name="repo-lineage-" + uuid.uuid4().hex[:8],
            layer="silver",
            subtype="text-corpus",
        )
        session.add(repo)
        await session.commit()

        tree_hash = uuid.uuid4().hex + uuid.uuid4().hex
        commit_hash = uuid.uuid4().hex + uuid.uuid4().hex
        await session.execute(
            text("INSERT INTO trees (hash, repo_id) VALUES (:h, :rid)"),
            {"h": tree_hash, "rid": repo_id},
        )
        await session.commit()

        commit = CommitORM(
            hash=commit_hash,
            repo_id=repo_id,
            tree_hash=tree_hash,
            parents=[],
            author_id="user1",
            message="lineage smoke",
            lineage_json={
                "produced_by": {
                    "kind": "processor",
                    "name": "noop",
                    "version": "0.0",
                    "config_hash": "f" * 64,
                },
                "inputs": [],
                "run_id": "r-smoke",
                "env": {"python": "3.11"},
            },
        )
        session.add(commit)
        await session.commit()
        await session.refresh(commit)

        assert commit.lineage_json is not None
        assert commit.lineage_json["produced_by"]["kind"] == "processor"
        assert commit.lineage_json["run_id"] == "r-smoke"

        # 清理顺序：commit 先 flush，再删 tree（避免 FK 违反）
        await session.delete(commit)
        await session.commit()
        await session.execute(text("DELETE FROM trees WHERE hash = :h"), {"h": tree_hash})
        await session.commit()
        await session.delete(repo)
        await session.commit()

    await _with_session(body)
