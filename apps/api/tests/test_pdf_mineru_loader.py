"""PdfMineruLoader 行为测试 (W1-4 AC-2, AC-3)."""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch


_FAKE_SHA = "a" * 64
_FAKE_MARKDOWN = "# Hello\n\nThis is fake markdown content."
_FAKE_IMAGE_1 = ("img1.png", b"fake-img-bytes-1")
_FAKE_IMAGE_2 = ("img2.png", b"fake-img-bytes-2")


def _make_fake_blob_store() -> Any:
    """构造 in-memory fake blob_store，提供 async get / async put。"""
    _blobs: dict[str, bytes] = {
        _FAKE_SHA: b"fake pdf bytes",
    }
    _put_counter = [0]

    class FakePutResult:
        def __init__(self, sha256: str, size: int) -> None:
            self.sha256 = sha256
            self.size = size

    class FakeBlobStore:
        async def get(self, sha: str) -> bytes:
            return _blobs[sha]

        async def put(self, stream: Any, declared_size: int) -> FakePutResult:
            _put_counter[0] += 1
            # 生成确定性 sha（用序号区分）
            fake_sha = f"{_put_counter[0]:064x}"
            data = stream.read()
            _blobs[fake_sha] = data
            return FakePutResult(sha256=fake_sha, size=len(data))

    return FakeBlobStore()


def _make_fake_ctx(blob_store: Any) -> Any:
    ctx = SimpleNamespace()
    ctx.blob_store = blob_store
    return ctx


def test_load_returns_single_silver_row(monkeypatch: Any) -> None:
    """AC-2: mock MinerUClient → load() 返 1 个 SilverRow，字段语义正确。"""
    monkeypatch.setenv("MINERU_API_URL", "http://fake-mineru.local")

    fake_blob_store = _make_fake_blob_store()
    fake_ctx = _make_fake_ctx(fake_blob_store)

    fake_full_result: dict[str, Any] = {
        "markdown": _FAKE_MARKDOWN,
        "images": {
            _FAKE_IMAGE_1[0]: _FAKE_IMAGE_1[1],
            _FAKE_IMAGE_2[0]: _FAKE_IMAGE_2[1],
        },
        "content_list": None,
    }

    # patch MinerUClient.submit → 返 fake task_id
    # patch _wait_terminal → 立即返 "succeeded"（绕过 poll 循环）
    # patch MinerUClient.fetch_full_result → 返 fake_full_result
    with (
        patch(
            "dataplat_api.loaders.pdf_mineru.MinerUClient.submit",
            new_callable=AsyncMock,
            return_value="fake-task-id-001",
        ),
        patch(
            "dataplat_api.loaders.pdf_mineru._wait_terminal",
            new_callable=AsyncMock,
            return_value="succeeded",
        ),
        patch(
            "dataplat_api.loaders.pdf_mineru.MinerUClient.fetch_full_result",
            new_callable=AsyncMock,
            return_value=fake_full_result,
        ),
    ):
        from dataplat_api.loaders.pdf_mineru import PdfMineruLoader

        loader = PdfMineruLoader()
        result = loader.load(
            bronze_blob_sha=_FAKE_SHA,
            config={},
            ctx=fake_ctx,
        )

    # 结构断言
    assert result.total_count == 1
    assert len(result.rows) == 1

    row = result.rows[0]

    # text
    assert row.text == _FAKE_MARKDOWN

    # images：2 项，每项有 blob_sha + filename
    assert len(row.images) == 2
    for img_item in row.images:
        assert "blob_sha" in img_item
        assert "filename" in img_item
        assert len(img_item["blob_sha"]) == 64  # sha256 hex

    # source_ref
    assert row.source_ref["loader"] == "pdf-mineru"
    assert row.source_ref["blob_sha"] == _FAKE_SHA
    assert row.source_ref["loader_version"] == "0.1"

    # stats
    assert row.stats["text_chars"] == len(_FAKE_MARKDOWN)
    assert row.stats["image_count"] == 2

    # lineage_ops 为空（Loader 不追加 lineage_ops）
    assert row.lineage_ops == []


def test_load_missing_env_raises(monkeypatch: Any) -> None:
    """AC-3: 缺 MINERU_API_URL env → ValueError 含 'MINERU_API_URL' 字样。"""
    monkeypatch.delenv("MINERU_API_URL", raising=False)

    fake_blob_store = _make_fake_blob_store()
    fake_ctx = _make_fake_ctx(fake_blob_store)

    import pytest
    from dataplat_api.loaders.pdf_mineru import PdfMineruLoader

    loader = PdfMineruLoader()
    with pytest.raises(ValueError, match="MINERU_API_URL"):
        loader.load(
            bronze_blob_sha=_FAKE_SHA,
            config={},
            ctx=fake_ctx,
        )
