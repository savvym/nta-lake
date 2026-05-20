"""GET /jobs 列表端点集成测试（spec web-jobs-list-page-20260520 AC-8）。

5 用例：admin list / user 403 / status 过滤 / limit+offset 分页 / 400 非白名单。
直接 INSERT JobORM 绕过 RQ enqueue（不依赖真 worker）。
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
from dataplat_api.auth.password import hash_password
from dataplat_api.main import app
from dataplat_api.models import JobORM, UserORM
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _db_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not _db_url(),
    reason="DATAPLAT_DATABASE_URL 未设置；test_jobs_list 跳过",
)


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
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
    return {"id": user.id, "username": username, "password": password}


async def _delete_user(user_id: uuid.UUID) -> None:
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(delete(UserORM).where(UserORM.id == user_id))
        await session.commit()


async def _seed_jobs(seed_marker: str) -> list[uuid.UUID]:
    """Insert 4 JobORM with diverse status/type/created_at；返 ids（按 desc 顺序）。

    payload 嵌 seed_marker 便于本测试隔离；测试结束 delete by marker。
    """
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    base = datetime.now(UTC)
    rows = [
        ("ingest", "queued", -3),
        ("ingest", "succeeded", -2),
        ("process", "running", -1),
        ("process", "failed", 0),
    ]
    ids: list[uuid.UUID] = []
    async with factory() as session:
        for t, s, off in rows:
            j = JobORM(
                id=uuid.uuid4(),
                type=t,
                status=s,
                payload={"_marker": seed_marker},
                created_at=base + timedelta(minutes=off),
            )
            session.add(j)
            ids.append(j.id)
        await session.commit()
    return list(reversed(ids))  # desc by created_at


async def _delete_jobs(seed_marker: str) -> None:
    from sqlalchemy import text

    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(
            text("DELETE FROM jobs WHERE payload->>'_marker' = :m"),
            {"m": seed_marker},
        )
        await session.commit()


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


async def _login(client: AsyncClient, user: dict) -> None:
    resp = await client.post(
        "/auth/login",
        json={"username": user["username"], "password": user["password"]},
    )
    assert resp.status_code == 200


async def test_admin_list_returns_items_and_total(admin_user: dict) -> None:
    marker = f"t-list-{uuid.uuid4().hex[:8]}"
    await _seed_jobs(marker)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            await _login(client, admin_user)
            r = await client.get("/jobs", params={"limit": 200})
            assert r.status_code == 200, r.text
            body = r.json()
            mine = [
                j for j in body["items"] if j["payload"].get("_marker") == marker
            ]
            assert len(mine) == 4
            assert body["total"] >= 4
            ts = [j["created_at"] for j in mine]
            assert ts == sorted(ts, reverse=True)
    finally:
        await _delete_jobs(marker)


async def test_user_list_returns_403(normal_user: dict) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, normal_user)
        r = await client.get("/jobs")
        assert r.status_code == 403, r.text


async def test_status_filter_narrows_results(admin_user: dict) -> None:
    marker = f"t-stat-{uuid.uuid4().hex[:8]}"
    await _seed_jobs(marker)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            await _login(client, admin_user)
            r = await client.get(
                "/jobs", params={"status": "queued", "limit": 200}
            )
            assert r.status_code == 200
            mine = [
                j
                for j in r.json()["items"]
                if j["payload"].get("_marker") == marker
            ]
            assert len(mine) == 1
            assert mine[0]["status"] == "queued"
    finally:
        await _delete_jobs(marker)


async def test_pagination_preserves_desc_order(admin_user: dict) -> None:
    """同时覆盖 desc 排序与 offset 切页（review SHOULD FIX：原版只测排序）。"""
    marker = f"t-page-{uuid.uuid4().hex[:8]}"
    ids_desc = await _seed_jobs(marker)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            await _login(client, admin_user)
            # 全量取一遍验证 desc 顺序
            r = await client.get("/jobs", params={"limit": 200})
            assert r.status_code == 200
            mine_all = [
                j
                for j in r.json()["items"]
                if j["payload"].get("_marker") == marker
            ]
            assert len(mine_all) == 4
            assert mine_all[1]["id"] == str(ids_desc[1])

            # 全局 offset 切页：用 limit=2 的两页拼出 4 行（marker 隔离避免邻居数据干扰）
            mine_p1: list[dict] = []
            mine_p2: list[dict] = []
            for off in range(0, 400, 2):  # 上限放宽以容忍并发噪声
                r = await client.get(
                    "/jobs", params={"limit": 2, "offset": off}
                )
                assert r.status_code == 200
                page = r.json()["items"]
                if not page:
                    break
                for j in page:
                    if j["payload"].get("_marker") == marker:
                        if len(mine_p1) < 2:
                            mine_p1.append(j)
                        else:
                            mine_p2.append(j)
                if len(mine_p1) >= 2 and len(mine_p2) >= 2:
                    break
            assert len(mine_p1) == 2 and len(mine_p2) == 2
            # 拼出的 4 个 id 必须就是 seed 时 desc 顺序的 4 个
            assert [j["id"] for j in mine_p1 + mine_p2] == [
                str(i) for i in ids_desc
            ]
    finally:
        await _delete_jobs(marker)


async def test_invalid_status_returns_400(admin_user: dict) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _login(client, admin_user)
        r = await client.get("/jobs", params={"status": "bogus"})
        assert r.status_code == 400, r.text
        assert "非白名单" in r.text
