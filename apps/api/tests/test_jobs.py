"""Jobs HTTP + RQ worker 集成测试（spec rq-worker-skeleton-20260517 AC-11）。

10 测试，三探针（PG + MinIO + Redis）任一不可达 → skip 全文件。
(g)(h)(i)(j) 用 RQ SimpleWorker burst 同进程跑 task 函数。
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
    reason="PG / MinIO / Redis 三探针未全通；jobs 集成测试跳过",
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
def _override_blob_store(monkeypatch) -> AsyncGenerator[None, None]:  # type: ignore[no-untyped-def]
    """FastAPI dep override + worker 全局 singleton 重置 + env 注入。

    Worker task 跑在同进程但调 get_blob_store() 单例（非 FastAPI Depends），
    所以必须 monkeypatch 模块级 _blob_store=None + env DATAPLAT_BLOB_BUCKET，
    让 worker 与 FastAPI 指向同 bucket。
    """
    bucket = f"dataplat-test-{uuid.uuid4().hex[:8]}"
    endpoint = os.environ.get("DATAPLAT_MINIO_ENDPOINT", "http://localhost:9000")
    ak = os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat")
    sk = os.environ.get("DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret")

    # 1. FastAPI handler 走 dependency_overrides → per-test store
    store = MinioBlobStore(endpoint_url=endpoint, access_key=ak, secret_key=sk, bucket=bucket)
    app.dependency_overrides[get_blob_store] = lambda: store

    # 2. Worker task 调 get_blob_store() 单例 → reset 并设 env，让 worker 新建到同 bucket
    import dataplat_api.storage as storage_mod

    monkeypatch.setattr(storage_mod, "_blob_store", None)
    monkeypatch.setenv("DATAPLAT_BLOB_BUCKET", bucket)
    monkeypatch.setenv("DATAPLAT_MINIO_ENDPOINT", endpoint)
    monkeypatch.setenv("DATAPLAT_MINIO_ACCESS_KEY", ak)
    monkeypatch.setenv("DATAPLAT_MINIO_SECRET_KEY", sk)
    try:
        yield  # type: ignore[misc]
    finally:
        # 重置 worker singleton 防污染下个测试
        storage_mod._blob_store = None
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
    """每测前清 default queue（避免跨测试任务残留）。"""
    try:
        queue = get_queue()
        queue.empty()
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


async def _run_worker_burst() -> None:
    """绕过 RQ Worker，直接 dequeue → 调用 task 函数；线程内跑（避免 asyncio.run 嵌套）。

    避免两个 RQ 限制：
    - SIGINT/SIGTERM 信号 handler 只能装在主线程
    - SIGALRM death penalty 同样限制
    直接 import + call task 函数避开上述。
    """
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
                # task 内部应自负 mark_failed；这里仅兜底
                pass

    await asyncio.to_thread(_work)


# --------- (a) admin POST /jobs/ingest → 201 status=queued ---------


@pytest.mark.asyncio
async def test_a_admin_enqueue_returns_queued(admin_user: dict) -> None:
    repo_name = f"repo-ja-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            sha = await _upload_blob(c, "test", repo_name, b"job a content")
            resp = await c.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "request": {
                        "adapter_name": "raw-file-upload",
                        "adapter_version": "0.1",
                        "spec": {"files": [{"path": "a.md", "sha256": sha}]},
                        "author_id": "u1",
                    },
                },
            )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "queued"
        assert body["type"] == "ingest"
        assert "id" in body
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (b) GET 已有 job ---------


@pytest.mark.asyncio
async def test_b_get_existing_job(admin_user: dict) -> None:
    repo_name = f"repo-jb-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            sha = await _upload_blob(c, "test", repo_name, b"b")
            r1 = await c.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "request": {
                        "adapter_name": "raw-file-upload",
                        "adapter_version": "0.1",
                        "spec": {"files": [{"path": "b", "sha256": sha}]},
                        "author_id": "u",
                    },
                },
            )
            job_id = r1.json()["id"]
            r2 = await c.get(f"/jobs/{job_id}")
        assert r2.status_code == 200
        assert r2.json()["id"] == job_id
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (c) GET 不存在 job → 404 ---------


@pytest.mark.asyncio
async def test_c_get_unknown_job_404(admin_user: dict) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as c:
        await _login(c, admin_user)
        r = await c.get(f"/jobs/{uuid.uuid4()}")
    assert r.status_code == 404


# --------- (d) user POST → 403 ---------


@pytest.mark.asyncio
async def test_d_user_post_returns_403(
    admin_user: dict, normal_user: dict
) -> None:
    repo_name = f"repo-jd-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await _create_repo(a, "test", repo_name, "public")
        async with AsyncClient(transport=transport, base_url="https://test") as u:
            await _login(u, normal_user)
            r = await u.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "request": {
                        "adapter_name": "raw-file-upload",
                        "adapter_version": "0.1",
                        "spec": {"files": [{"path": "x", "sha256": "a" * 64}]},
                        "author_id": "u",
                    },
                },
            )
        assert r.status_code == 403
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (e) anon POST → 401 ---------


@pytest.mark.asyncio
async def test_e_anon_post_returns_401(admin_user: dict) -> None:
    repo_name = f"repo-je-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin_user)
            await _create_repo(a, "test", repo_name, "public")
        async with AsyncClient(transport=transport, base_url="https://test") as anon:
            r = await anon.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "request": {
                        "adapter_name": "raw-file-upload",
                        "adapter_version": "0.1",
                        "spec": {"files": [{"path": "x", "sha256": "a" * 64}]},
                        "author_id": "u",
                    },
                },
            )
        assert r.status_code == 401
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (f) 缺 blob 入队成功 + worker 跑后 status=failed ---------


@pytest.mark.asyncio
async def test_f_missing_blob_marks_failed(admin_user: dict) -> None:
    repo_name = f"repo-jf-{uuid.uuid4().hex[:6]}"
    fake = "0" * 64
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r1 = await c.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "request": {
                        "adapter_name": "raw-file-upload",
                        "adapter_version": "0.1",
                        "spec": {"files": [{"path": "missing", "sha256": fake}]},
                        "author_id": "u",
                    },
                },
            )
            job_id = r1.json()["id"]

        # 注入 BlobStore env vars 让 worker import 时找得到（同进程；worker 用 get_blob_store
        # 全局，但 dependency_overrides 不传到 worker → worker 用真实 env 读 endpoint）
        # MVP：worker 也走相同 endpoint；以为 missing_hashes 校验在 AdapterRunner.run 早期失败
        await _run_worker_burst()

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            r2 = await c.get(f"/jobs/{job_id}")
        assert r2.status_code == 200
        body = r2.json()
        # missing blob 触发 400-equivalent 在 worker 内被 catch → status=failed
        assert body["status"] == "failed"
        assert body["error"] is not None
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (g) 端到端：上传 → POST job → SimpleWorker burst → status=succeeded ---------


@pytest.mark.asyncio
async def test_g_end_to_end_succeeded(admin_user: dict) -> None:
    repo_name = f"repo-jg-{uuid.uuid4().hex[:6]}"
    data = b"end to end ingest"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            sha = await _upload_blob(c, "test", repo_name, data)
            r1 = await c.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "request": {
                        "adapter_name": "raw-file-upload",
                        "adapter_version": "0.1",
                        "spec": {"files": [{"path": "g.md", "sha256": sha}]},
                        "author_id": "u",
                    },
                },
            )
            job_id = r1.json()["id"]

        await _run_worker_burst()

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            r2 = await c.get(f"/jobs/{job_id}")
        body = r2.json()
        assert body["status"] == "succeeded", body
        assert body["result"]["commit_hash"]
        assert len(body["result"]["commit_hash"]) == 64
        assert body["result"]["deduplicated"] is False
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (h) parent 自动接链：两次 ingest 同 ref → C2.parents=[C1] ---------


@pytest.mark.asyncio
async def test_h_parent_chain_through_ref(admin_user: dict) -> None:
    repo_name = f"repo-jh-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            sha1 = await _upload_blob(c, "test", repo_name, b"first job")
            r1 = await c.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "request": {
                        "adapter_name": "raw-file-upload",
                        "adapter_version": "0.1",
                        "spec": {"files": [{"path": "v1", "sha256": sha1}]},
                        "author_id": "u",
                        "ref": "main",
                    },
                },
            )
            job1_id = r1.json()["id"]

        await _run_worker_burst()

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            j1 = (await c.get(f"/jobs/{job1_id}")).json()
            c1_hash = j1["result"]["commit_hash"]
            sha2 = await _upload_blob(c, "test", repo_name, b"second job")
            r2 = await c.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "request": {
                        "adapter_name": "raw-file-upload",
                        "adapter_version": "0.1",
                        "spec": {"files": [{"path": "v2", "sha256": sha2}]},
                        "author_id": "u",
                        "ref": "main",
                    },
                },
            )
            job2_id = r2.json()["id"]

        await _run_worker_burst()

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            j2 = (await c.get(f"/jobs/{job2_id}")).json()
            c2_hash = j2["result"]["commit_hash"]
            assert c2_hash != c1_hash
            r_c2 = await c.get(f"/repos/test/{repo_name}/commits/{c2_hash}")
            commit2 = r_c2.json()
            assert commit2["parents"] == [c1_hash]
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (i) worker 异常 swallow → status=failed ---------


@pytest.mark.asyncio
async def test_i_worker_exception_marked_failed(admin_user: dict) -> None:
    """通过 unknown adapter 触发 worker 内异常路径。"""
    repo_name = f"repo-ji-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            r1 = await c.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo_name,
                    "request": {
                        "adapter_name": "no-such-adapter",
                        "adapter_version": "9.9",
                        "spec": {"files": [{"path": "x", "sha256": "a" * 64}]},
                        "author_id": "u",
                    },
                },
            )
            job_id = r1.json()["id"]

        await _run_worker_burst()

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            r2 = await c.get(f"/jobs/{job_id}")
        body = r2.json()
        assert body["status"] == "failed"
        assert body["error"] is not None
    finally:
        await _delete_repo_cascade("test", repo_name)


# --------- (j) 幂等：相同 spec 两次 enqueue → 第二次 result.deduplicated=true ---------


@pytest.mark.asyncio
async def test_j_idempotent_dedup_true(admin_user: dict) -> None:
    repo_name = f"repo-jj-{uuid.uuid4().hex[:6]}"
    data = b"idem job content"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            await _create_repo(c, "test", repo_name, "public")
            sha = await _upload_blob(c, "test", repo_name, data)
            payload = {
                "owner": "test",
                "name": repo_name,
                "request": {
                    "adapter_name": "raw-file-upload",
                    "adapter_version": "0.1",
                    "spec": {"files": [{"path": "j", "sha256": sha}]},
                    "author_id": "u",
                    "message": "idem",
                },
            }
            j1 = (await c.post("/jobs/ingest", json=payload)).json()["id"]
            j2 = (await c.post("/jobs/ingest", json=payload)).json()["id"]

        await _run_worker_burst()

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin_user)
            r1 = (await c.get(f"/jobs/{j1}")).json()
            r2 = (await c.get(f"/jobs/{j2}")).json()
        assert r1["status"] == "succeeded"
        assert r2["status"] == "succeeded"
        assert r1["result"]["commit_hash"] == r2["result"]["commit_hash"]
        # 第一个新建，第二个 dedup
        assert r1["result"]["deduplicated"] is False
        assert r2["result"]["deduplicated"] is True
    finally:
        await _delete_repo_cascade("test", repo_name)


