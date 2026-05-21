"""Budget router 集成测试（W4-5 AC-4）。

3 tests（env-gated：缺 DATAPLAT_DATABASE_URL → SKIP；env 就位 → PASS）：
1. test_a_admin_set_and_get_budget  — POST 设 0.5 → GET 拿到 limit_usd=0.5 + current_usd=0
2. test_b_non_admin_returns_403     — 非 admin POST → 403
3. test_c_admin_delete_budget       — DELETE 清预算 → cleared=True；再 GET → limit_usd=None
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
from dataplat_api.auth.password import hash_password
from dataplat_api.llm.cost import get_cost_controller, reset_cost_controller
from dataplat_api.main import app
from dataplat_api.models import RepositoryORM, UserORM
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _db_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not _db_url(),
    reason="DATAPLAT_DATABASE_URL 未设置；budget router 集成测试跳过",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_user(role: str) -> dict:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    prefix = "a" if role == "admin" else "u"
    username = f"{prefix}_{uuid.uuid4().hex[:8]}"
    password = "test-password-x"
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


async def _delete_repo(owner: str, name: str) -> None:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(
            delete(RepositoryORM).where(
                RepositoryORM.owner == owner,
                RepositoryORM.name == name,
            )
        )
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
def _reset_cost_controller():
    """每个测试前后清 cost controller 单例，避免跨测试预算状态污染。"""
    reset_cost_controller()
    yield
    reset_cost_controller()


# ---------------------------------------------------------------------------
# Test a: admin POST 设预算 + GET 拿到
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_admin_set_and_get_budget(admin_user: dict) -> None:
    """POST 设 limit_usd=0.5 → GET 拿到 limit_usd=0.5 + current_usd=0.0。"""
    repo_name = f"repo-budget-a-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as client:
            await _login(client, admin_user)
            # 创建 repo
            r_create = await client.post(
                "/repos",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "layer": "bronze",
                    "subtype": "pdf",
                    "visibility": "public",
                },
            )
            assert r_create.status_code == 201, r_create.text

            # POST 设预算
            r_set = await client.post(
                f"/repos/test/{repo_name}/llm-budget",
                json={"limit_usd": 0.5, "reset_window": "monthly"},
            )
            assert r_set.status_code == 200, r_set.text
            body_set = r_set.json()
            assert body_set["limit_usd"] == pytest.approx(0.5)
            assert body_set["current_usd"] == pytest.approx(0.0)
            scope = body_set["scope"]
            assert scope.startswith("repo:")

            # GET 拿到
            r_get = await client.get(f"/repos/test/{repo_name}/llm-budget")
            assert r_get.status_code == 200, r_get.text
            body_get = r_get.json()
            assert body_get["limit_usd"] == pytest.approx(0.5)
            assert body_get["current_usd"] == pytest.approx(0.0)
            assert body_get["scope"] == scope
    finally:
        await _delete_repo("test", repo_name)


# ---------------------------------------------------------------------------
# Test b: 非 admin → 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_b_non_admin_returns_403(admin_user: dict, normal_user: dict) -> None:
    """普通用户 POST budget → 403。"""
    repo_name = f"repo-budget-b-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as client:
            await _login(client, admin_user)
            r_create = await client.post(
                "/repos",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "layer": "bronze",
                    "subtype": "pdf",
                    "visibility": "public",
                },
            )
            assert r_create.status_code == 201, r_create.text

        async with AsyncClient(transport=transport, base_url="https://test") as client:
            await _login(client, normal_user)
            r_set = await client.post(
                f"/repos/test/{repo_name}/llm-budget",
                json={"limit_usd": 1.0},
            )
            assert r_set.status_code == 403, r_set.text
    finally:
        await _delete_repo("test", repo_name)


# ---------------------------------------------------------------------------
# Test c: admin DELETE 清预算
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_c_admin_delete_budget(admin_user: dict) -> None:
    """DELETE 清预算 → cleared=True；再 GET → limit_usd=None。"""
    repo_name = f"repo-budget-c-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as client:
            await _login(client, admin_user)
            await client.post(
                "/repos",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "layer": "bronze",
                    "subtype": "pdf",
                    "visibility": "public",
                },
            )

            # 先设预算
            await client.post(
                f"/repos/test/{repo_name}/llm-budget",
                json={"limit_usd": 1.0},
            )

            # 删除
            r_del = await client.delete(f"/repos/test/{repo_name}/llm-budget")
            assert r_del.status_code == 200, r_del.text
            body_del = r_del.json()
            assert body_del["cleared"] is True

            # 再 GET → limit_usd=None
            r_get = await client.get(f"/repos/test/{repo_name}/llm-budget")
            assert r_get.status_code == 200, r_get.text
            body_get = r_get.json()
            assert body_get["limit_usd"] is None
    finally:
        await _delete_repo("test", repo_name)
