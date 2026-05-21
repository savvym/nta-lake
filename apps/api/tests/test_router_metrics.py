"""Metrics router 集成测试（W4-7 AC-4）。

2 tests（env-gated：缺 DATAPLAT_DATABASE_URL → SKIP；env 就位 → PASS）：
1. test_admin_get_metrics  — admin GET /metrics → 200 + JSON 字段 operators + collected_at
2. test_non_admin_returns_403  — 非 admin GET /metrics → 403
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
from dataplat_api.auth.password import hash_password
from dataplat_api.main import app
from dataplat_api.models import UserORM
from dataplat_core.metrics import reset_metrics_registry
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _db_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not _db_url(),
    reason="DATAPLAT_DATABASE_URL 未设置；metrics router 集成测试跳过",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_user(role: str) -> dict:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    prefix = "a" if role == "admin" else "u"
    username = f"{prefix}_{uuid.uuid4().hex[:8]}"
    password = "test-password-metrics"
    async with factory() as session:
        user = UserORM(
            id=uuid.uuid4(),
            username=username,
            email=None,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {"id": user.id, "username": username, "password": password, "role": role}


async def _delete_user(user_id: uuid.UUID) -> None:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(delete(UserORM).where(UserORM.id == user_id))
        await session.commit()


async def _login(client: AsyncClient, user: dict) -> None:
    resp = await client.post(
        "/auth/login",
        json={"username": user["username"], "password": user["password"]},
    )
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def admin_user() -> AsyncGenerator[dict, None]:
    info = await _make_user("admin")
    try:
        yield info
    finally:
        await _delete_user(info["id"])


@pytest.fixture
async def normal_user() -> AsyncGenerator[dict, None]:
    info = await _make_user("user")
    try:
        yield info
    finally:
        await _delete_user(info["id"])


@pytest.fixture(autouse=True)
def _reset_metrics():
    """每个测试前后清 metrics registry 单例，避免跨测试数据污染。"""
    reset_metrics_registry()
    yield
    reset_metrics_registry()


# ---------------------------------------------------------------------------
# Test 1: admin GET /metrics → 200 + 字段齐
# ---------------------------------------------------------------------------


async def test_admin_get_metrics(admin_user: dict) -> None:
    """admin GET /metrics → 200 + JSON 含 operators list + collected_at string。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        await _login(client, admin_user)
        resp = await client.get("/metrics")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "operators" in body, f"缺 operators 字段：{body}"
        assert "collected_at" in body, f"缺 collected_at 字段：{body}"
        assert isinstance(body["operators"], list)
        assert isinstance(body["collected_at"], str)
        # collected_at 应为 ISO 8601 格式（含 T 分隔符）
        assert "T" in body["collected_at"], f"collected_at 格式异常：{body['collected_at']}"


# ---------------------------------------------------------------------------
# Test 2: 非 admin → 403
# ---------------------------------------------------------------------------


async def test_non_admin_returns_403(normal_user: dict) -> None:
    """普通用户 GET /metrics → 403。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        await _login(client, normal_user)
        resp = await client.get("/metrics")
        assert resp.status_code == 403, resp.text
