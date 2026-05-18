"""Commit / Blob / Tree HTTP 集成测试（spec commit-api-mvp-20260517 AC-11）。

18 测试覆盖 admin / user / 匿名 × public / internal / private + 大文件 + lineage
+ 幂等 + canonical hash 单元（g1）+ ref upsert + missing blob 400 等。

依赖：
- Postgres（DATAPLAT_DATABASE_URL）
- MinIO（DATAPLAT_MINIO_ENDPOINT；fixture 用唯一 bucket 隔离）
- conftest 早设 JWT_SECRET + USE_NULL_POOL
"""

from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from collections.abc import AsyncGenerator

import boto3
import pytest
from dataplat_api.auth.password import hash_password
from dataplat_api.main import app
from dataplat_api.models import UserORM
from dataplat_api.services.commit import CommitService
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
    reason="DATAPLAT_DATABASE_URL / DATAPLAT_MINIO_ENDPOINT 未设置；commits 集成跳过",
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
    """删 repo + 所属 commits / refs / trees。

    tree_entries 由 CASCADE 自动清；trees / commits 由 repo CASCADE 清；
    但 trees.hash 是全局唯一，commits 引用 trees，所以需要先删 commits → refs → trees → repo。
    """
    engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        # 找 repo id
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
        # 删 refs（commit_hash FK RESTRICT）
        await session.execute(
            text("DELETE FROM refs WHERE repo_id=:r"), {"r": repo_id}
        )
        # 删 commits（tree_hash FK RESTRICT）
        await session.execute(
            text("DELETE FROM commits WHERE repo_id=:r"), {"r": repo_id}
        )
        # 删 trees（tree_entries CASCADE）
        await session.execute(
            text("DELETE FROM trees WHERE repo_id=:r"), {"r": repo_id}
        )
        # 删 repo
        await session.execute(
            text("DELETE FROM repositories WHERE id=:r"), {"r": repo_id}
        )
        await session.commit()


@pytest.fixture(autouse=True)
def _override_blob_store() -> AsyncGenerator[None, None]:
    """每测一个唯一 bucket 的 MinioBlobStore；teardown 清空 bucket。

    避免 `get_blob_store()` 默认单例污染 / 凭据漂移。
    """
    bucket = f"dataplat-test-{uuid.uuid4().hex[:8]}"
    endpoint = os.environ.get("DATAPLAT_MINIO_ENDPOINT", "http://localhost:9000")
    ak = os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat")
    sk = os.environ.get("DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret")
    store = MinioBlobStore(
        endpoint_url=endpoint,
        access_key=ak,
        secret_key=sk,
        bucket=bucket,
    )
    app.dependency_overrides[get_blob_store] = lambda: store
    try:
        yield  # type: ignore[misc]
    finally:
        app.dependency_overrides.pop(get_blob_store, None)
        # 清 bucket
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


# --------- (g1) 单元：canonical hash 确定性（不依赖 PG / MinIO） ---------


def test_g1_canonical_hash_is_deterministic() -> None:
    """spec AC-9 / AC-11 (g1)：entries / parents 排序不变性 + 同输入同 hash。"""
    from dataplat_api.schemas.tree import TreeEntryCreate

    e1 = TreeEntryCreate(name="b.txt", mode=33188, target_hash="a" * 64)
    e2 = TreeEntryCreate(name="a.txt", mode=33188, target_hash="b" * 64)
    # entries 排序不变性
    assert CommitService._canonical_tree_bytes([e1, e2]) == CommitService._canonical_tree_bytes([e2, e1])
    th = CommitService._tree_hash([e1, e2])
    assert th == CommitService._tree_hash([e2, e1])

    # parents 排序不变性 + author/message 一致 → 同 hash
    p1 = "c" * 64
    p2 = "d" * 64
    h1 = CommitService._commit_hash(th, [p1, p2], "u1", "msg", None)
    h2 = CommitService._commit_hash(th, [p2, p1], "u1", "msg", None)
    assert h1 == h2

    # 改 message → 不同 hash
    h3 = CommitService._commit_hash(th, [p1, p2], "u1", "msg2", None)
    assert h3 != h1


# --------- (a) admin POST blob 200 + sha256 正确 ---------


@pytest.mark.asyncio
async def test_a_admin_post_blob_200_sha256_correct(admin_user: dict) -> None:
    repo_name = f"repo-ca-{uuid.uuid4().hex[:6]}"
    data = b"hello commit api"
    expected = hashlib.sha256(data).hexdigest()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            resp = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["sha256"] == expected
        assert body["size"] == len(data)
        assert body["deduplicated"] is False
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (b) 重复 POST 相同字节 → dedup=true ---------


