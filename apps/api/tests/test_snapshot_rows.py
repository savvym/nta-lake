"""Snapshot rows API 集成测试（W4-1 web-pdf-mineru-ui-v2-20260520）。

4 个测试覆盖验收标准 AC-1/AC-2/AC-3：
- test_rows_happy_paginated       AC-1  happy path: 3 行 JSONL → 分页取 2 行
- test_rows_snapshot_not_found    AC-2  404: snapshot hash 不存在
- test_rows_jsonl_resolution_errors AC-3 422: (a) 无 .jsonl entry; (b) ambiguous .jsonl entries

依赖（同 test_commits.py / test_snapshots_api.py）：
- Postgres（DATAPLAT_DATABASE_URL）
- MinIO（DATAPLAT_MINIO_ENDPOINT；fixture 用唯一 bucket 隔离）
- conftest 早设 JWT_SECRET + USE_NULL_POOL
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import AsyncGenerator, Generator

import boto3
import pytest
from dataplat_api.auth.password import hash_password
from dataplat_api.main import app
from dataplat_api.models import UserORM
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
    reason="DATAPLAT_DATABASE_URL / DATAPLAT_MINIO_ENDPOINT 未设置；snapshot-rows 集成跳过",
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


@pytest.fixture(autouse=True)
def _override_blob_store() -> Generator[None, None, None]:
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


async def _login(client: AsyncClient, user: dict) -> None:
    resp = await client.post(
        "/auth/login",
        json={"username": user["username"], "password": user["password"]},
    )
    assert resp.status_code == 200, f"login failed: {resp.text}"


async def _create_repo(
    client: AsyncClient, owner: str, name: str, vis: str = "public"
) -> None:
    resp = await client.post(
        "/repos",
        json={
            "owner": owner,
            "name": name,
            "layer": "bronze",
            "subtype": "pdf",
            "visibility": vis,
        },
    )
    assert resp.status_code == 201, f"create_repo failed: {resp.text}"


def _make_silver_jsonl(rows: list[dict]) -> bytes:
    """生成 silver JSONL bytes，每行是一个 SilverRow JSON。"""
    lines = []
    for row in rows:
        lines.append(json.dumps(row))
    return "\n".join(lines).encode("utf-8")


# --------- AC-1: happy path 分页 ---------


@pytest.mark.asyncio
async def test_rows_happy_paginated(admin_user: dict) -> None:
    """AC-1: 3 行 JSONL → GET rows?offset=0&limit=2 → 200, total=3, len(rows)=2, rows[0].text 正确。"""
    repo_name = f"repo-rows-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)

    silver_rows = [
        {
            "text": "row text 1",
            "images": [],
            "source_ref": {"blob_sha": "a" * 64, "path": "p1.pdf"},
            "stats": {"char_count": 10},
            "lineage_ops": [],
        },
        {
            "text": "row text 2",
            "images": [],
            "source_ref": {"blob_sha": "b" * 64, "path": "p2.pdf"},
            "stats": {"char_count": 10},
            "lineage_ops": [],
        },
        {
            "text": "row text 3",
            "images": [],
            "source_ref": {"blob_sha": "c" * 64, "path": "p3.pdf"},
            "stats": {"char_count": 10},
            "lineage_ops": [],
        },
    ]
    jsonl_bytes = _make_silver_jsonl(silver_rows)

    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")

            # 上传 JSONL blob
            r_blob = await c.post(
                f"/repos/test/{repo_name}/blobs",
                content=jsonl_bytes,
                headers={"content-type": "application/octet-stream"},
            )
            assert r_blob.status_code == 201, f"upload blob failed: {r_blob.text}"
            blob_sha = r_blob.json()["sha256"]

            # 创建 snapshot，tree 含 data.jsonl entry
            r_snap = await c.post(
                f"/repos/test/{repo_name}/snapshots",
                json={
                    "tree": {
                        "entries": [
                            {
                                "name": "data.jsonl",
                                "mode": 33188,
                                "entry_type": "blob",
                                "target_hash": blob_sha,
                            }
                        ]
                    },
                    "author_id": "test-user",
                    "message": "silver rows test",
                },
            )
            assert r_snap.status_code == 200, f"create snapshot failed: {r_snap.text}"
            snap_hash = r_snap.json()["hash"]

            # GET rows?offset=0&limit=2
            r_rows = await c.get(
                f"/repos/test/{repo_name}/snapshots/{snap_hash}/rows?offset=0&limit=2"
            )

        assert r_rows.status_code == 200, f"get rows failed: {r_rows.text}"
        body = r_rows.json()
        assert body["total"] == 3, f"total 应为 3，实际 {body['total']}"
        assert body["offset"] == 0
        assert body["limit"] == 2
        assert len(body["rows"]) == 2, f"rows 应有 2 行，实际 {len(body['rows'])}"
        assert body["blob_sha"] == blob_sha, "blob_sha 应与 entry sha 一致"
        assert body["rows"][0]["text"] == "row text 1", f"rows[0].text 错误: {body['rows'][0]['text']}"
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- AC-2: snapshot not found 404 ---------


@pytest.mark.asyncio
async def test_rows_snapshot_not_found(admin_user: dict) -> None:
    """AC-2: GET 不存在的 snapshot hash → 404, detail 含 'Snapshot' 和 '不存在'。"""
    repo_name = f"repo-rows-404-{uuid.uuid4().hex[:6]}"
    fake_hash = "e" * 64
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r = await c.get(f"/repos/test/{repo_name}/snapshots/{fake_hash}/rows")
        assert r.status_code == 404, f"期望 404，实际 {r.status_code}: {r.text}"
        detail = r.json().get("detail", "")
        assert "Snapshot" in detail, f"detail 应含 'Snapshot'，实际: {detail}"
        assert "不存在" in detail, f"detail 应含 '不存在'，实际: {detail}"
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- AC-3: 422 jsonl resolution errors ---------


@pytest.mark.asyncio
async def test_rows_jsonl_resolution_errors(admin_user: dict) -> None:
    """AC-3: (a) tree 无 .jsonl entry → 422 detail 含 'no_jsonl_entry';
    (b) tree 有 2 个 .jsonl entry 且未传 blob_sha → 422 detail 含 'ambiguous_blob_sha'。
    """
    transport = ASGITransport(app=app)

    # --- sub-case (a): tree 无 .jsonl entry ---
    repo_name_a = f"repo-rows-nojsonl-{uuid.uuid4().hex[:6]}"
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name_a, "public")

            # 上传一个非 .jsonl 文件
            r_blob = await c.post(
                f"/repos/test/{repo_name_a}/blobs",
                content=b"not a jsonl file",
                headers={"content-type": "application/octet-stream"},
            )
            assert r_blob.status_code == 201
            blob_sha = r_blob.json()["sha256"]

            r_snap = await c.post(
                f"/repos/test/{repo_name_a}/snapshots",
                json={
                    "tree": {
                        "entries": [
                            {
                                "name": "data.txt",
                                "mode": 33188,
                                "entry_type": "blob",
                                "target_hash": blob_sha,
                            }
                        ]
                    },
                    "author_id": "test-user",
                },
            )
            assert r_snap.status_code == 200
            snap_hash = r_snap.json()["hash"]

            r = await c.get(f"/repos/test/{repo_name_a}/snapshots/{snap_hash}/rows")

        assert r.status_code == 422, f"期望 422，实际 {r.status_code}: {r.text}"
        detail_a = r.json().get("detail", "")
        assert "no_jsonl_entry" in detail_a, f"detail 应含 'no_jsonl_entry'，实际: {detail_a}"
    finally:
        await _delete_repo_cascade("test", repo_name_a)

    # --- sub-case (b): tree 有 2 个 .jsonl entry，未传 blob_sha ---
    repo_name_b = f"repo-rows-ambig-{uuid.uuid4().hex[:6]}"
    try:
        jsonl_bytes = _make_silver_jsonl([
            {
                "text": "row 1",
                "images": [],
                "source_ref": {"blob_sha": "a" * 64},
                "stats": {},
                "lineage_ops": [],
            }
        ])
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name_b, "public")

            r_blob1 = await c.post(
                f"/repos/test/{repo_name_b}/blobs",
                content=jsonl_bytes,
                headers={"content-type": "application/octet-stream"},
            )
            assert r_blob1.status_code == 201
            sha1 = r_blob1.json()["sha256"]

            # 上传第二个不同内容的 jsonl
            jsonl_bytes2 = _make_silver_jsonl([
                {
                    "text": "row 2",
                    "images": [],
                    "source_ref": {"blob_sha": "b" * 64},
                    "stats": {},
                    "lineage_ops": [],
                }
            ])
            r_blob2 = await c.post(
                f"/repos/test/{repo_name_b}/blobs",
                content=jsonl_bytes2,
                headers={"content-type": "application/octet-stream"},
            )
            assert r_blob2.status_code == 201
            sha2 = r_blob2.json()["sha256"]

            # tree 含 2 个 .jsonl entry
            r_snap = await c.post(
                f"/repos/test/{repo_name_b}/snapshots",
                json={
                    "tree": {
                        "entries": [
                            {
                                "name": "data1.jsonl",
                                "mode": 33188,
                                "entry_type": "blob",
                                "target_hash": sha1,
                            },
                            {
                                "name": "data2.jsonl",
                                "mode": 33188,
                                "entry_type": "blob",
                                "target_hash": sha2,
                            },
                        ]
                    },
                    "author_id": "test-user",
                },
            )
            assert r_snap.status_code == 200
            snap_hash_b = r_snap.json()["hash"]

            r = await c.get(f"/repos/test/{repo_name_b}/snapshots/{snap_hash_b}/rows")

        assert r.status_code == 422, f"期望 422，实际 {r.status_code}: {r.text}"
        detail_b = r.json().get("detail", "")
        assert "ambiguous_blob_sha" in detail_b, f"detail 应含 'ambiguous_blob_sha'，实际: {detail_b}"
    finally:
        await _delete_repo_cascade("test", repo_name_b)
