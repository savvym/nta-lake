"""Processor framework 集成 + 单元测试（spec processor-framework-20260517 AC-10）。

8 测试：a registry / b processor 单元 / c DbRepoView open / d admin POST 201 /
e user 403 / f 端到端 ingest→process succeeded / g unknown processor 404 / h source ref 不存在。
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator

import boto3
import pytest
import redis as redis_lib
from dataplat_api.auth.password import hash_password
from dataplat_api.jobs.redis_client import get_queue, get_redis
from dataplat_api.main import app
from dataplat_api.models import UserORM
from dataplat_api.processors.markdown_normalize import MarkdownNormalizeProcessor
from dataplat_api.runner.processor_registry import (
    ProcessorRegistry,
    get_processor_registry,
)
from dataplat_api.runner.repo_view import DbRepoView
from dataplat_api.storage import get_blob_store
from dataplat_api.storage.minio_store import MinioBlobStore
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _db_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


def _minio_endpoint() -> str | None:
    return os.environ.get("DATAPLAT_MINIO_ENDPOINT")


def _redis_url() -> str:
    return os.environ.get("DATAPLAT_REDIS_URL", "redis://localhost:6379/0")


def _redis_reachable() -> bool:
    try:
        r = redis_lib.Redis.from_url(_redis_url(), socket_connect_timeout=1)
        r.ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not (_db_url() and _minio_endpoint() and _redis_reachable()),
    reason="PG / MinIO / Redis 任一未通；processor 集成跳过",
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
def _override_blob_store(monkeypatch) -> AsyncGenerator[None, None]:  # type: ignore[no-untyped-def]
    bucket = f"dataplat-test-{uuid.uuid4().hex[:8]}"
    endpoint = os.environ.get("DATAPLAT_MINIO_ENDPOINT", "http://localhost:9000")
    ak = os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat")
    sk = os.environ.get("DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret")
    store = MinioBlobStore(endpoint_url=endpoint, access_key=ak, secret_key=sk, bucket=bucket)
    app.dependency_overrides[get_blob_store] = lambda: store

    import dataplat_api.storage as storage_mod
    monkeypatch.setattr(storage_mod, "_blob_store", None)
    monkeypatch.setenv("DATAPLAT_BLOB_BUCKET", bucket)
    monkeypatch.setenv("DATAPLAT_MINIO_ENDPOINT", endpoint)
    monkeypatch.setenv("DATAPLAT_MINIO_ACCESS_KEY", ak)
    monkeypatch.setenv("DATAPLAT_MINIO_SECRET_KEY", sk)
    try:
        yield  # type: ignore[misc]
    finally:
        storage_mod._blob_store = None
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


@pytest.fixture(autouse=True)
def _clear_redis_queue() -> None:
    try:
        get_queue().empty()
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


async def _run_worker_burst() -> None:
    import asyncio
    from importlib import import_module

    from rq.job import Job

    def _work() -> None:
        queue = get_queue()
        conn = get_redis()
        while True:
            if queue.is_empty():
                break
            try:
                job_id = queue.pop_job_id()
            except Exception:  # noqa: BLE001
                break
            if not job_id:
                break
            try:
                job = Job.fetch(job_id, connection=conn)
            except Exception:  # noqa: BLE001
                continue
            module_path, func_name = job.func_name.rsplit(".", 1)
            module = import_module(module_path)
            func = getattr(module, func_name)
            try:
                func(*(job.args or ()), **(job.kwargs or {}))
            except Exception:  # noqa: BLE001
                pass

    await asyncio.to_thread(_work)


# --------- (a) registry register/get/list 单元 ---------


def test_a_registry_register_get_list() -> None:
    reg = ProcessorRegistry()
    assert reg.list_all() == []
    reg.register(MarkdownNormalizeProcessor())
    assert reg.get("markdown-normalize", "0.1") is not None
    # 全局单例自动注册了
    assert get_processor_registry().get("markdown-normalize", "0.1") is not None


# --------- (b) markdown-normalize 单元（mock blob_store）---------


def test_b_markdown_normalize_unit() -> None:
    """直接调 processor.run，验证 CRLF + trailing ws + 折叠 ≥3 空行。"""
    import asyncio
    import io as _io

    from dataplat_api.runner.runcontext import StandardRunContext

    raw = b"line1   \r\nline2\r\n\r\n\r\n\r\nline5\r\n"
    expected = b"line1\nline2\n\nline5\n"

    class _FakeStore:
        def __init__(self) -> None:
            self.uploaded: list[bytes] = []

        async def put(self, stream, declared_size=None):  # type: ignore[no-untyped-def]
            from dataplat_core.protocols.storage import BlobPutResult

            data = stream.read()
            self.uploaded.append(data)
            import hashlib
            sha = hashlib.sha256(data).hexdigest()
            return BlobPutResult(
                sha256=sha,
                size=len(data),
                storage_key=f"blobs/{sha[:2]}/{sha}",
                deduplicated=False,
            )

    class _FakeView:
        def __init__(self) -> None:
            self._paths = ["a.md"]

        @property
        def repo_id(self):  # type: ignore[no-untyped-def]
            return "r1"

        @property
        def commit_hash(self):  # type: ignore[no-untyped-def]
            return "c" * 64

        def iter_paths(self):  # type: ignore[no-untyped-def]
            return self._paths

        def open(self, path):  # type: ignore[no-untyped-def]
            return _io.BytesIO(raw)

        def iter_records(self):  # type: ignore[no-untyped-def]
            raise NotImplementedError

    store = _FakeStore()
    import logging
    ctx = StandardRunContext(
        logger=logging.getLogger("test"), blob_store=store
    )

    p = MarkdownNormalizeProcessor()
    result = asyncio.run(_run_processor(p, _FakeView(), ctx))
    assert result.file_count == 1
    assert len(store.uploaded) == 1
    assert store.uploaded[0] == expected


async def _run_processor(p, view, ctx):  # type: ignore[no-untyped-def]
    """processor.run 是同步的；asyncio.to_thread 包。"""
    import asyncio
    from pathlib import Path

    return await asyncio.to_thread(p.run, [view], {}, Path("/tmp"), ctx)


# --------- (c) DbRepoView.open round-trip ---------


@pytest.mark.asyncio
async def test_c_db_repo_view_open_roundtrip(admin_user: dict) -> None:
    repo_name = f"repo-pc-{uuid.uuid4().hex[:6]}"
    data = b"# Hello\n\nLine 2\n"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r_blob = await c.post(
                f"/repos/test/{repo_name}/blobs", content=data
            )
            sha = r_blob.json()["sha256"]
            r_commit = await c.post(
                f"/repos/test/{repo_name}/commits",
                json={
                    "tree": {
                        "entries": [
                            {"name": "hi.md", "mode": 33188, "entry_type": "blob", "target_hash": sha}
                        ]
                    },
                    "parents": [],
                    "author_id": "u1",
                    "ref": "main",
                },
            )
            commit_hash = r_commit.json()["hash"]

        # 直接构 DbRepoView
        engine = create_async_engine(_db_url() or "", pool_pre_ping=True)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        repo_row = None
        async with factory() as session:
            r = await session.execute(
                text("SELECT id FROM repositories WHERE owner=:o AND name=:n"),
                {"o": "test", "n": repo_name},
            )
            repo_row = r.first()
        assert repo_row is not None
        store = app.dependency_overrides[get_blob_store]()  # 拿 fixture override
        async with factory() as session:
            view = DbRepoView(session, store, repo_row[0], commit_hash)
            await view.load()
            paths = view.iter_paths()
            assert paths == ["hi.md"]
            # open 在 thread 跑（避免 asyncio.run 嵌套 event loop）
            import asyncio
            content = await asyncio.to_thread(lambda: view.open("hi.md").read())
            assert content == data
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (d) admin POST /process → 201 queued ---------


@pytest.mark.asyncio
async def test_d_admin_process_returns_queued(admin_user: dict) -> None:
    src = f"repo-pds-{uuid.uuid4().hex[:6]}"
    tgt = f"repo-pdt-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", src, "public")
            await _create_repo(c, "test", tgt, "public")
            r_blob = await c.post(f"/repos/test/{src}/blobs", content=b"hi\n")
            sha = r_blob.json()["sha256"]
            await c.post(
                f"/repos/test/{src}/commits",
                json={
                    "tree": {"entries": [{"name": "a.md", "mode": 33188, "entry_type": "blob", "target_hash": sha}]},
                    "parents": [],
                    "author_id": "u1",
                    "ref": "main",
                },
            )
            resp = await c.post(
                "/process",
                json={
                    "source_owner": "test",
                    "source_name": src,
                    "source_ref": "main",
                    "target_owner": "test",
                    "target_name": tgt,
                    "processor_name": "markdown-normalize",
                    "processor_version": "0.1",
                    "config": {},
                    "author_id": "u1",
                    "ref": "main",
                },
            )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "queued"
        assert body["type"] == "process"
    finally:
        await _delete_repo_cascade("test", src)
        await _delete_repo_cascade("test", tgt)


# --------- (e) user POST → 403 ---------


@pytest.mark.asyncio
async def test_e_user_process_returns_403(
    admin_user: dict, normal_user: dict
) -> None:
    src = f"repo-pes-{uuid.uuid4().hex[:6]}"
    tgt = f"repo-pet-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await _create_repo(a, "test", src, "public")
            await _create_repo(a, "test", tgt, "public")
        async with AsyncClient(transport=transport, base_url="https://test") as u:
            await _login(u, normal_user)
            r = await u.post(
                "/process",
                json={
                    "source_owner": "test", "source_name": src,
                    "target_owner": "test", "target_name": tgt,
                    "processor_name": "markdown-normalize", "processor_version": "0.1",
                    "config": {}, "author_id": "u1",
                },
            )
        assert r.status_code == 403
    finally:
        await _delete_repo_cascade("test", src)
        await _delete_repo_cascade("test", tgt)


# --------- (f) 端到端 process → worker → succeeded → 下游 commit ---------


@pytest.mark.asyncio
async def test_f_end_to_end_process_succeeded(admin_user: dict) -> None:
    src = f"repo-pfs-{uuid.uuid4().hex[:6]}"
    tgt = f"repo-pft-{uuid.uuid4().hex[:6]}"
    raw = b"hello\r\nworld   \r\n\r\n\r\n\r\nend\r\n"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", src, "public")
            await _create_repo(c, "test", tgt, "public")
            r_blob = await c.post(f"/repos/test/{src}/blobs", content=raw)
            sha = r_blob.json()["sha256"]
            r_commit = await c.post(
                f"/repos/test/{src}/commits",
                json={
                    "tree": {"entries": [{"name": "doc.md", "mode": 33188, "entry_type": "blob", "target_hash": sha}]},
                    "parents": [],
                    "author_id": "u1",
                    "ref": "main",
                },
            )
            assert r_commit.status_code == 200
            r_job = await c.post(
                "/process",
                json={
                    "source_owner": "test", "source_name": src,
                    "source_ref": "main",
                    "target_owner": "test", "target_name": tgt,
                    "processor_name": "markdown-normalize", "processor_version": "0.1",
                    "config": {}, "author_id": "u1",
                    "ref": "main",
                },
            )
            job_id = r_job.json()["id"]

        await _run_worker_burst()

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            r = await c.get(f"/jobs/{job_id}")
        body = r.json()
        assert body["status"] == "succeeded", body
        commit_hash = body["result"]["commit_hash"]
        assert len(commit_hash) == 64

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            r_get = await c.get(f"/repos/test/{tgt}/commits/{commit_hash}")
        commit = r_get.json()
        assert len(commit["tree"]["entries"]) == 1
        assert commit["tree"]["entries"][0]["name"] == "doc.md"
        # 下载 normalized 内容验证
        normalized_sha = commit["tree"]["entries"][0]["target_hash"]
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            r_blob = await c.get(f"/repos/test/{tgt}/blobs/{normalized_sha}")
        assert r_blob.status_code == 200
        # normalize: CRLF→LF, trailing ws 去, ≥3 空行 → 2 空行
        expected = b"hello\nworld\n\nend\n"
        assert r_blob.content == expected
    finally:
        await _delete_repo_cascade("test", src)
        await _delete_repo_cascade("test", tgt)


# --------- (g) unknown processor → worker mark_failed ---------


@pytest.mark.asyncio
async def test_g_unknown_processor_marks_failed(admin_user: dict) -> None:
    src = f"repo-pgs-{uuid.uuid4().hex[:6]}"
    tgt = f"repo-pgt-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", src, "public")
            await _create_repo(c, "test", tgt, "public")
            r_blob = await c.post(f"/repos/test/{src}/blobs", content=b"x\n")
            sha = r_blob.json()["sha256"]
            await c.post(
                f"/repos/test/{src}/commits",
                json={
                    "tree": {"entries": [{"name": "x.md", "mode": 33188, "entry_type": "blob", "target_hash": sha}]},
                    "parents": [], "author_id": "u", "ref": "main",
                },
            )
            r_job = await c.post(
                "/process",
                json={
                    "source_owner": "test", "source_name": src, "source_ref": "main",
                    "target_owner": "test", "target_name": tgt,
                    "processor_name": "no-such-processor", "processor_version": "9.9",
                    "config": {}, "author_id": "u",
                },
            )
            job_id = r_job.json()["id"]

        await _run_worker_burst()

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            r = await c.get(f"/jobs/{job_id}")
        body = r.json()
        assert body["status"] == "failed"
        assert body["error"]
    finally:
        await _delete_repo_cascade("test", src)
        await _delete_repo_cascade("test", tgt)


# --------- (h) source ref 不存在 → worker mark_failed ---------


@pytest.mark.asyncio
async def test_h_source_ref_missing_marks_failed(admin_user: dict) -> None:
    src = f"repo-phs-{uuid.uuid4().hex[:6]}"
    tgt = f"repo-pht-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", src, "public")
            await _create_repo(c, "test", tgt, "public")
            # 不建 commit / 不建 ref → main 不存在
            r_job = await c.post(
                "/process",
                json={
                    "source_owner": "test", "source_name": src,
                    "source_ref": "main",
                    "target_owner": "test", "target_name": tgt,
                    "processor_name": "markdown-normalize", "processor_version": "0.1",
                    "config": {}, "author_id": "u",
                },
            )
            job_id = r_job.json()["id"]

        await _run_worker_burst()

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            r = await c.get(f"/jobs/{job_id}")
        body = r.json()
        assert body["status"] == "failed"
    finally:
        await _delete_repo_cascade("test", src)
        await _delete_repo_cascade("test", tgt)
