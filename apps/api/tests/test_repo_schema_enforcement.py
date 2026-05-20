"""W1-3 silver-schema-enforce AC-2 / AC-3 集成测试。

AC-2: POST /repos layer=silver 缺 schema_id → 422；缺 row_format → 422；
      schema_id="unknown" → 422；schema_id 是 gold 的但 layer=silver → 422。
AC-3: POST /repos layer=silver 合法 → 201 + 响应含 schema_id/row_format；
      GET 同上；layer=bronze 传 schema_id → 422。

依赖（同 test_repos.py）：
- Postgres（DATAPLAT_DATABASE_URL）
- conftest 早设 JWT_SECRET + USE_NULL_POOL
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
from dataplat_api.auth.password import hash_password
from dataplat_api.main import app
from dataplat_api.models import UserORM
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _db_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


def _minio_endpoint() -> str | None:
    return os.environ.get("DATAPLAT_MINIO_ENDPOINT")


pytestmark = pytest.mark.skipif(
    not _db_url(),
    reason="DATAPLAT_DATABASE_URL 未设置；schema_enforcement 集成测试跳过",
)


# --------- helpers ---------


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
        info = {"id": user.id, "username": username, "password": password, "role": role}
    return info


async def _delete_user(user_id: uuid.UUID) -> None:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(delete(UserORM).where(UserORM.id == user_id))
        await session.commit()


async def _delete_repo_cascade(owner: str, name: str) -> None:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        repo_row = (
            await session.execute(
                text("SELECT id FROM repositories WHERE owner=:o AND name=:n"),
                {"o": owner, "n": name},
            )
        ).first()
        if repo_row is None:
            await session.commit()
            return
        repo_id = repo_row[0]
        await session.execute(text("DELETE FROM refs WHERE repo_id=:r"), {"r": repo_id})
        await session.execute(text("DELETE FROM commits WHERE repo_id=:r"), {"r": repo_id})
        await session.execute(text("DELETE FROM trees WHERE repo_id=:r"), {"r": repo_id})
        await session.execute(text("DELETE FROM repositories WHERE id=:r"), {"r": repo_id})
        await session.commit()


@pytest.fixture
async def admin_user() -> AsyncGenerator[dict, None]:
    info = await _make_user("admin")
    try:
        yield info
    finally:
        await _delete_user(info["id"])


async def _login(client: AsyncClient, user: dict) -> None:
    resp = await client.post(
        "/auth/login",
        json={"username": user["username"], "password": user["password"]},
    )
    assert resp.status_code == 200, f"login failed: {resp.text}"


# --------- AC-2: 4 种 422 ---------


@pytest.mark.asyncio
async def test_silver_create_422(admin_user: dict) -> None:
    """AC-2: 4 种 422：缺 schema_id / 缺 row_format / schema 未注册 / 跨层。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as c:
        await _login(c, admin_user)

        # 1. 缺 schema_id
        r1 = await c.post(
            "/repos",
            json={
                "owner": "t",
                "name": f"r422-{uuid.uuid4().hex[:6]}",
                "layer": "silver",
                "subtype": "text-corpus",
                "row_format": "parquet",
            },
        )
        assert r1.status_code == 422, f"缺 schema_id 期望 422，实际: {r1.status_code} {r1.text}"

        # 2. 缺 row_format
        r2 = await c.post(
            "/repos",
            json={
                "owner": "t",
                "name": f"r422-{uuid.uuid4().hex[:6]}",
                "layer": "silver",
                "subtype": "text-corpus",
                "schema_id": "silver-text-v1",
            },
        )
        assert r2.status_code == 422, f"缺 row_format 期望 422，实际: {r2.status_code} {r2.text}"

        # 3. schema_id 未注册
        r3 = await c.post(
            "/repos",
            json={
                "owner": "t",
                "name": f"r422-{uuid.uuid4().hex[:6]}",
                "layer": "silver",
                "subtype": "text-corpus",
                "schema_id": "unknown-v9",
                "row_format": "parquet",
            },
        )
        assert r3.status_code == 422, f"未注册 schema 期望 422，实际: {r3.status_code} {r3.text}"

        # 4. 跨层（gold schema 用于 silver layer）
        r4 = await c.post(
            "/repos",
            json={
                "owner": "t",
                "name": f"r422-{uuid.uuid4().hex[:6]}",
                "layer": "silver",
                "subtype": "text-corpus",
                "schema_id": "gold-sft-v1",
                "row_format": "parquet",
            },
        )
        assert r4.status_code == 422, f"跨层 schema 期望 422，实际: {r4.status_code} {r4.text}"


# --------- AC-3: 合法创建 + bronze 拒绝 ---------


@pytest.mark.asyncio
async def test_silver_create_201_and_bronze_reject(admin_user: dict) -> None:
    """AC-3: silver 合法 → 201 + GET 响应含两字段；bronze 带 schema_id → 422。"""
    repo_name = f"r201-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)

            # silver 合法创建 → 201
            r1 = await c.post(
                "/repos",
                json={
                    "owner": "t",
                    "name": repo_name,
                    "layer": "silver",
                    "subtype": "text-corpus",
                    "schema_id": "silver-text-v1",
                    "row_format": "parquet",
                    "visibility": "public",
                },
            )
            assert r1.status_code == 201, f"期望 201，实际: {r1.status_code} {r1.text}"
            body = r1.json()
            assert body["schema_id"] == "silver-text-v1", f"创建响应 schema_id 不匹配: {body}"
            assert body["row_format"] == "parquet", f"创建响应 row_format 不匹配: {body}"

            # GET 响应含两字段
            r_get = await c.get(f"/repos/t/{repo_name}")
            assert r_get.status_code == 200, f"GET 期望 200，实际: {r_get.status_code} {r_get.text}"
            get_body = r_get.json()
            assert get_body["schema_id"] == "silver-text-v1", f"GET 响应 schema_id 不匹配: {get_body}"
            assert get_body["row_format"] == "parquet", f"GET 响应 row_format 不匹配: {get_body}"

            # bronze 带 schema_id → 422
            r2 = await c.post(
                "/repos",
                json={
                    "owner": "t",
                    "name": f"r-bronze-{uuid.uuid4().hex[:6]}",
                    "layer": "bronze",
                    "subtype": "pdf",
                    "schema_id": "silver-text-v1",
                },
            )
            assert r2.status_code == 422, f"bronze 带 schema_id 期望 422，实际: {r2.status_code} {r2.text}"
    finally:
        await _delete_repo_cascade("t", repo_name)