@pytest.mark.asyncio
async def test_b_admin_dedup_returns_true(admin_user: dict) -> None:
    repo_name = f"repo-cb-{uuid.uuid4().hex[:6]}"
    data = b"dedup-payload-" + secrets.token_bytes(16)
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r1 = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
            r2 = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
        assert r1.json()["deduplicated"] is False
        assert r2.json()["deduplicated"] is True
        assert r1.json()["sha256"] == r2.json()["sha256"]
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (c) 非 admin POST blob → 403 ---------


@pytest.mark.asyncio
async def test_c_user_post_blob_403(admin_user: dict, normal_user: dict) -> None:
    repo_name = f"repo-cc-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await _create_repo(a, "test", repo_name, "public")
        async with AsyncClient(transport=transport, base_url="https://test") as u:
            await _login(u, normal_user)
            resp = await u.post(f"/repos/test/{repo_name}/blobs", content=b"x")
        assert resp.status_code == 403
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (d) admin POST commit 1 entry → 200 + 服务端 hash ---------


@pytest.mark.asyncio
async def test_d_admin_post_commit_with_one_entry(admin_user: dict) -> None:
    repo_name = f"repo-cd-{uuid.uuid4().hex[:6]}"
    data = b"file content for commit d"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
            sha = r_blob.json()["sha256"]
            resp = await c.post(
                f"/repos/test/{repo_name}/commits",
                json={
                    "tree": {
                        "entries": [
                            {
                                "name": "f.txt",
                                "mode": 33188,
                                "entry_type": "blob",
                                "target_hash": sha,
                            }
                        ]
                    },
                    "parents": [],
                    "author_id": "u1",
                    "message": "init",
                },
            )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["hash"]) == 64
        assert body["tree_hash"] != body["hash"]
        assert body["deduplicated"] is False
        assert body["tree"]["entries"][0]["target_hash"] == sha
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (e) POST commit 引用不存在 blob → 400 + missing_hashes ---------


@pytest.mark.asyncio
async def test_e_post_commit_missing_blob_returns_400(admin_user: dict) -> None:
    repo_name = f"repo-ce-{uuid.uuid4().hex[:6]}"
    fake_sha = "0" * 64
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            resp = await c.post(
                f"/repos/test/{repo_name}/commits",
                json={
                    "tree": {
                        "entries": [
                            {
                                "name": "missing.txt",
                                "mode": 33188,
                                "entry_type": "blob",
                                "target_hash": fake_sha,
                            }
                        ]
                    },
                    "parents": [],
                    "author_id": "u1",
                },
            )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert fake_sha in detail["missing_hashes"]
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (f) POST commit 含 ref → ref upsert ---------


@pytest.mark.asyncio
async def test_f_post_commit_with_ref_upserts(admin_user: dict) -> None:
    repo_name = f"repo-cf-{uuid.uuid4().hex[:6]}"
    data = b"ref upsert test"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
            sha = r_blob.json()["sha256"]
            resp = await c.post(
                f"/repos/test/{repo_name}/commits",
                json={
                    "tree": {
                        "entries": [
                            {"name": "f.txt", "mode": 33188, "entry_type": "blob", "target_hash": sha}
                        ]
                    },
                    "parents": [],
                    "author_id": "u1",
                    "ref": "main",
                },
            )
            commit_hash = resp.json()["hash"]
        # 直接查 DB 确认 ref
        engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with factory() as s:
            row = (
                await s.execute(
                    text(
                        "SELECT r.name, r.commit_hash FROM refs r JOIN repositories rp "
                        "ON r.repo_id=rp.id WHERE rp.owner=:o AND rp.name=:n"
                    ),
                    {"o": "test", "n": repo_name},
                )
            ).first()
        assert row is not None
        assert row[0] == "main"
        assert row[1] == commit_hash
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (g2) 顺序幂等：相同 payload 二次 POST → deduplicated=true ---------


@pytest.mark.asyncio
async def test_g2_idempotent_repeat_post_dedup_true(admin_user: dict) -> None:
    repo_name = f"repo-cg-{uuid.uuid4().hex[:6]}"
    data = b"idempotent test"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
            sha = r_blob.json()["sha256"]
            payload = {
                "tree": {
                    "entries": [
                        {"name": "g.txt", "mode": 33188, "entry_type": "blob", "target_hash": sha}
                    ]
                },
                "parents": [],
                "author_id": "u1",
                "message": "idem",
            }
            r1 = await c.post(f"/repos/test/{repo_name}/commits", json=payload)
            r2 = await c.post(f"/repos/test/{repo_name}/commits", json=payload)
        assert r1.json()["hash"] == r2.json()["hash"]
        assert r1.json()["deduplicated"] is False
        assert r2.json()["deduplicated"] is True
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (h) GET commit → 含 tree.entries ---------


