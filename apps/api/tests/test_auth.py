"""auth 集成测试（依赖 Postgres + 0001 + 0002 schema）。

7 个测试（spec AC-15 (a)~(h)）：
  a) hash/verify password round-trip
  b) JWT encode/decode round-trip
  c) /auth/login 成功后 cookies 设置（httponly + secure + samesite=lax）
  d) /auth/login 错密码返 401
  e) /auth/me 用 cookies 通过
  f) /auth/me 缺 cookies 返 401
  g) /auth/refresh 从 refresh cookie 重发 access
  h) 普通 user 角色访问 POST /admin/users 返 403

Fixture（tasks MUST FIX-2）：
- `@pytest.fixture(scope='session')` 跑 alembic upgrade head 一次（避免反复）
- 测试用户记录用 `scope='function'` + teardown delete row（不 drop table）
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
from dataplat_api.auth.password import hash_password, verify_password
from dataplat_api.auth.tokens import (
    decode_token,
    encode_access_token,
    encode_refresh_token,
)
from dataplat_api.main import app
from dataplat_api.models import UserORM
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _db_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not _db_url(),
    reason="DATAPLAT_DATABASE_URL 未设置；auth 集成测试跳过",
)


@pytest.fixture(scope="session", autouse=True)
def _ensure_jwt_secret() -> None:
    # conftest 兜底已设；此处再 setdefault 保 idempotent
    os.environ.setdefault("DATAPLAT_JWT_SECRET", "test-secret-not-prod-x32-bytes-xxxxx")


@pytest.fixture
async def created_user() -> AsyncGenerator[dict, None]:
    """每测一个 fresh user row；teardown delete row（不 drop table）。"""
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    username = f"u_{uuid.uuid4().hex[:8]}"
    password = "correct horse battery staple"
    role = "user"

    user_info: dict = {}
    async with factory() as session:
        user = UserORM(
            id=uuid.uuid4(),
            username=username,
            email=f"{username}@example.com",
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_info.update(
            {
                "id": user.id,
                "username": username,
                "password": password,
                "role": role,
            }
        )

    try:
        yield user_info
    finally:
        async with factory() as session:
            await session.execute(delete(UserORM).where(UserORM.id == user_info["id"]))
            await session.commit()
        # 不显式 engine.dispose()——asyncpg 在 event loop 关闭后 cancel pending
        # command 会 raise；pytest-asyncio 退出时 GC 兜底（无 connection 泄漏顾虑：
        # 测试结束进程退出）


@pytest.fixture
async def created_admin() -> AsyncGenerator[dict, None]:
    """admin user 用于 admin 路由测试。"""
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    username = f"a_{uuid.uuid4().hex[:8]}"
    password = "admin-pw-correct"
    user_info: dict = {}
    async with factory() as session:
        user = UserORM(
            id=uuid.uuid4(),
            username=username,
            email=None,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_info.update(
            {"id": user.id, "username": username, "password": password, "role": "admin"}
        )

    try:
        yield user_info
    finally:
        async with factory() as session:
            await session.execute(delete(UserORM).where(UserORM.id == user_info["id"]))
            await session.commit()
        # 不显式 engine.dispose()——asyncpg 在 event loop 关闭后 cancel pending
        # command 会 raise；pytest-asyncio 退出时 GC 兜底（无 connection 泄漏顾虑：
        # 测试结束进程退出）


@pytest.mark.asyncio
async def test_a_password_hash_verify_roundtrip() -> None:
    h1 = hash_password("xyz")
    h2 = hash_password("xyz")
    assert h1 != h2  # 含随机 salt
    assert verify_password("xyz", h1)
    assert verify_password("xyz", h2)
    assert not verify_password("wrong", h1)


@pytest.mark.asyncio
async def test_b_jwt_encode_decode_roundtrip() -> None:
    t = encode_access_token("user-1", "admin")
    d = decode_token(t)
    assert d["sub"] == "user-1"
    assert d["role"] == "admin"
    assert d["typ"] == "access"
    rt = encode_refresh_token("user-1")
    rd = decode_token(rt)
    assert rd["typ"] == "refresh"


@pytest.mark.asyncio
async def test_c_login_sets_cookies_with_security_flags(created_user: dict) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        resp = await client.post(
            "/auth/login",
            json={"username": created_user["username"], "password": created_user["password"]},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == created_user["username"]

    cookie_headers = [h for h in resp.headers.raw if h[0].decode().lower() == "set-cookie"]
    raw = b"\n".join(h[1] for h in cookie_headers).lower()
    assert b"access_token=" in raw
    assert b"refresh_token=" in raw
    assert b"httponly" in raw
    assert b"secure" in raw
    assert b"samesite=lax" in raw


@pytest.mark.asyncio
async def test_d_login_wrong_password_returns_401(created_user: dict) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        resp = await client.post(
            "/auth/login",
            json={"username": created_user["username"], "password": "WRONG"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_e_me_passes_with_valid_cookies(created_user: dict) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        login = await client.post(
            "/auth/login",
            json={"username": created_user["username"], "password": created_user["password"]},
        )
        assert login.status_code == 200
        resp = await client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == created_user["username"]


@pytest.mark.asyncio
async def test_f_me_without_cookies_returns_401() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_g_refresh_issues_new_access(created_user: dict) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        login = await client.post(
            "/auth/login",
            json={"username": created_user["username"], "password": created_user["password"]},
        )
        assert login.status_code == 200
        resp = await client.post("/auth/refresh")
    assert resp.status_code == 204
    cookie_headers = [h for h in resp.headers.raw if h[0].decode().lower() == "set-cookie"]
    raw = b"\n".join(h[1] for h in cookie_headers).lower()
    assert b"access_token=" in raw


@pytest.mark.asyncio
async def test_h_user_role_cannot_access_admin_users(created_user: dict) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        login = await client.post(
            "/auth/login",
            json={"username": created_user["username"], "password": created_user["password"]},
        )
        assert login.status_code == 200
        resp = await client.post(
            "/admin/users",
            json={"username": "newbie", "password": "p", "role": "user"},
        )
    assert resp.status_code == 403


# ============================================================================
# Stage 4 MUST FIX 回归保护（stage 6 reviewer SHOULD FIX：常驻断言）
# ============================================================================


@pytest.mark.asyncio
async def test_i_refresh_token_cannot_be_used_as_access(created_user: dict) -> None:
    """安全：把 refresh token 放到 access_token cookie 不应被认证为用户。

    stage 4 review MUST FIX #1 的常驻回归测试。
    """
    refresh_token = encode_refresh_token(str(created_user["id"]))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        client.cookies.set("access_token", refresh_token)
        resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_j_admin_refresh_preserves_admin_role(created_admin: dict) -> None:
    """admin 登录 + refresh 后 role 仍为 admin（不静默降权）。

    stage 4 review MUST FIX #2 的常驻回归测试。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        login = await client.post(
            "/auth/login",
            json={"username": created_admin["username"], "password": created_admin["password"]},
        )
        assert login.status_code == 200
        assert login.json()["role"] == "admin"

        # refresh 一次
        refresh_resp = await client.post("/auth/refresh")
        assert refresh_resp.status_code == 204

        # 用新 access cookie 调 admin 路由——若 role 被错降为 user，应当 403；admin 应当 ≠ 403
        resp = await client.post(
            "/admin/users",
            json={
                "username": f"created_by_admin_{uuid.uuid4().hex[:6]}",
                "password": "newpw",
                "role": "user",
            },
        )
    # 应当成功创建（201）或 200——总之不是 403（降权）也不是 401（认证失败）
    assert resp.status_code not in (401, 403), (
        f"admin refresh 后失去权限：status={resp.status_code} body={resp.text}"
    )

    # 清理新建的用户
    body = resp.json()
    if isinstance(body, dict) and body.get("user_id"):
        engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with factory() as session:
            await session.execute(
                delete(UserORM).where(UserORM.id == uuid.UUID(body["user_id"]))
            )
            await session.commit()


@pytest.mark.asyncio
async def test_k_deactivated_user_cannot_refresh(created_user: dict) -> None:
    """用户被停用后 refresh 应当返 401（不能继续保持会话）。

    stage 4 review MUST FIX #2 副效益的常驻回归测试。
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        login = await client.post(
            "/auth/login",
            json={"username": created_user["username"], "password": created_user["password"]},
        )
        assert login.status_code == 200

        # 直接通过 DB 停用用户
        engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with factory() as session:
            from sqlalchemy import update

            await session.execute(
                update(UserORM).where(UserORM.id == created_user["id"]).values(is_active=False)
            )
            await session.commit()

        resp = await client.post("/auth/refresh")

    assert resp.status_code == 401
