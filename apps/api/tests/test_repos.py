"""Repository CRUD 集成测试（spec repo-api-mvp-20260517 AC-11）。

13 测试覆盖 admin / user / 匿名 × public / internal / private visibility 矩阵。

依赖：
- Postgres + alembic upgrade head（0001 + 0002）
- conftest 早设 JWT_SECRET + USE_NULL_POOL
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
from dataplat_api.auth.password import hash_password
from dataplat_api.main import app
from dataplat_api.models import RepositoryORM, UserORM
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _db_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not _db_url(),
    reason="DATAPLAT_DATABASE_URL 未设置；repos 集成测试跳过",
)


# --------- fixtures ---------


async def _make_user(role: str) -> dict:
    """fresh engine + 直接 INSERT 一个用户，返回 dict 含 username + password + role。"""
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


# --------- (a) admin POST 创建成功 201 ---------


@pytest.mark.asyncio
async def test_a_admin_create_returns_201(admin_user: dict) -> None:
    repo_name = f"repo-a-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as client:
            await _login(client, admin_user)
            resp = await client.post(
                "/repos",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "layer": "bronze",
                    "subtype": "pdf",
                    "visibility": "public",
                },
            )
        assert resp.status_code == 201
        body = resp.json()
        assert body["owner"] == "test"
        assert body["name"] == repo_name
    finally:
        await _delete_repo("test", repo_name)


# --------- (b) user POST 返 403 ---------


@pytest.mark.asyncio
async def test_b_user_post_returns_403(normal_user: dict) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        await _login(client, normal_user)
        resp = await client.post(
            "/repos",
            json={
                "owner": "test",
                "name": f"repo-b-{uuid.uuid4().hex[:6]}",
                "layer": "bronze",
                "subtype": "pdf",
            },
        )
    assert resp.status_code == 403


# --------- (c) 重复 (owner, name) 返 409 ---------


@pytest.mark.asyncio
async def test_c_duplicate_owner_name_returns_409(admin_user: dict) -> None:
    repo_name = f"repo-c-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as client:
            await _login(client, admin_user)
            body = {
                "owner": "test",
                "name": repo_name,
                "layer": "bronze",
                "subtype": "pdf",
            }
            resp1 = await client.post("/repos", json=body)
            assert resp1.status_code == 201
            resp2 = await client.post("/repos", json=body)
        assert resp2.status_code == 409
    finally:
        await _delete_repo("test", repo_name)


# --------- (d) admin GET 已创建 200 ---------


@pytest.mark.asyncio
async def test_d_admin_get_existing_200(admin_user: dict) -> None:
    repo_name = f"repo-d-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as client:
            await _login(client, admin_user)
            create_resp = await client.post(
                "/repos",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "layer": "silver",
                    "subtype": "text-corpus",
                    "visibility": "private",
                },
            )
            assert create_resp.status_code == 201
            resp = await client.get(f"/repos/test/{repo_name}")
        assert resp.status_code == 200
        assert resp.json()["layer"] == "silver"
    finally:
        await _delete_repo("test", repo_name)


# --------- (e) admin list 返回新 repo ---------


@pytest.mark.asyncio
async def test_e_admin_list_includes_new_repo(admin_user: dict) -> None:
    repo_name = f"repo-e-{uuid.uuid4().hex[:6]}"
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
            resp = await client.get("/repos?limit=200")
        assert resp.status_code == 200
        body = resp.json()
        names = [r["name"] for r in body["items"]]
        assert repo_name in names
    finally:
        await _delete_repo("test", repo_name)


# --------- (f) 匿名 GET public repo → 200 ---------


@pytest.mark.asyncio
async def test_f_anonymous_get_public_200(admin_user: dict) -> None:
    repo_name = f"repo-f-{uuid.uuid4().hex[:6]}"
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
        # 匿名 client（无 cookies）
        async with AsyncClient(transport=transport, base_url="https://test") as anon:
            resp = await anon.get(f"/repos/test/{repo_name}")
        assert resp.status_code == 200
    finally:
        await _delete_repo("test", repo_name)


# --------- (g) 匿名 GET private repo → 404 ---------


@pytest.mark.asyncio
async def test_g_anonymous_get_private_404(admin_user: dict) -> None:
    repo_name = f"repo-g-{uuid.uuid4().hex[:6]}"
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
                    "visibility": "private",
                },
            )
        async with AsyncClient(transport=transport, base_url="https://test") as anon:
            resp = await anon.get(f"/repos/test/{repo_name}")
        assert resp.status_code == 404
    finally:
        await _delete_repo("test", repo_name)


# --------- (h) user GET internal repo → 200 ---------


@pytest.mark.asyncio
async def test_h_user_get_internal_200(admin_user: dict, normal_user: dict) -> None:
    repo_name = f"repo-h-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await a.post(
                "/repos",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "layer": "bronze",
                    "subtype": "pdf",
                    "visibility": "internal",
                },
            )
        async with AsyncClient(transport=transport, base_url="https://test") as u:
            await _login(u, normal_user)
            resp = await u.get(f"/repos/test/{repo_name}")
        assert resp.status_code == 200
    finally:
        await _delete_repo("test", repo_name)


# --------- (i) user GET private repo → 404 ---------


@pytest.mark.asyncio
async def test_i_user_get_private_404(admin_user: dict, normal_user: dict) -> None:
    repo_name = f"repo-i-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await a.post(
                "/repos",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "layer": "bronze",
                    "subtype": "pdf",
                    "visibility": "private",
                },
            )
        async with AsyncClient(transport=transport, base_url="https://test") as u:
            await _login(u, normal_user)
            resp = await u.get(f"/repos/test/{repo_name}")
        assert resp.status_code == 404
    finally:
        await _delete_repo("test", repo_name)


# --------- (j) admin PATCH public→private + user 视角变 404 ---------


@pytest.mark.asyncio
async def test_j_patch_visibility_realtime_check(
    admin_user: dict, normal_user: dict
) -> None:
    """spec MUST FIX-4：visibility 实时 DB 检查，旧 cookie 不构成缓存窗口。"""
    repo_name = f"repo-j-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await a.post(
                "/repos",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "layer": "bronze",
                    "subtype": "pdf",
                    "visibility": "public",
                },
            )

        # user 先确认可见
        async with AsyncClient(transport=transport, base_url="https://test") as u:
            await _login(u, normal_user)
            r1 = await u.get(f"/repos/test/{repo_name}")
            assert r1.status_code == 200

            # admin PATCH 改为 private
            async with AsyncClient(transport=transport, base_url="https://test") as a:
                await _login(a, admin_user)
                patch_resp = await a.patch(
                    f"/repos/test/{repo_name}",
                    json={"visibility": "private"},
                )
                assert patch_resp.status_code == 200

            # user 用同一 cookies 再访问 → 应当 404（实时检查；不缓存）
            r2 = await u.get(f"/repos/test/{repo_name}")
        assert r2.status_code == 404
    finally:
        await _delete_repo("test", repo_name)


# --------- (k) admin DELETE 204 + 再 GET 404 ---------


@pytest.mark.asyncio
async def test_k_admin_delete_then_get_404(admin_user: dict) -> None:
    repo_name = f"repo-k-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
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
        del_resp = await client.delete(f"/repos/test/{repo_name}")
        assert del_resp.status_code == 204
        get_resp = await client.get(f"/repos/test/{repo_name}")
    assert get_resp.status_code == 404


# --------- (l) 匿名 list 仅含 public ---------


@pytest.mark.asyncio
async def test_l_anonymous_list_only_public(admin_user: dict) -> None:
    repo_public = f"repo-l-pub-{uuid.uuid4().hex[:6]}"
    repo_private = f"repo-l-priv-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            for name, vis in [(repo_public, "public"), (repo_private, "private")]:
                await a.post(
                    "/repos",
                    json={
                        "owner": "test",
                        "name": name,
                        "layer": "bronze",
                        "subtype": "pdf",
                        "visibility": vis,
                    },
                )
        async with AsyncClient(transport=transport, base_url="https://test") as anon:
            resp = await anon.get("/repos?limit=200")
        assert resp.status_code == 200
        names = {r["name"] for r in resp.json()["items"]}
        assert repo_public in names
        assert repo_private not in names
    finally:
        await _delete_repo("test", repo_public)
        await _delete_repo("test", repo_private)


# --------- (m) user list 不含 private ---------


@pytest.mark.asyncio
async def test_m_user_list_excludes_private(
    admin_user: dict, normal_user: dict
) -> None:
    repo_internal = f"repo-m-int-{uuid.uuid4().hex[:6]}"
    repo_private = f"repo-m-priv-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            for name, vis in [(repo_internal, "internal"), (repo_private, "private")]:
                await a.post(
                    "/repos",
                    json={
                        "owner": "test",
                        "name": name,
                        "layer": "bronze",
                        "subtype": "pdf",
                        "visibility": vis,
                    },
                )
        async with AsyncClient(transport=transport, base_url="https://test") as u:
            await _login(u, normal_user)
            resp = await u.get("/repos?limit=200")
        assert resp.status_code == 200
        names = {r["name"] for r in resp.json()["items"]}
        assert repo_internal in names  # user 能看 internal
        assert repo_private not in names  # user 看不到 private
    finally:
        await _delete_repo("test", repo_internal)
        await _delete_repo("test", repo_private)


# --------- (n) list 含 total + layer query 过滤（spec AC-10） ---------


@pytest.mark.asyncio
async def test_n_list_total_and_layer_filter(admin_user: dict) -> None:
    """spec AC-10：GET /repos 返回 {items, total}；layer 过滤生效。"""
    repo_bronze = f"repo-n-br-{uuid.uuid4().hex[:6]}"
    repo_silver = f"repo-n-sv-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await a.post(
                "/repos",
                json={
                    "owner": "test",
                    "name": repo_bronze,
                    "layer": "bronze",
                    "subtype": "pdf",
                    "visibility": "public",
                },
            )
            await a.post(
                "/repos",
                json={
                    "owner": "test",
                    "name": repo_silver,
                    "layer": "silver",
                    "subtype": "text-corpus",
                    "visibility": "public",
                },
            )
            # 不带 layer → 含 total 字段，至少含两个新建
            resp_all = await a.get("/repos?limit=200")
            assert resp_all.status_code == 200
            body_all = resp_all.json()
            assert "total" in body_all and isinstance(body_all["total"], int)
            assert "items" in body_all and isinstance(body_all["items"], list)
            all_names = {r["name"] for r in body_all["items"]}
            assert repo_bronze in all_names and repo_silver in all_names

            # layer=bronze → 不含 silver
            resp_br = await a.get("/repos?limit=200&layer=bronze")
            assert resp_br.status_code == 200
            br_names = {r["name"] for r in resp_br.json()["items"]}
            assert repo_bronze in br_names
            assert repo_silver not in br_names

            # layer=silver → 不含 bronze
            resp_sv = await a.get("/repos?limit=200&layer=silver")
            assert resp_sv.status_code == 200
            sv_names = {r["name"] for r in resp_sv.json()["items"]}
            assert repo_silver in sv_names
            assert repo_bronze not in sv_names
    finally:
        await _delete_repo("test", repo_bronze)
        await _delete_repo("test", repo_silver)
