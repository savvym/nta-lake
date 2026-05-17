"""Refs HTTP 集成测试（spec repo-files-tab-20260517 AC-10）。

3 测试覆盖：
- (a) admin ingest commit + ref=main → GET /refs/main → 200
- (b) 不存在 ref → 404
- (c) anon GET private repo refs → 404
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator

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
    reason="PG / MinIO 未通；refs 集成跳过",
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
    store = MinioBlobStore(endpoint_url=endpoint, access_key=ak, secret_key=sk, bucket=bucket)
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


# --------- (a) admin POST commit ref=main → GET refs/main 200 ---------


@pytest.mark.asyncio
async def test_a_get_ref_after_commit(admin_user: dict) -> None:
    repo_name = f"repo-ra-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(
                f"/repos/test/{repo_name}/blobs", content=b"content for ref test"
            )
            sha = r_blob.json()["sha256"]
            r_commit = await c.post(
                f"/repos/test/{repo_name}/commits",
                json={
                    "tree": {
                        "entries": [
                            {"name": "a.md", "mode": 33188, "entry_type": "blob", "target_hash": sha}
                        ]
                    },
                    "parents": [],
                    "author_id": "u1",
                    "ref": "main",
                },
            )
            commit_hash = r_commit.json()["hash"]
            r_ref = await c.get(f"/repos/test/{repo_name}/refs/main")
        assert r_ref.status_code == 200
        body = r_ref.json()
        assert body["name"] == "main"
        assert body["commit_hash"] == commit_hash
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (b) GET 不存在 ref → 404 ---------


@pytest.mark.asyncio
async def test_b_unknown_ref_404(admin_user: dict) -> None:
    repo_name = f"repo-rb-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r = await c.get(f"/repos/test/{repo_name}/refs/no-such-ref")
        assert r.status_code == 404
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (c) anon GET private repo refs → 404（不泄露） ---------


@pytest.mark.asyncio
async def test_c_anon_private_repo_refs_404(admin_user: dict) -> None:
    repo_name = f"repo-rc-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await _create_repo(a, "test", repo_name, "private")
        async with AsyncClient(transport=transport, base_url="https://test") as anon:
            r = await anon.get(f"/repos/test/{repo_name}/refs/main")
        assert r.status_code == 404
    finally:
        await _delete_repo_cascade("test", repo_name)
