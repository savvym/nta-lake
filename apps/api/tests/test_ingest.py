"""Adapter ingest 集成 + 单元测试（spec adapter-framework-20260517 AC-11）。

13 测试覆盖 (a) registry 单元 + (b) RawAdapter 单元 + (c)~(m) 集成路径
（admin 200 / user 403 / unknown adapter 404 / missing blob 400 / 幂等
/ ref upsert / round-trip / visibility 404 / 多文件 tree / validation 400
/ parent 父子链）。
"""

from __future__ import annotations

import hashlib
import os
import uuid
from collections.abc import AsyncGenerator

import boto3
import pytest
from dataplat_api.adapters.raw_upload import RawFileUploadAdapter
from dataplat_api.auth.password import hash_password
from dataplat_api.main import app
from dataplat_api.models import UserORM
from dataplat_api.runner.registry import AdapterRegistry, get_registry
from dataplat_api.storage import get_blob_store
from dataplat_api.storage.minio_store import MinioBlobStore
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _db_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


def _minio_endpoint() -> str | None:
    return os.environ.get("DATAPLAT_MINIO_ENDPOINT")


pytestmark = pytest.mark.skipif(
    not (_db_url() and _minio_endpoint()),
    reason="DATAPLAT_DATABASE_URL / DATAPLAT_MINIO_ENDPOINT 未设置；ingest 集成跳过",
)


# --------- fixtures ---------


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


@pytest.fixture(autouse=True)
def _override_blob_store() -> AsyncGenerator[None, None]:
    bucket = f"dataplat-test-{uuid.uuid4().hex[:8]}"
    endpoint = os.environ.get("DATAPLAT_MINIO_ENDPOINT", "http://localhost:9000")
    ak = os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat")
    sk = os.environ.get("DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret")
    store = MinioBlobStore(
        endpoint_url=endpoint, access_key=ak, secret_key=sk, bucket=bucket
    )
    app.dependency_overrides[get_blob_store] = lambda: store
    try:
        yield  # type: ignore[misc]
    finally:
        app.dependency_overrides.pop(get_blob_store, None)
        raw = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=ak,
            aws_secret_access_key=sk,
            region_name="us-east-1",
        )
        try:
            paginator = raw.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket):
                for obj in page.get("Contents") or []:
                    raw.delete_object(Bucket=bucket, Key=obj["Key"])
            raw.delete_bucket(Bucket=bucket)
        except Exception:  # noqa: BLE001
            pass


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


async def _create_repo(
    client: AsyncClient, owner: str, name: str, visibility: str = "public"
) -> None:
    resp = await client.post(
        "/repos",
        json={
            "owner": owner,
            "name": name,
            "layer": "bronze",
            "subtype": "pdf",
            "visibility": visibility,
        },
    )
    assert resp.status_code == 201, resp.text


async def _upload_blob(client: AsyncClient, owner: str, name: str, data: bytes) -> str:
    resp = await client.post(f"/repos/{owner}/{name}/blobs", content=data)
    assert resp.status_code == 201, resp.text
    return resp.json()["sha256"]


# --------- (a) 单元：registry register/get/list（不依赖 PG/MinIO） ---------


def test_a_registry_register_get_list() -> None:
    reg = AdapterRegistry()
    assert reg.list_all() == []
    reg.register(RawFileUploadAdapter())
    assert reg.get("raw-file-upload", "0.1") is not None
    assert ("raw-file-upload", "0.1") in reg.list_all()
    # 重复注册幂等（warning 跳过，不 raise）
    reg.register(RawFileUploadAdapter())
    assert len(reg.list_all()) == 1
    # module 单例自动注册了
    global_reg = get_registry()
    assert global_reg.get("raw-file-upload", "0.1") is not None


# --------- (b) 单元：RawFileUploadAdapter.ingest pass-through ---------


def test_b_raw_adapter_ingest_pass_through() -> None:
    a = RawFileUploadAdapter()
    sha = "a" * 64
    result = a.ingest({"files": [{"path": "x.md", "sha256": sha}]}, None, None)
    assert result.file_count == 1
    assert result.files[0].path == "x.md"
    assert result.files[0].sha256 == sha
    assert result.files[0].mode == 33188

    # path 重复 → ValueError
    with pytest.raises(ValueError, match="重复"):
        a.ingest(
            {"files": [{"path": "a", "sha256": "a" * 64}, {"path": "a", "sha256": "b" * 64}]},
            None,
            None,
        )


