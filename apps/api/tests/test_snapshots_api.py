"""Snapshot API 集成测试（W1-1 api-snapshot-rename-20260520 AC-9 / AC-10）。

AC-9：create snapshot + get snapshot roundtrip（parent 字段 / 无 parents 字段）。
AC-10：老路径 /commits 返 308 Permanent Redirect + Location header。

依赖（同 test_commits.py）：
- Postgres（DATAPLAT_DATABASE_URL）
- MinIO（DATAPLAT_MINIO_ENDPOINT；fixture 用唯一 bucket 隔离）
- conftest 早设 JWT_SECRET + USE_NULL_POOL

D-13：不在本文件加 self_check block；业务正确性靠本测试文件覆盖。
"""

from __future__ import annotations

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
    reason="DATAPLAT_DATABASE_URL / DATAPLAT_MINIO_ENDPOINT 未设置；snapshot 集成跳过",
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


async def _create_repo(client: AsyncClient, owner: str, name: str, vis: str = "public") -> None:
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


# --------- AC-9: create + get snapshot roundtrip ---------


@pytest.mark.asyncio
async def test_create_snapshot_then_get_200(admin_user: dict) -> None:
    """AC-9: POST /snapshots 200 + 响应含 parent 字段（非 parents）; GET /snapshots/{hash} 200。"""
    repo_name = f"repo-snap-{uuid.uuid4().hex[:6]}"
    data = b"hello snapshot"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")

            # 上传 blob
            r_blob = await c.post(
                f"/repos/test/{repo_name}/blobs",
                content=data,
                headers={"content-type": "application/octet-stream"},
            )
            assert r_blob.status_code == 201, f"upload blob failed: {r_blob.text}"
            sha = r_blob.json()["sha256"]

            # POST /snapshots（无 parent = root snapshot）
            r_create = await c.post(
                f"/repos/test/{repo_name}/snapshots",
                json={
                    "tree": {
                        "entries": [
                            {
                                "name": "data.txt",
                                "mode": 33188,
                                "entry_type": "blob",
                                "target_hash": sha,
                            }
                        ]
                    },
                    "author_id": "test-user",
                },
            )
        assert r_create.status_code == 200, f"create snapshot failed: {r_create.text}"
        body = r_create.json()
        # 响应含 parent 字段，不含 parents 字段
        assert "parent" in body, "响应应含 parent 字段"
        assert "parents" not in body, "响应不应含 parents 字段"
        assert body["parent"] is None, "root snapshot 的 parent 应为 null"
        assert "hash" in body
        snap_hash = body["hash"]

        # GET /snapshots/{hash}
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            r_get = await c.get(f"/repos/test/{repo_name}/snapshots/{snap_hash}")
        assert r_get.status_code == 200, f"get snapshot failed: {r_get.text}"
        get_body = r_get.json()
        assert get_body["hash"] == snap_hash, "GET 响应 hash 应与创建时一致"
        assert get_body["parent"] is None
        assert "parents" not in get_body
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- AC-10: 308 兼容 ---------


@pytest.mark.asyncio
async def test_old_commits_path_redirects_308(admin_user: dict) -> None:
    """AC-10: POST /commits 返 308 + Location=/snapshots; GET /commits/{hash} 同理。"""
    repo_name = f"repo-redir-{uuid.uuid4().hex[:6]}"
    fake_hash = "a" * 64
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(
            transport=transport,
            base_url="https://test",
            follow_redirects=False,  # 不跟 redirect，验证 308
        ) as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")

            # POST /commits → 308
            r_post = await c.post(
                f"/repos/test/{repo_name}/commits",
                json={
                    "tree": {"entries": []},
                    "author_id": "test-user",
                },
            )
            assert r_post.status_code == 308, f"期望 308，实际 {r_post.status_code}: {r_post.text}"
            location_post = r_post.headers.get("location", "")
            assert "/snapshots" in location_post, (
                f"POST /commits Location header 应包含 /snapshots；实际: {location_post}"
            )

            # GET /commits/{hash} → 308
            r_get = await c.get(f"/repos/test/{repo_name}/commits/{fake_hash}")
            assert r_get.status_code == 308, f"期望 308，实际 {r_get.status_code}: {r_get.text}"
            location_get = r_get.headers.get("location", "")
            assert f"/snapshots/{fake_hash}" in location_get, (
                f"GET /commits/{{hash}} Location header 应包含 /snapshots/{{hash}}；实际: {location_get}"
            )
    finally:
        await _delete_repo_cascade("test", repo_name)