@pytest.mark.asyncio
async def test_h_get_commit_includes_tree_entries(admin_user: dict) -> None:
    repo_name = f"repo-ch-{uuid.uuid4().hex[:6]}"
    data = b"get commit content"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
            sha = r_blob.json()["sha256"]
            r_commit = await c.post(
                f"/repos/test/{repo_name}/commits",
                json={
                    "tree": {
                        "entries": [
                            {"name": "h.txt", "mode": 33188, "entry_type": "blob", "target_hash": sha}
                        ]
                    },
                    "parents": [],
                    "author_id": "u1",
                },
            )
            commit_hash = r_commit.json()["hash"]
            r_get = await c.get(f"/repos/test/{repo_name}/commits/{commit_hash}")
        assert r_get.status_code == 200
        body = r_get.json()
        assert body["hash"] == commit_hash
        assert body["tree"]["entries"][0]["name"] == "h.txt"
        assert body["tree"]["entries"][0]["target_hash"] == sha
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (i) GET commit 不存在 → 404 ---------


@pytest.mark.asyncio
async def test_i_get_commit_unknown_hash_404(admin_user: dict) -> None:
    repo_name = f"repo-ci-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r = await c.get(f"/repos/test/{repo_name}/commits/{'a' * 64}")
        assert r.status_code == 404
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (j) GET blob → 流式字节正确 ---------


@pytest.mark.asyncio
async def test_j_get_blob_streams_correct_bytes(admin_user: dict) -> None:
    repo_name = f"repo-cj-{uuid.uuid4().hex[:6]}"
    data = b"stream this back" * 100
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
            sha = r_blob.json()["sha256"]
            r_get = await c.get(f"/repos/test/{repo_name}/blobs/{sha}")
        assert r_get.status_code == 200
        assert r_get.content == data
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (k) GET blob 不存在 → 404 ---------


@pytest.mark.asyncio
async def test_k_get_blob_unknown_404(admin_user: dict) -> None:
    repo_name = f"repo-ck-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r = await c.get(f"/repos/test/{repo_name}/blobs/{'9' * 64}")
        assert r.status_code == 404
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (l) 匿名 GET on private repo → 404 ---------


@pytest.mark.asyncio
async def test_l_anonymous_private_repo_returns_404(admin_user: dict) -> None:
    repo_name = f"repo-cl-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "private")
        async with AsyncClient(transport=transport, base_url="https://test") as anon:
            r_blob = await anon.get(f"/repos/test/{repo_name}/blobs/{'a' * 64}")
            r_commit = await anon.get(f"/repos/test/{repo_name}/commits/{'a' * 64}")
            r_tree = await anon.get(f"/repos/test/{repo_name}/tree/{'a' * 64}")
        assert r_blob.status_code == 404
        assert r_commit.status_code == 404
        assert r_tree.status_code == 404
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (m) 匿名 GET public repo blob → 200 ---------


@pytest.mark.asyncio
async def test_m_anonymous_public_repo_blob_200(admin_user: dict) -> None:
    repo_name = f"repo-cm-{uuid.uuid4().hex[:6]}"
    data = b"public blob content"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
            sha = r_blob.json()["sha256"]
        async with AsyncClient(transport=transport, base_url="https://test") as anon:
            r = await anon.get(f"/repos/test/{repo_name}/blobs/{sha}")
        assert r.status_code == 200
        assert r.content == data
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (n) 2MB 大文件流式 round-trip ---------


@pytest.mark.asyncio
async def test_n_2mb_streaming_roundtrip(admin_user: dict) -> None:
    """spec 风险 #2 缓解措施：2MB+17 字节随机内容，sha256 与本地 hashlib 一致。"""
    repo_name = f"repo-cn-{uuid.uuid4().hex[:6]}"
    data = secrets.token_bytes(2 * 1024 * 1024 + 17)
    expected_sha = hashlib.sha256(data).hexdigest()
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
            assert r_blob.json()["sha256"] == expected_sha
            assert r_blob.json()["size"] == len(data)
            r_get = await c.get(f"/repos/test/{repo_name}/blobs/{expected_sha}")
        assert r_get.status_code == 200
        assert hashlib.sha256(r_get.content).hexdigest() == expected_sha
        assert len(r_get.content) == len(data)
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (o) lineage round-trip ---------