# --------- (c) admin POST /ingest 创建 commit 200 ---------


@pytest.mark.asyncio
async def test_c_admin_ingest_creates_commit_200(admin_user: dict) -> None:
    repo_name = f"repo-ic-{uuid.uuid4().hex[:6]}"
    data = b"ingest test content"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            sha = await _upload_blob(c, "test", repo_name, data)
            resp = await c.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {"files": [{"path": "content/a.md", "sha256": sha}]},
                    "author_id": "u1",
                    "message": "first ingest",
                },
            )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "commit" in body and "ingest_summary" in body
        assert body["commit"]["deduplicated"] is False
        assert body["ingest_summary"]["file_count"] == 1
        assert body["commit"]["tree"]["entries"][0]["target_hash"] == sha
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (d) ingest 引用未上传 blob → 400 missing_hashes ---------


@pytest.mark.asyncio
async def test_d_ingest_with_missing_blob_returns_400(admin_user: dict) -> None:
    repo_name = f"repo-id-{uuid.uuid4().hex[:6]}"
    fake = "0" * 64
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            resp = await c.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {"files": [{"path": "x.md", "sha256": fake}]},
                    "author_id": "u1",
                },
            )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert fake in detail["missing_hashes"]
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (e) user POST /ingest → 403 ---------


@pytest.mark.asyncio
async def test_e_user_ingest_returns_403(
    admin_user: dict, normal_user: dict
) -> None:
    repo_name = f"repo-ie-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await _create_repo(a, "test", repo_name, "public")
        async with AsyncClient(transport=transport, base_url="https://test") as u:
            await _login(u, normal_user)
            resp = await u.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {"files": [{"path": "x", "sha256": "a" * 64}]},
                    "author_id": "u1",
                },
            )
        assert resp.status_code == 403
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (f) unknown adapter → 404 ---------


@pytest.mark.asyncio
async def test_f_unknown_adapter_returns_404(admin_user: dict) -> None:
    repo_name = f"repo-if-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            resp = await c.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "no-such-adapter",
                    "adapter_version": "9.9",
                    "spec": {"files": [{"path": "x", "sha256": "a" * 64}]},
                    "author_id": "u1",
                },
            )
        assert resp.status_code == 404
        detail = resp.json()["detail"]
        assert "no-such-adapter" in detail["detail"]
        assert "raw-file-upload@0.1" in detail["available"]
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (g) 幂等：相同 spec 二次 POST → deduplicated=true ---------


@pytest.mark.asyncio
async def test_g_ingest_idempotent_returns_dedup_true(admin_user: dict) -> None:
    repo_name = f"repo-ig-{uuid.uuid4().hex[:6]}"
    data = b"idem ingest"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            sha = await _upload_blob(c, "test", repo_name, data)
            payload = {
                "adapter_name": "raw-file-upload",
                "adapter_version": "0.1",
                "spec": {"files": [{"path": "a", "sha256": sha}]},
                "author_id": "u1",
                "message": "idem",
            }
            r1 = await c.post(f"/repos/test/{repo_name}/ingest", json=payload)
            r2 = await c.post(f"/repos/test/{repo_name}/ingest", json=payload)
        assert r1.json()["commit"]["hash"] == r2.json()["commit"]["hash"]
        assert r1.json()["commit"]["deduplicated"] is False
        assert r2.json()["commit"]["deduplicated"] is True
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (h) ingest 含 ref → ref upsert ---------


@pytest.mark.asyncio
async def test_h_ingest_with_ref_upserts(admin_user: dict) -> None:
    repo_name = f"repo-ih-{uuid.uuid4().hex[:6]}"
    data = b"ref upsert"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            sha = await _upload_blob(c, "test", repo_name, data)
            resp = await c.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {"files": [{"path": "x", "sha256": sha}]},
                    "author_id": "u1",
                    "ref": "main",
                },
            )
            commit_hash = resp.json()["commit"]["hash"]
        engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with factory() as s:
            row = (
                await s.execute(
                    text(
                        "SELECT r.name, r.commit_hash FROM refs r "
                        "JOIN repositories rp ON r.repo_id=rp.id "
                        "WHERE rp.owner=:o AND rp.name=:n"
                    ),
                    {"o": "test", "n": repo_name},
                )
            ).first()
        assert row is not None
        assert row[0] == "main"
        assert row[1] == commit_hash
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (i) ingest → GET commit round-trip 含 tree.entries ---------


