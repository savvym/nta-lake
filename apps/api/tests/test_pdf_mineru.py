"""PdfMineruProcessor + MinerUClient 单元测试（spec processor-pdf-mineru-20260519 AC-9/10/12）。

测试是纯 unit：FakeRepoView + FakeBlobStore + monkeypatch httpx；不依赖 pg / minio / redis。

7 测试：
- test_run_success: 1 PDF 上游 → 产出 1 个 <name>.md blob（含 sha + bytes）
- test_run_poll_failed_raises: poll status=failed → ValueError
- test_run_env_missing_url: unset MINERU_API_URL → ValueError
- test_client_token_header_present: set TOKEN → submit/poll 收到 Authorization: Bearer
- test_client_token_header_absent: unset TOKEN → 无 Authorization header
- test_run_skips_non_pdf: 上游 .txt + .pdf → 仅 1 个 .md，非 PDF 不进 tree
- test_run_poll_timeout: poll 永远 running + 小 timeout → ValueError
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import logging
import types
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx as real_httpx
import pytest
from dataplat_api.processors._mineru_client import MinerUClient
from dataplat_api.processors.pdf_mineru import PdfMineruProcessor
from dataplat_api.runner.runcontext import StandardRunContext
from dataplat_core.protocols.storage import BlobPutResult

# --------- Fakes ---------


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload: Any = None) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self) -> Any:
        return self._payload


class _FakeAsyncClient:
    """按 method+url 路由到预设响应。

    routes:
      submit (POST /tasks)   → submit_response，默认 status_code=202, payload={"task_id":"task-xyz"}
      poll   (GET /tasks/{id})→ poll_sequence 依次取（用完保持最后一个）
      result (GET /tasks/{id}/result) → result_response，默认 200 + {"markdown":"# Hello\\n"}
    submit_calls / poll_calls / result_calls 记录每次请求的 headers，
    便于断言 X-API-Key（MinerU 3.1.x 鉴权方式）。
    """

    submit_response: _FakeResponse = _FakeResponse()
    poll_sequence: list[_FakeResponse] = []
    result_response: _FakeResponse = _FakeResponse()
    submit_calls: list[dict[str, Any]] = []
    poll_calls: list[dict[str, Any]] = []
    result_calls: list[dict[str, Any]] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs

    async def __aenter__(self) -> _FakeAsyncClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None

    async def post(
        self,
        url: str,
        files: Any = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> _FakeResponse:
        type(self).submit_calls.append(
            {"url": url, "files": files, "data": data, "headers": dict(headers or {})}
        )
        return type(self).submit_response

    async def get(
        self, url: str, headers: dict[str, str] | None = None
    ) -> _FakeResponse:
        if url.endswith("/result"):
            type(self).result_calls.append(
                {"url": url, "headers": dict(headers or {})}
            )
            return type(self).result_response
        type(self).poll_calls.append(
            {"url": url, "headers": dict(headers or {})}
        )
        seq = type(self).poll_sequence
        if not seq:
            return _FakeResponse(status_code=200, payload={"status": "running"})
        if len(seq) == 1:
            return seq[0]
        return seq.pop(0)


def _reset_fake() -> None:
    _FakeAsyncClient.submit_response = _FakeResponse(
        status_code=202, payload={"task_id": "task-xyz"}
    )
    _FakeAsyncClient.poll_sequence = [
        _FakeResponse(payload={"status": "succeeded"})
    ]
    _FakeAsyncClient.result_response = _FakeResponse(
        payload={"markdown": "# Hello\n"}
    )
    _FakeAsyncClient.submit_calls = []
    _FakeAsyncClient.poll_calls = []
    _FakeAsyncClient.result_calls = []


def _fake_httpx() -> Any:
    return types.SimpleNamespace(
        AsyncClient=_FakeAsyncClient,
        Timeout=real_httpx.Timeout,
    )


def _patch_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "dataplat_api.processors._mineru_client.httpx", _fake_httpx()
    )


class _FakeRepoView:
    def __init__(self, files: dict[str, bytes]) -> None:
        self._files = files

    @property
    def repo_id(self) -> str:
        return "fake-repo"

    @property
    def commit_hash(self) -> str:
        return "fake-commit"

    def iter_paths(self) -> list[str]:
        return list(self._files.keys())

    def open(self, path: str) -> io.BytesIO:
        return io.BytesIO(self._files[path])

    def iter_records(self) -> Any:
        raise NotImplementedError


class _FakeBlobStore:
    def __init__(self) -> None:
        self.puts: list[bytes] = []

    async def put(
        self, stream: Any, declared_size: int | None = None
    ) -> BlobPutResult:
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


def _make_ctx() -> StandardRunContext:
    return StandardRunContext(
        logger=logging.getLogger("test.pdf_mineru"),
        blob_store=_FakeBlobStore(),
    )


# --------- Tests ---------


def test_run_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_fake()
    monkeypatch.setenv("MINERU_API_URL", "http://mineru.test")
    monkeypatch.delenv("MINERU_API_TOKEN", raising=False)
    _patch_httpx(monkeypatch)

    view = _FakeRepoView({"sample.pdf": b"%PDF-1.4 fake bytes"})
    ctx = _make_ctx()
    proc = PdfMineruProcessor()
    result = proc.run([view], {}, Path("/tmp"), ctx)

    assert result.file_count == 1
    assert result.files[0].path == "sample.md"
    blob_store = ctx.blob_store
    assert isinstance(blob_store, _FakeBlobStore)
    assert blob_store.puts == [b"# Hello\n"]
    assert result.bytes_written == len(b"# Hello\n")
    # submit + poll + result 都被调过
    assert len(_FakeAsyncClient.submit_calls) == 1
    assert _FakeAsyncClient.submit_calls[0]["url"] == "http://mineru.test/tasks"
    # MinerU v3 multipart 字段名为 files（数组），非 file 单数
    submit_files = _FakeAsyncClient.submit_calls[0]["files"]
    assert isinstance(submit_files, list)
    assert submit_files[0][0] == "files"
    # submit 也透传 backend 字段
    assert _FakeAsyncClient.submit_calls[0]["data"]["backend"] == "hybrid-auto-engine"
    assert len(_FakeAsyncClient.poll_calls) == 1
    assert len(_FakeAsyncClient.result_calls) == 1
    assert _FakeAsyncClient.result_calls[0]["url"].endswith("/tasks/task-xyz/result")


def test_run_poll_failed_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_fake()
    _FakeAsyncClient.poll_sequence = [
        _FakeResponse(payload={"status": "failed", "error": "ocr crashed"})
    ]
    monkeypatch.setenv("MINERU_API_URL", "http://mineru.test")
    _patch_httpx(monkeypatch)

    view = _FakeRepoView({"bad.pdf": b"%PDF-1.4 bad"})
    ctx = _make_ctx()
    proc = PdfMineruProcessor()
    with pytest.raises(ValueError, match="failed"):
        proc.run([view], {}, Path("/tmp"), ctx)


def test_run_env_missing_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_fake()
    monkeypatch.delenv("MINERU_API_URL", raising=False)
    monkeypatch.delenv("MINERU_API_TOKEN", raising=False)

    view = _FakeRepoView({"sample.pdf": b"%PDF-1.4"})
    ctx = _make_ctx()
    proc = PdfMineruProcessor()
    with pytest.raises(ValueError, match="MINERU_API_URL"):
        proc.run([view], {}, Path("/tmp"), ctx)


def test_client_token_header_present(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_fake()
    _patch_httpx(monkeypatch)

    client = MinerUClient(base_url="http://mineru.test", token="secret-key")
    task_id = asyncio.run(client.submit(b"%PDF-1.4", "x.pdf", "auto"))
    assert task_id == "task-xyz"
    submit_call = _FakeAsyncClient.submit_calls[0]
    # MinerU 3.1.x 用 X-API-Key 头，非 Authorization Bearer
    assert submit_call["headers"].get("X-API-Key") == "secret-key"
    assert "Authorization" not in submit_call["headers"]

    asyncio.run(client.poll(task_id))
    poll_call = _FakeAsyncClient.poll_calls[0]
    assert poll_call["headers"].get("X-API-Key") == "secret-key"

    asyncio.run(client.fetch_result(task_id))
    result_call = _FakeAsyncClient.result_calls[0]
    assert result_call["headers"].get("X-API-Key") == "secret-key"


def test_client_token_header_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_fake()
    _patch_httpx(monkeypatch)

    client = MinerUClient(base_url="http://mineru.test", token=None)
    asyncio.run(client.submit(b"%PDF-1.4", "x.pdf", "auto"))
    submit_call = _FakeAsyncClient.submit_calls[0]
    assert "X-API-Key" not in submit_call["headers"]
    assert "Authorization" not in submit_call["headers"]

    asyncio.run(client.poll("task-xyz"))
    poll_call = _FakeAsyncClient.poll_calls[0]
    assert "X-API-Key" not in poll_call["headers"]


def test_run_skips_non_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_fake()
    monkeypatch.setenv("MINERU_API_URL", "http://mineru.test")
    _patch_httpx(monkeypatch)

    view = _FakeRepoView(
        {
            "notes.txt": b"plain text",
            "doc.pdf": b"%PDF-1.4",
            "readme.md": b"# already md",
        }
    )
    ctx = _make_ctx()
    proc = PdfMineruProcessor()
    result = proc.run([view], {}, Path("/tmp"), ctx)

    # 只有 1 个 PDF 被处理；非 PDF 文件不进产出 tree
    assert result.file_count == 1
    assert result.files[0].path == "doc.md"
    paths = [f.path for f in result.files]
    assert "notes.txt" not in paths
    assert "readme.md" not in paths


def test_run_poll_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_fake()
    # poll 永远返 running → MinerUClient.fetch_markdown 触发超时
    _FakeAsyncClient.poll_sequence = [
        _FakeResponse(payload={"status": "running"})
    ]
    monkeypatch.setenv("MINERU_API_URL", "http://mineru.test")
    _patch_httpx(monkeypatch)

    view = _FakeRepoView({"slow.pdf": b"%PDF-1.4"})
    ctx = _make_ctx()
    proc = PdfMineruProcessor()
    # 用极短 poll_timeout + interval 让超时立即触发
    config = {"poll_interval_seconds": 0.01, "poll_timeout_seconds": 0.05}
    with pytest.raises(ValueError, match="轮询超时"):
        proc.run([view], config, Path("/tmp"), ctx)


# 防止 unused import 警告（io.BytesIO 在 _FakeRepoView.open 用到）
_ = BytesIO
