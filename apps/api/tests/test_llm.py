"""LLM Gateway 集成 + 单元测试（spec llm-gateway-mvp-20260517 AC-10）。

6 测试：
- (a) FakeLLMProvider deterministic
- (b) RedisLLMCache get/set 往返
- (c) LLMGateway cache hit 跳过 provider
- (d) LLMGateway retry 3 次后成功
- (e) factory 单例 + 默认 fake
- (f) LLMSummarizeProcessor 端到端（admin POST /process → worker → succeeded）
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator

import boto3
import pytest
import redis as redis_lib
from dataplat_api.auth.password import hash_password
from dataplat_api.jobs.redis_client import get_queue, get_redis
from dataplat_api.llm.cache import RedisLLMCache
from dataplat_api.llm.factory import get_llm_gateway, reset_llm_gateway
from dataplat_api.llm.gateway import LLMGateway
from dataplat_api.llm.providers.fake import FakeLLMProvider
from dataplat_api.main import app
from dataplat_api.models import UserORM
from dataplat_api.storage import get_blob_store
from dataplat_api.storage.minio_store import MinioBlobStore
from dataplat_core.protocols.llm import LLMMessage, LLMRequest, LLMResponse
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


# --------- (a) FakeLLMProvider deterministic（纯单元，无 fixture）---------


def test_a_fake_provider_deterministic() -> None:
    p = FakeLLMProvider()
    req = LLMRequest(
        model_id="x",
        messages=[LLMMessage(role="user", content="hi")],
        max_tokens=16,
    )
    a = asyncio.run(p.call(req))
    b = asyncio.run(p.call(req))
    assert a.text == b.text
    assert a.text.startswith("FAKE[x]:")
    assert a.text.endswith("hi")
    assert a.model_id == "x"


# --------- (b) RedisLLMCache get/set 往返 ---------


@pytest.mark.skipif(not _redis_reachable(), reason="Redis 未通")
def test_b_redis_cache_get_set_roundtrip() -> None:
    redis_client = redis_lib.Redis.from_url(_redis_url())
    cache = RedisLLMCache(redis_client, ttl_seconds=60)
    req = LLMRequest(
        model_id=f"m-{uuid.uuid4().hex[:6]}",
        messages=[LLMMessage(role="user", content="hello world")],
        max_tokens=32,
        temperature=0.5,
        seed=42,
    )
    resp = LLMResponse(
        text="cached response", model_id=req.model_id, input_tokens=2, output_tokens=2
    )
    # 初次 miss
    assert asyncio.run(cache.get(req)) is None
    # set 后命中
    asyncio.run(cache.set(req, resp))
    got = asyncio.run(cache.get(req))
    assert got is not None
    assert got.text == "cached response"
    assert got.model_id == req.model_id
    # 不同 req 不命中
    other = req.model_copy(update={"seed": 99})
    assert asyncio.run(cache.get(other)) is None


# --------- (c) LLMGateway cache hit 跳过 provider ---------


@pytest.mark.skipif(not _redis_reachable(), reason="Redis 未通")
def test_c_gateway_cache_hit_skips_provider() -> None:
    class _SpyProvider:
        def __init__(self) -> None:
            self.calls = 0

        async def call(self, req: LLMRequest) -> LLMResponse:
            self.calls += 1
            return LLMResponse(
                text=f"hi-{self.calls}",
                model_id=req.model_id,
                input_tokens=1,
                output_tokens=1,
            )

    provider = _SpyProvider()
    redis_client = redis_lib.Redis.from_url(_redis_url())
    cache = RedisLLMCache(redis_client, ttl_seconds=60)
    gw = LLMGateway(provider=provider, cache=cache, max_retries=0)
    req = LLMRequest(
        model_id=f"gw-{uuid.uuid4().hex[:6]}",
        messages=[LLMMessage(role="user", content="ping")],
        max_tokens=16,
    )
    r1 = asyncio.run(gw.call(req))
    r2 = asyncio.run(gw.call(req))
    assert provider.calls == 1, "第二次 call 应命中缓存，不走 provider"
    assert r1.text == r2.text == "hi-1"


# --------- (d) LLMGateway retry 3 次后成功 ---------


def test_d_gateway_retry_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FlakyProvider:
        def __init__(self) -> None:
            self.attempts = 0

        async def call(self, req: LLMRequest) -> LLMResponse:
            self.attempts += 1
            if self.attempts <= 3:
                raise RuntimeError(f"transient {self.attempts}")
            return LLMResponse(
                text="ok-after-retry",
                model_id=req.model_id,
                input_tokens=1,
                output_tokens=1,
            )

    async def _no_sleep(_secs: float) -> None:
        return None

    monkeypatch.setattr("dataplat_api.llm.gateway.asyncio.sleep", _no_sleep)

    provider = _FlakyProvider()
    gw = LLMGateway(provider=provider, cache=None, max_retries=3, base_delay=0.0)
    req = LLMRequest(
        model_id="retry",
        messages=[LLMMessage(role="user", content="please")],
        max_tokens=4,
    )
    resp = asyncio.run(gw.call(req))
    assert resp.text == "ok-after-retry"
    assert provider.attempts == 4


# --------- (e) factory 单例 + 默认 fake ---------


def test_e_factory_singleton_and_default_fake(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATAPLAT_LLM_PROVIDER", raising=False)
    reset_llm_gateway()
    g1 = get_llm_gateway()
    g2 = get_llm_gateway()
    assert g1 is g2
    # 内部 provider 应为 fake
    assert isinstance(g1._provider, FakeLLMProvider)  # noqa: SLF001
    reset_llm_gateway()


# --------- (f) end-to-end LLMSummarizeProcessor via /process → worker ---------


_PG_MINIO_REDIS_OK = bool(_db_url() and _minio_endpoint() and _redis_reachable())


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
            "subtype": "pdf",
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


@pytest.mark.skipif(not _PG_MINIO_REDIS_OK, reason="PG/MinIO/Redis 任一未通")
@pytest.mark.asyncio
async def test_f_llm_summarize_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
    _override_blob_store: None,
) -> None:
    """强制 DATAPLAT_LLM_PROVIDER=fake；ingest 1 个 .md → /process llm-summarize
    → worker → succeeded；下游 commit 含 summary.md，内容以 'FAKE[' 起头。"""
    monkeypatch.setenv("DATAPLAT_LLM_PROVIDER", "fake")
    reset_llm_gateway()

    admin = await _make_user("admin")
    src = f"repo-ls-{uuid.uuid4().hex[:6]}"
    tgt = f"repo-lt-{uuid.uuid4().hex[:6]}"
    raw = b"# Hello\n\nThis is a long text to summarize. " * 5
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin)
            await _create_repo(c, "test", src)
            await _create_repo(c, "test", tgt)
            r_blob = await c.post(f"/repos/test/{src}/blobs", content=raw)
            sha = r_blob.json()["sha256"]
            r_commit = await c.post(
                f"/repos/test/{src}/commits",
                json={
                    "tree": {
                        "entries": [
                            {
                                "name": "doc.md",
                                "mode": 33188,
                                "entry_type": "blob",
                                "target_hash": sha,
                            }
                        ]
                    },
                    "parents": [],
                    "author_id": "u1",
                    "ref": "main",
                },
            )
            assert r_commit.status_code == 200
            r_job = await c.post(
                "/process",
                json={
                    "source_owner": "test",
                    "source_name": src,
                    "source_ref": "main",
                    "target_owner": "test",
                    "target_name": tgt,
                    "processor_name": "llm-summarize",
                    "processor_version": "0.1",
                    "config": {"model_id": "claude-haiku-4-5-20251001", "max_tokens": 64},
                    "author_id": "u1",
                    "ref": "main",
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
            r_get = await c.get(f"/repos/test/{tgt}/commits/{commit_hash}")
        commit = r_get.json()
        entries = commit["tree"]["entries"]
        assert len(entries) == 1
        assert entries[0]["name"] == "summary.md"
        summary_sha = entries[0]["target_hash"]
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin)
            r_blob = await c.get(f"/repos/test/{tgt}/blobs/{summary_sha}")
        assert r_blob.status_code == 200
        assert r_blob.content.startswith(b"FAKE[claude-haiku-4-5-20251001]:")
    finally:
        await _delete_repo_cascade("test", src)
        await _delete_repo_cascade("test", tgt)
        await _delete_user(admin["id"])
        reset_llm_gateway()
