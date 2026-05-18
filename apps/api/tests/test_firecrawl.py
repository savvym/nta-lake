"""FirecrawlURLAdapter 集成 + 单元测试（spec adapter-firecrawl-20260517 AC-10）。

6 测试：
- (a) extract_image_urls 单元
- (b) adapter.ingest 单元（mock httpx + FakeLLMProvider + FakeStore）
- (c) admin POST /repos/{}/{}/ingest 返 201 queued
- (d) user POST → 403
- (e) 端到端：admin POST → worker → succeeded；下游 commit 含 assets/0/content.md + ≥1 image
- (f) unreachable URL → worker mark_failed
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import types
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import boto3
import httpx as real_httpx
import pytest
import redis as redis_lib
from dataplat_api.adapters._image_extract import extract_image_urls
from dataplat_api.adapters.firecrawl_url import FirecrawlURLAdapter, FirecrawlURLSpec
from dataplat_api.auth.password import hash_password
from dataplat_api.jobs.redis_client import get_queue, get_redis
from dataplat_api.llm.factory import reset_llm_gateway
from dataplat_api.llm.providers.fake import FakeLLMProvider
from dataplat_api.main import app
from dataplat_api.models import UserORM
from dataplat_api.runner.runcontext import StandardRunContext
from dataplat_api.storage import get_blob_store
from dataplat_api.storage.minio_store import MinioBlobStore
from dataplat_core.protocols.storage import BlobPutResult
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


_PG_MINIO_REDIS_OK = bool(_db_url() and _minio_endpoint() and _redis_reachable())


# --------- Fake httpx ---------


class _FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        text: str = "",
        content: bytes = b"",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.text = text
        self.content = content
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise real_httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=None,  # type: ignore[arg-type]
                response=None,  # type: ignore[arg-type]
            )


class _FakeAsyncClient:
    """按 URL 路由到预设响应；未匹配 → 404；可被参数化抛 ConnectError。"""

    routes: dict[str, _FakeResponse] = {}
    raise_for: set[str] = set()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs  # 接受任何参数

    async def __aenter__(self) -> _FakeAsyncClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None

    async def get(self, url: str) -> _FakeResponse:
        if url in self.raise_for:
            raise real_httpx.ConnectError("fake unreachable")
        if url not in self.routes:
            return _FakeResponse(status_code=404, text="not found")
        return self.routes[url]


def _make_fake_httpx() -> Any:
    """构造 module-level fake，保留 real Timeout / 异常类。"""
    return types.SimpleNamespace(
        AsyncClient=_FakeAsyncClient,
        Timeout=real_httpx.Timeout,
        HTTPStatusError=real_httpx.HTTPStatusError,
        ConnectError=real_httpx.ConnectError,
    )


# --------- (a) extract_image_urls 单元 ---------


def test_a_extract_image_urls_unit() -> None:
    md = (
        "hi <img src=\"https://x.com/a.png\">\n"
        "![alt](/img/b.jpg)\n"
        "![c](https://y.com/c.gif)\n"
        "<img src=\"data:image/png;base64,xxx\">\n"
        "![dup](https://x.com/a.png)\n"  # 去重
        "<img src=\"  \">"  # 空 src 跳过
    )
    urls = extract_image_urls(md, "https://example.com/page")
    # 按文档出现顺序：HTML a.png（第 1 行）→ md /img/b.jpg（第 2 行）→ md c.gif（第 3 行）
    assert urls == [
        "https://x.com/a.png",
        "https://example.com/img/b.jpg",
        "https://y.com/c.gif",
    ]


# --------- (b) adapter.ingest 单元 ---------


class _FakeStore:
    def __init__(self) -> None:
        self.puts: list[bytes] = []

    async def put(self, stream: Any, declared_size: int | None = None) -> BlobPutResult:
        del declared_size
        data = stream.read()
        self.puts.append(data)
        sha = hashlib.sha256(data).hexdigest()
        return BlobPutResult(
            sha256=sha,
            size=len(data),
            storage_key=f"blobs/{sha[:2]}/{sha}",
            deduplicated=False,
        )


def test_b_adapter_ingest_unit_with_fakes(monkeypatch: pytest.MonkeyPatch) -> None:
    # markdown response 含 1 个 image URL
    md_text = (
        "# Page\nhello\n"
        "![banner](https://imgs.example.com/banner.png)\n"
    )
    _FakeAsyncClient.routes = {
        "https://example.com/page": _FakeResponse(text="<html><body>X</body></html>"),
        "https://imgs.example.com/banner.png": _FakeResponse(
            content=b"\x89PNG-fake-bytes", headers={"content-type": "image/png"}
        ),
    }
    _FakeAsyncClient.raise_for = set()

    # LLM 返 md_text（按 fake provider 默认是 "FAKE[model]: ..."；这里要拦截让它返 md_text）
    class _SummaryLLM:
        async def call(self, req: Any) -> Any:
            from dataplat_core.protocols.llm import LLMResponse

            return LLMResponse(
                text=md_text,
                model_id=req.model_id,
                input_tokens=10,
                output_tokens=10,
            )

    monkeypatch.setattr(
        "dataplat_api.adapters.firecrawl_url.httpx", _make_fake_httpx()
    )

    store = _FakeStore()
    ctx = StandardRunContext(
        logger=logging.getLogger("test"), blob_store=store, llm=_SummaryLLM()
    )
    adapter = FirecrawlURLAdapter()
    result = adapter.ingest(
        {"urls": ["https://example.com/page"], "extract_images": True}, None, ctx
    )
    paths = [f.path for f in result.files]
    assert "assets/0/content.md" in paths
    assert any(p.startswith("assets/0/images/") for p in paths)
    assert any(p.endswith(".png") for p in paths)
    # blob_store 至少有 content.md + banner.png 两次 put
    assert len(store.puts) >= 2


# --------- 共享 fixtures (c)~(f) ---------


@pytest.fixture
def _override_blob_store(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[None, None]:
    bucket = f"dataplat-test-{uuid.uuid4().hex[:8]}"
    endpoint = os.environ.get("DATAPLAT_MINIO_ENDPOINT", "http://localhost:9000")
    ak = os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat")
    sk = os.environ.get("DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret")
    store = MinioBlobStore(
        endpoint_url=endpoint, access_key=ak, secret_key=sk, bucket=bucket
    )
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
        return {
            "id": user.id,
            "username": username,
            "password": password,
            "role": role,
        }


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
        await session.execute(
            text("DELETE FROM commits WHERE repo_id=:r"), {"r": repo_id}
        )
        await session.execute(text("DELETE FROM trees WHERE repo_id=:r"), {"r": repo_id})
        await session.execute(
            text("DELETE FROM repositories WHERE id=:r"), {"r": repo_id}
        )
        await session.commit()


async def _login(client: AsyncClient, user: dict) -> None:
    resp = await client.post(
        "/auth/login",
        json={"username": user["username"], "password": user["password"]},
    )
    assert resp.status_code == 200


async def _create_repo(client: AsyncClient, owner: str, name: str) -> None:
    resp = await client.post(
        "/repos",
        json={
            "owner": owner,
            "name": name,
            "layer": "bronze",
            "subtype": "webpage",
            "visibility": "public",
        },
    )
    assert resp.status_code == 201, resp.text


async def _run_worker_burst() -> None:
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


# --------- (c) admin /ingest 返 201 queued ---------


@pytest.mark.skipif(not _PG_MINIO_REDIS_OK, reason="PG/MinIO/Redis 任一未通")
@pytest.mark.asyncio
async def test_c_admin_ingest_returns_queued(
    monkeypatch: pytest.MonkeyPatch, _override_blob_store: None
) -> None:
    monkeypatch.setenv("DATAPLAT_LLM_PROVIDER", "fake")
    reset_llm_gateway()
    monkeypatch.setattr(
        "dataplat_api.adapters.firecrawl_url.httpx", _make_fake_httpx()
    )
    _FakeAsyncClient.routes = {"https://example.com/p1": _FakeResponse(text="<p>x</p>")}
    _FakeAsyncClient.raise_for = set()

    admin = await _make_user("admin")
    repo = f"repo-fc-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin)
            await _create_repo(c, "test", repo)
            resp = await c.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo,
                    "request": {
                        "adapter_name": "firecrawl-url",
                        "adapter_version": "0.1",
                        "spec": {
                            "urls": ["https://example.com/p1"],
                            "extract_images": False,
                        },
                        "author_id": "u1",
                        "message": "ingest 1",
                        "ref": "main",
                    },
                },
            )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "queued"
    finally:
        await _delete_repo_cascade("test", repo)
        await _delete_user(admin["id"])
        reset_llm_gateway()


# --------- (d) user → 403 ---------


@pytest.mark.skipif(not _PG_MINIO_REDIS_OK, reason="PG/MinIO/Redis 任一未通")
@pytest.mark.asyncio
async def test_d_user_ingest_returns_403(
    monkeypatch: pytest.MonkeyPatch, _override_blob_store: None
) -> None:
    monkeypatch.setenv("DATAPLAT_LLM_PROVIDER", "fake")
    reset_llm_gateway()

    admin = await _make_user("admin")
    normal = await _make_user("user")
    repo = f"repo-fd-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as a:
            await _login(a, admin)
            await _create_repo(a, "test", repo)
        async with AsyncClient(transport=transport, base_url="https://test") as u:
            await _login(u, normal)
            r = await u.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo,
                    "request": {
                        "adapter_name": "firecrawl-url",
                        "adapter_version": "0.1",
                        "spec": {"urls": ["https://example.com/p1"]},
                        "author_id": "u",
                    },
                },
            )
        assert r.status_code == 403
    finally:
        await _delete_repo_cascade("test", repo)
        await _delete_user(normal["id"])
        await _delete_user(admin["id"])
        reset_llm_gateway()


# --------- (e) end-to-end → succeeded ---------


@pytest.mark.skipif(not _PG_MINIO_REDIS_OK, reason="PG/MinIO/Redis 任一未通")
@pytest.mark.asyncio
async def test_e_end_to_end_succeeded(
    monkeypatch: pytest.MonkeyPatch, _override_blob_store: None
) -> None:
    # 让 LLM 返回的 markdown 中包含 1 个 image URL；fake provider 默认 FAKE[...] 不含 image
    # 用真 fake provider，但我们把 markdown 的 image URL 通过 prompt 传进去 → fake 输出复述 prompt
    # fake 模板：FAKE[model]: <first user content[:80]>
    # 若 prompt 含 https://imgs/x.png 我们 fake 输出会含 prompt 子串 → extract_image_urls 命中
    monkeypatch.setenv("DATAPLAT_LLM_PROVIDER", "fake")
    reset_llm_gateway()
    monkeypatch.setattr(
        "dataplat_api.adapters.firecrawl_url.httpx", _make_fake_httpx()
    )
    # 让 FakeLLMProvider.call 返回固定的 markdown 含 image URL（默认模板会被 prompt
    # 前缀截断，提取不到 URL）
    from dataplat_core.protocols.llm import LLMResponse as _LR

    async def _fake_md_call(self: Any, req: Any) -> Any:
        return _LR(
            text="![pic](https://imgs.test/x.png)\n\nbody",
            model_id=req.model_id,
            input_tokens=10,
            output_tokens=10,
        )

    monkeypatch.setattr(
        "dataplat_api.llm.providers.fake.FakeLLMProvider.call", _fake_md_call
    )

    _FakeAsyncClient.routes = {
        "https://example.test/page": _FakeResponse(text="<html><body>X</body></html>"),
        "https://imgs.test/x.png": _FakeResponse(
            content=b"\x89PNG-fake", headers={"content-type": "image/png"}
        ),
    }
    _FakeAsyncClient.raise_for = set()

    admin = await _make_user("admin")
    repo = f"repo-fe-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin)
            await _create_repo(c, "test", repo)
            r_job = await c.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo,
                    "request": {
                        "adapter_name": "firecrawl-url",
                        "adapter_version": "0.1",
                        "spec": {
                            "urls": ["https://example.test/page"],
                            "extract_images": True,
                            "max_tokens": 200,
                        },
                        "author_id": "u1",
                        "message": "firecrawl e2e",
                        "ref": "main",
                    },
                },
            )
            assert r_job.status_code == 201, r_job.text
            job_id = r_job.json()["id"]

        await _run_worker_burst()

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin)
            r = await c.get(f"/jobs/{job_id}")
        body = r.json()
        assert body["status"] == "succeeded", body
        commit_hash = body["result"]["commit_hash"]

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin)
            r_get = await c.get(f"/repos/test/{repo}/commits/{commit_hash}")
        commit = r_get.json()
        paths = [e["name"] for e in commit["tree"]["entries"]]
        assert "assets/0/content.md" in paths
        # monkeypatched fake → markdown 含 https://imgs.test/x.png → extract → 下载 → tree entry
        assert any(p.startswith("assets/0/images/") for p in paths)
    finally:
        await _delete_repo_cascade("test", repo)
        await _delete_user(admin["id"])
        reset_llm_gateway()


# --------- (f) unreachable URL → mark_failed ---------


@pytest.mark.skipif(not _PG_MINIO_REDIS_OK, reason="PG/MinIO/Redis 任一未通")
@pytest.mark.asyncio
async def test_f_unreachable_url_marks_failed(
    monkeypatch: pytest.MonkeyPatch, _override_blob_store: None
) -> None:
    monkeypatch.setenv("DATAPLAT_LLM_PROVIDER", "fake")
    reset_llm_gateway()
    monkeypatch.setattr(
        "dataplat_api.adapters.firecrawl_url.httpx", _make_fake_httpx()
    )
    bad_url = "https://unreachable.test/x"
    _FakeAsyncClient.routes = {}
    _FakeAsyncClient.raise_for = {bad_url}

    admin = await _make_user("admin")
    repo = f"repo-ff-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin)
            await _create_repo(c, "test", repo)
            r_job = await c.post(
                "/jobs/ingest",
                json={
                    "owner": "test",
                    "name": repo,
                    "request": {
                        "adapter_name": "firecrawl-url",
                        "adapter_version": "0.1",
                        "spec": {"urls": [bad_url], "extract_images": False},
                        "author_id": "u1",
                        "ref": "main",
                    },
                },
            )
            assert r_job.status_code == 201, r_job.text
            job_id = r_job.json()["id"]

        await _run_worker_burst()

        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin)
            r = await c.get(f"/jobs/{job_id}")
        body = r.json()
        assert body["status"] == "failed", body
        assert body.get("error")
    finally:
        await _delete_repo_cascade("test", repo)
        await _delete_user(admin["id"])
        reset_llm_gateway()


# 抑制 unused（FakeLLMProvider 在 import 链路注册需要保留 import）
_ = FakeLLMProvider
_ = FirecrawlURLSpec