@pytest.mark.asyncio
async def test_o_lineage_roundtrip(admin_user: dict) -> None:
    """spec 风险 #5 缓解措施：lineage JSONB POST → GET 反序列化为完整 Lineage 模型。"""
    repo_name = f"repo-co-{uuid.uuid4().hex[:6]}"
    data = b"lineage roundtrip content"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
            sha = r_blob.json()["sha256"]
            r_commit = await c.post(
                f"/repos/test/{repo_name}/commits",
                json={
                    "tree": {
                        "entries": [
                            {"name": "o.txt", "mode": 33188, "entry_type": "blob", "target_hash": sha}
                        ]
                    },
                    "parents": [],
                    "author_id": "u1",
                    "lineage": {
                        "produced_by": {
                            "kind": "processor",
                            "name": "llm-qa-gen",
                            "version": "0.5",
                            "config_hash": "c" * 64,
                        },
                        "inputs": [
                            {"repo": "silver/cn-lit/normalized-text-v1", "commit": "a" * 64}
                        ],
                        "run_id": "r1",
                        "env": {"python": "3.12"},
                    },
                },
            )
            commit_hash = r_commit.json()["hash"]
            r_get = await c.get(f"/repos/test/{repo_name}/commits/{commit_hash}")
        body = r_get.json()
        ln = body["lineage"]
        assert ln is not None
        assert ln["produced_by"]["kind"] == "processor"
        assert ln["produced_by"]["name"] == "llm-qa-gen"
        assert ln["inputs"][0]["repo"] == "silver/cn-lit/normalized-text-v1"
        assert ln["inputs"][0]["commit"] == "a" * 64
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (p) user GET commit on internal repo → 200 ---------


@pytest.mark.asyncio
async def test_p_user_get_internal_commit_200(
    admin_user: dict, normal_user: dict
) -> None:
    repo_name = f"repo-cp-{uuid.uuid4().hex[:6]}"
    data = b"internal commit content"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await _create_repo(a, "test", repo_name, "internal")
            r_blob = await a.post(f"/repos/test/{repo_name}/blobs", content=data)
            sha = r_blob.json()["sha256"]
            r_commit = await a.post(
                f"/repos/test/{repo_name}/commits",
                json={
                    "tree": {
                        "entries": [
                            {"name": "p.txt", "mode": 33188, "entry_type": "blob", "target_hash": sha}
                        ]
                    },
                    "parents": [],
                    "author_id": "u1",
                },
            )
            commit_hash = r_commit.json()["hash"]
        async with AsyncClient(transport=transport, base_url="https://test") as u:
            await _login(u, normal_user)
            r = await u.get(f"/repos/test/{repo_name}/commits/{commit_hash}")
        assert r.status_code == 200
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (q) user GET commit on private repo → 404 ---------


@pytest.mark.asyncio
async def test_q_user_get_private_commit_404(
    admin_user: dict, normal_user: dict
) -> None:
    repo_name = f"repo-cq-{uuid.uuid4().hex[:6]}"
    data = b"private commit content"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await _create_repo(a, "test", repo_name, "private")
            r_blob = await a.post(f"/repos/test/{repo_name}/blobs", content=data)
            sha = r_blob.json()["sha256"]
            r_commit = await a.post(
                f"/repos/test/{repo_name}/commits",
                json={
                    "tree": {
                        "entries": [
                            {"name": "q.txt", "mode": 33188, "entry_type": "blob", "target_hash": sha}
                        ]
                    },
                    "parents": [],
                    "author_id": "u1",
                },
            )
            commit_hash = r_commit.json()["hash"]
        async with AsyncClient(transport=transport, base_url="https://test") as u:
            await _login(u, normal_user)
            r = await u.get(f"/repos/test/{repo_name}/commits/{commit_hash}")
        assert r.status_code == 404
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- blob_meta (a) 上传 → GET /blobs/{sha}/meta → 200 + size 正确 ---------


@pytest.mark.asyncio
async def test_blob_meta_returns_size(admin_user: dict) -> None:
    repo_name = f"repo-bm-{uuid.uuid4().hex[:6]}"
    data = b"hello"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
            assert r_blob.status_code == 201
            sha = r_blob.json()["sha256"]

            r_meta = await c.get(f"/repos/test/{repo_name}/blobs/{sha}/meta")
            assert r_meta.status_code == 200
            body = r_meta.json()
            assert body["sha256"] == sha
            assert body["size"] == len(data)
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- blob_meta (b) GET /blobs/{9*64}/meta → 404 ---------


@pytest.mark.asyncio
async def test_blob_meta_not_found(admin_user: dict) -> None:
    repo_name = f"repo-bm-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r = await c.get(f"/repos/test/{repo_name}/blobs/{'9' * 64}/meta")
            assert r.status_code == 404
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- blob_meta (c) 匿名 GET public repo blob meta → 200 ---------


@pytest.mark.asyncio
async def test_blob_meta_public_anon(admin_user: dict) -> None:
    repo_name = f"repo-bm-{uuid.uuid4().hex[:6]}"
    data = b"public meta content"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
            sha = r_blob.json()["sha256"]

        async with AsyncClient(transport=transport, base_url="https://test") as anon:
            r_meta = await anon.get(f"/repos/test/{repo_name}/blobs/{sha}/meta")
        assert r_meta.status_code == 200
        body = r_meta.json()
        assert body["sha256"] == sha
        assert body["size"] == len(data)
    finally:
        await _delete_repo_cascade("test", repo_name)