@pytest.mark.asyncio
async def test_i_get_commit_after_ingest_includes_tree(admin_user: dict) -> None:
    repo_name = f"repo-ii-{uuid.uuid4().hex[:6]}"
    data = b"roundtrip content"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            sha = await _upload_blob(c, "test", repo_name, data)
            r_ingest = await c.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {"files": [{"path": "round.md", "sha256": sha}]},
                    "author_id": "u1",
                },
            )
            commit_hash = r_ingest.json()["commit"]["hash"]
            r_get = await c.get(f"/repos/test/{repo_name}/commits/{commit_hash}")
        assert r_get.status_code == 200
        body = r_get.json()
        assert body["tree"]["entries"][0]["name"] == "round.md"
        assert body["tree"]["entries"][0]["target_hash"] == sha
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (j) 匿名 ingest private repo → 404 ---------


@pytest.mark.asyncio
async def test_j_anonymous_ingest_private_repo_401(admin_user: dict) -> None:
    repo_name = f"repo-ij-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await _create_repo(a, "test", repo_name, "private")
        # 匿名 client；不带 require_admin 头 → 路由先 require_admin 401
        async with AsyncClient(transport=transport, base_url="https://test") as anon:
            resp = await anon.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {"files": [{"path": "x", "sha256": "a" * 64}]},
                    "author_id": "u1",
                },
            )
        # require_admin → 401（未登录），符合 admin-only 写路径语义
        assert resp.status_code == 401
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (k) 多文件 tree 结构正确 ---------


@pytest.mark.asyncio
async def test_k_ingest_multi_file_tree_structure_correct(admin_user: dict) -> None:
    repo_name = f"repo-ik-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            sha1 = await _upload_blob(c, "test", repo_name, b"ch01")
            sha2 = await _upload_blob(c, "test", repo_name, b"ch02")
            sha3 = await _upload_blob(c, "test", repo_name, b"ch03")
            resp = await c.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {
                        "files": [
                            {"path": "content/ch01.md", "sha256": sha1},
                            {"path": "content/ch02.md", "sha256": sha2},
                            {"path": "content/ch03.md", "sha256": sha3},
                        ]
                    },
                    "author_id": "u1",
                },
            )
        assert resp.status_code == 200
        entries = resp.json()["commit"]["tree"]["entries"]
        # entries 按 position 升序，但 canonical 按 name 升序——name 升序时 path "ch01..03" 自然有序
        names = [e["name"] for e in entries]
        assert names == sorted(names)
        assert {e["target_hash"] for e in entries} == {sha1, sha2, sha3}
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (l) adapter 校验失败 → 400 ---------


@pytest.mark.asyncio
async def test_l_adapter_validation_error_returns_400(admin_user: dict) -> None:
    repo_name = f"repo-il-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            # 缺 files
            r1 = await c.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {},
                    "author_id": "u1",
                },
            )
            assert r1.status_code == 400
            # files 含重复 path
            sha = hashlib.sha256(b"x").hexdigest()
            r2 = await c.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {
                        "files": [
                            {"path": "a", "sha256": sha},
                            {"path": "a", "sha256": sha},
                        ]
                    },
                    "author_id": "u1",
                },
            )
            assert r2.status_code == 400
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (m) 第二次 ingest 到同 ref → C2.parents=[C1] 历史链不断（spec v2 修 MUST FIX-1）---------


@pytest.mark.asyncio
async def test_m_second_ingest_to_same_ref_creates_child(admin_user: dict) -> None:
    repo_name = f"repo-im-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            sha1 = await _upload_blob(c, "test", repo_name, b"first")
            r1 = await c.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {"files": [{"path": "v1.md", "sha256": sha1}]},
                    "author_id": "u1",
                    "ref": "main",
                },
            )
            c1_hash = r1.json()["commit"]["hash"]
            assert r1.json()["commit"]["parents"] == []

            sha2 = await _upload_blob(c, "test", repo_name, b"second")
            r2 = await c.post(
                f"/repos/test/{repo_name}/ingest",
                json={
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {"files": [{"path": "v2.md", "sha256": sha2}]},
                    "author_id": "u1",
                    "ref": "main",
                },
            )
            c2_hash = r2.json()["commit"]["hash"]
            assert c2_hash != c1_hash
            assert r2.json()["commit"]["parents"] == [c1_hash]

            # C1 仍可达
            r_c1 = await c.get(f"/repos/test/{repo_name}/commits/{c1_hash}")
        assert r_c1.status_code == 200
    finally:
        await _delete_repo_cascade("test", repo_name)
