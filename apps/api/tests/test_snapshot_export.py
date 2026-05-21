"""Snapshot export API 集成测试（W4-4 web-snapshot-export-ui-20260520）。

3 个测试覆盖验收标准 AC-2/AC-3：
- test_export_hf_datasets_happy     AC-2  happy: 2 行 silver → POST format=hf_datasets → 200 + tar.gz + headers
- test_export_format_jsonl_returns_422   AC-3  format=jsonl → 422 + detail 含"未实现"
- test_export_snapshot_not_found        AC-3  不存在 snapshot hash → 404

依赖（同 test_snapshot_rows.py）：
- Postgres（DATAPLAT_DATABASE_URL）
- MinIO（DATAPLAT_MINIO_ENDPOINT；fixture 用唯一 bucket 隔离）
- conftest 早设 JWT_SECRET + USE_NULL_POOL
"""

from __future__ import annotations

import io
import json
import os
import tarfile
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
    reason="DATAPLAT_DATABASE_URL / DATAPLAT_MINIO_ENDPOINT 未设置；snapshot-export 集成跳过",
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
            "layer": "silver",
            "subtype": "jsonl",
            "visibility": vis,
        },
    )
    assert resp.status_code == 201, f"create_repo failed: {resp.text}"


def _make_silver_jsonl(rows: list[dict]) -> bytes:
    """生成 silver JSONL bytes。"""
    lines = []
    for row in rows:
        lines.append(json.dumps(row))
    return "\n".join(lines).encode("utf-8")


# --------- AC-2: happy path ---------


@pytest.mark.asyncio
async def test_export_hf_datasets_happy(admin_user: dict) -> None:
    """AC-2: 2 行 silver JSONL → POST format=hf_datasets → 200 + content-type=application/gzip
    + tar.gz 解开含 dataset_info.json + state.json + .arrow file + X-Snapshot-Row-Count == '2'。
    """
    repo_name = f"repo-export-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)

    silver_rows = [
        {
            "text": "export row one",
            "images": [],
            "source_ref": {"blob_sha": "a" * 64, "path": "doc1.pdf"},
            "stats": {"char_count": 14},
            "lineage_ops": [],
        },
        {
            "text": "export row two",
            "images": [],
            "source_ref": {"blob_sha": "b" * 64, "path": "doc2.pdf"},
            "stats": {"char_count": 14},
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
                    "message": "export test snapshot",
                },
            )
            assert r_snap.status_code == 200, f"create snapshot failed: {r_snap.text}"
            snap_hash = r_snap.json()["hash"]

            # POST export
            r_export = await c.post(
                f"/repos/test/{repo_name}/snapshots/{snap_hash}/exports",
                json={"format": "hf_datasets", "split": "train"},
            )

        assert r_export.status_code == 200, f"export failed: {r_export.text}"
        assert "application/gzip" in r_export.headers.get("content-type", ""), (
            f"content-type 应含 application/gzip，实际 {r_export.headers.get('content-type')}"
        )

        # 检查自定义 headers
        row_count_header = r_export.headers.get("x-snapshot-row-count")
        assert row_count_header == "2", f"X-Snapshot-Row-Count 应为 '2'，实际 {row_count_header}"
        blob_sha_header = r_export.headers.get("x-snapshot-blob-sha")
        assert blob_sha_header == blob_sha, f"X-Snapshot-Blob-Sha 应为 {blob_sha}，实际 {blob_sha_header}"

        # 解开 tar.gz，检查内容
        tar_bytes = r_export.content
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
            names = tar.getnames()

        assert any("dataset_info.json" in n for n in names), (
            f"tar.gz 应含 dataset_info.json，实际 names: {names}"
        )
        assert any("state.json" in n for n in names), (
            f"tar.gz 应含 state.json，实际 names: {names}"
        )
        assert any(n.endswith(".arrow") for n in names), (
            f"tar.gz 应含 .arrow 文件，实际 names: {names}"
        )
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- AC-3: format=jsonl → 422 ---------


@pytest.mark.asyncio
async def test_export_format_jsonl_returns_422(admin_user: dict) -> None:
    """AC-3: POST format=jsonl → 422，detail 含"未实现"。"""
    repo_name = f"repo-export-jsonl-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    fake_hash = "a" * 64

    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")

            # 创建一个 dummy snapshot（这个测试 format 422 在 snapshot 解析前就返回，
            # 但为了确保 repo 存在，还是创建一个）
            # 实际上，format 检查在 _resolve_repo 之前，直接 POST 就能触发 422
            r = await c.post(
                f"/repos/test/{repo_name}/snapshots/{fake_hash}/exports",
                json={"format": "jsonl"},
            )

        assert r.status_code == 422, f"期望 422，实际 {r.status_code}: {r.text}"
        detail = r.json().get("detail", "")
        assert "未实现" in detail, f"detail 应含'未实现'，实际: {detail}"
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- AC-3: snapshot not found 404 ---------


@pytest.mark.asyncio
async def test_export_snapshot_not_found(admin_user: dict) -> None:
    """AC-3: POST 不存在的 snapshot hash → 404。"""
    repo_name = f"repo-export-404-{uuid.uuid4().hex[:6]}"
    fake_hash = "e" * 64
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")

            r = await c.post(
                f"/repos/test/{repo_name}/snapshots/{fake_hash}/exports",
                json={"format": "hf_datasets"},
            )

        assert r.status_code == 404, f"期望 404，实际 {r.status_code}: {r.text}"
        detail = r.json().get("detail", "")
        assert "Snapshot" in detail, f"detail 应含'Snapshot'，实际: {detail}"
        assert "不存在" in detail, f"detail 应含'不存在'，实际: {detail}"
    finally:
        await _delete_repo_cascade("test", repo_name)
