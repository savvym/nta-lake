"""LLMQAGenProcessor 集成 + 单元测试（spec llm-qa-gen-20260518 AC-10）。

6 测试：
- (a) _parse_qa_response 直接 JSON
- (b) _parse_qa_response ```json``` 代码块
- (c) _parse_qa_response fallback raw
- (d) processor 单元（mock _SummaryLLM 返 JSON + _FakeStore + _FakeView）
- (e) admin POST /process llm-qa-gen → 201 queued
- (f) end-to-end：admin ingest 1 .md → /process llm-qa-gen → worker → succeeded；
  下游 commit 含 sft.jsonl 内容是合法 jsonl ≥ 1 行 + 每行含 prompt+response+meta
"""

from __future__ import annotations

import asyncio
import hashlib
import io as _io
import json
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import boto3
import pytest
import redis as redis_lib
from dataplat_api.auth.password import hash_password
from dataplat_api.jobs.redis_client import get_queue, get_redis
from dataplat_api.llm.factory import reset_llm_gateway
from dataplat_api.main import app
from dataplat_api.models import UserORM
from dataplat_api.processors.llm_qa_gen import (
    LLMQAGenProcessor,
    LLMQAGenSpec,
    _parse_qa_response,
)
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


# --------- (a)(b)(c) _parse_qa_response 单元 ---------


def test_a_parse_qa_direct_json() -> None:
    r = _parse_qa_response('{"prompt":"p","response":"r"}')
    assert r == {"prompt": "p", "response": "r"}


def test_b_parse_qa_code_block() -> None:
    raw = "Sure! Here is the QA:\n```json\n{\"prompt\":\"a\",\"response\":\"b\"}\n```\nDone."
    r = _parse_qa_response(raw)
    assert r == {"prompt": "a", "response": "b"}


def test_c_parse_qa_fallback_raw() -> None:
    r = _parse_qa_response("not a json at all just text")
    assert r["prompt"] == "Summarize the following text."
    assert "not a json" in r["response"]


# --------- (d) processor 单元（mock LLM + Store + View）---------


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


class _FakeView:
    def __init__(self, docs: dict[str, bytes]) -> None:
        self._docs = docs

    @property
    def repo_id(self) -> str:
        return "r1"

    @property
    def commit_hash(self) -> str:
        return "c" * 64

    def iter_paths(self) -> list[str]:
        return list(self._docs.keys())

    def open(self, path: str) -> Any:
        return _io.BytesIO(self._docs[path])

    def iter_records(self) -> Any:
        raise NotImplementedError


class _JsonLLM:
    """每次 call 返合法 QA JSON。"""

    def __init__(self) -> None:
        self.calls = 0

    async def call(self, req: Any) -> Any:
        from dataplat_core.protocols.llm import LLMResponse

        self.calls += 1
        return LLMResponse(
            text=f'{{"prompt": "q{self.calls}", "response": "a{self.calls}"}}',
            model_id=req.model_id,
            input_tokens=5,
            output_tokens=10,
        )


def test_d_processor_unit_with_fakes() -> None:
    llm = _JsonLLM()
    store = _FakeStore()
    view = _FakeView({"doc1.md": b"# Hello\n\nText A", "skip.bin": b"\x00\x01"})
    ctx = StandardRunContext(
        logger=logging.getLogger("test"), blob_store=store, llm=llm
    )
    p = LLMQAGenProcessor()
    result = asyncio.run(
        asyncio.to_thread(
            p.run,
            [view],
            {"records_per_doc": 2},
            __import__("pathlib").Path("/tmp"),
            ctx,
        )
    )
    # 1 个 .md × 2 records = 2 records
    assert result.record_count == 2
    assert result.file_count == 1
    assert result.files[0].path == "sft.jsonl"
    # _FakeStore.puts 中应有 1 个 blob = sft.jsonl
    assert len(store.puts) == 1
    lines = store.puts[0].decode("utf-8").strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        obj = json.loads(line)
        assert "prompt" in obj and "response" in obj and "meta" in obj
    # LLM 被调 2 次
    assert llm.calls == 2


