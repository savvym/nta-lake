"""SQLAlchemy 2.0 async engine + session factory + get_session() 依赖。

环境变量 `DATAPLAT_DATABASE_URL` 控制连接串；默认连本地 docker-compose 起的
postgres:16（dataplat/dataplat@localhost:5432/dataplat）。

`get_session()` 是 async generator 依赖，路由用 `Depends(get_session)`。
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

DEFAULT_DATABASE_URL = "postgresql+asyncpg://dataplat:dataplat@localhost:5432/dataplat"


def _database_url() -> str:
    return os.environ.get("DATAPLAT_DATABASE_URL", DEFAULT_DATABASE_URL)


# pytest 环境下用 NullPool：每次 acquire 都建新 connection（避免跨 event-loop
# 复用 stale connection，asyncpg + pytest-asyncio 会触发 "Event loop is closed"）。
# 生产环境用默认 pool；性能差异在本变更 MVP 阶段可接受，后续 follow-up 可调。
_USE_NULL_POOL = os.environ.get("PYTEST_CURRENT_TEST") is not None or os.environ.get(
    "DATAPLAT_USE_NULL_POOL"
) == "1"


engine: AsyncEngine = create_async_engine(
    _database_url(),
    echo=False,
    pool_pre_ping=True,
    poolclass=NullPool if _USE_NULL_POOL else None,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：yield 一个会话，请求结束自动关闭。"""
    async with AsyncSessionLocal() as session:
        yield session