# --------- 共享 fixtures (e)(f) ---------


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


# --------- (e) admin /process → 201 queued ---------


@pytest.mark.skipif(not _PG_MINIO_REDIS_OK, reason="PG/MinIO/Redis 任一未通")
@pytest.mark.asyncio
async def test_e_admin_process_returns_queued(
    monkeypatch: pytest.MonkeyPatch, _override_blob_store: None
) -> None:
    monkeypatch.setenv("DATAPLAT_LLM_PROVIDER", "fake")
    reset_llm_gateway()

    admin = await _make_user("admin")
    src = f"repo-qe-s-{uuid.uuid4().hex[:6]}"
    tgt = f"repo-qe-t-{uuid.uuid4().hex[:6]}"
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin)
            await _create_repo(c, "test", src)
            await _create_repo(c, "test", tgt)
            r_blob = await c.post(f"/repos/test/{src}/blobs", content=b"text body")
            sha = r_blob.json()["sha256"]
            r_commit = await c.post(
                f"/repos/test/{src}/commits",
                json={
                    "tree": {
                        "entries": [
                            {
                                "name": "a.md",
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
                    "processor_name": "llm-qa-gen",
                    "processor_version": "0.1",
                    "config": {"records_per_doc": 1},
                    "author_id": "u1",
                    "ref": "main",
                },
            )
        assert r_job.status_code == 201, r_job.text
        body = r_job.json()
        assert body["status"] == "queued"
    finally:
        await _delete_repo_cascade("test", src)
        await _delete_repo_cascade("test", tgt)
        await _delete_user(admin["id"])
        reset_llm_gateway()


# --------- (f) end-to-end → succeeded → sft.jsonl 内容验证 ---------


@pytest.mark.skipif(not _PG_MINIO_REDIS_OK, reason="PG/MinIO/Redis 任一未通")
@pytest.mark.asyncio
async def test_f_end_to_end_succeeded(
    monkeypatch: pytest.MonkeyPatch, _override_blob_store: None
) -> None:
    monkeypatch.setenv("DATAPLAT_LLM_PROVIDER", "fake")
    reset_llm_gateway()

    # 让 FakeLLMProvider.call 返合法 JSON
    from dataplat_core.protocols.llm import LLMResponse as _LR

    async def _fake_qa_call(self: Any, req: Any) -> Any:
        return _LR(
            text='{"prompt": "What is the capital of France?", "response": "Paris."}',
            model_id=req.model_id,
            input_tokens=10,
            output_tokens=10,
        )

    monkeypatch.setattr(
        "dataplat_api.llm.providers.fake.FakeLLMProvider.call", _fake_qa_call
    )

    admin = await _make_user("admin")
    src = f"repo-qf-s-{uuid.uuid4().hex[:6]}"
    tgt = f"repo-qf-t-{uuid.uuid4().hex[:6]}"
    raw = b"# Doc\n\nFrance is a country in Europe."
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
                    "processor_name": "llm-qa-gen",
                    "processor_version": "0.1",
                    "config": {"records_per_doc": 2, "max_tokens": 64},
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
        assert entries[0]["name"] == "sft.jsonl"
        sft_sha = entries[0]["target_hash"]
        async with AsyncClient(transport=transport, base_url="https://test") as c:
            await _login(c, admin)
            r_blob = await c.get(f"/repos/test/{tgt}/blobs/{sft_sha}")
        assert r_blob.status_code == 200
        lines = [
            line for line in r_blob.content.decode("utf-8").split("\n") if line.strip()
        ]
        # records_per_doc=2 × 1 上游 .md = 2 行
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)
            assert "prompt" in obj
            assert "response" in obj
            assert "meta" in obj
            meta = json.loads(obj["meta"])
            assert meta["source_path"] == "doc.md"
    finally:
        await _delete_repo_cascade("test", src)
        await _delete_repo_cascade("test", tgt)
        await _delete_user(admin["id"])
        reset_llm_gateway()


_ = LLMQAGenSpec  # 抑制 unused
