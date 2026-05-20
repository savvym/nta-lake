"""W3-6 JsonlLoader behavioral tests."""

from __future__ import annotations

import gzip
from types import SimpleNamespace
from typing import Any

import pytest


class _StubBlobStore:
    """In-memory BlobStore stub: sha → bytes（async get 最小子集）。"""

    def __init__(self, data: dict[str, bytes]) -> None:
        self._data = dict(data)

    async def get(self, sha: str) -> bytes:
        return self._data[sha]


def _make_ctx(blob_store: Any | None) -> Any:
    return SimpleNamespace(
        blob_store=blob_store,
        logger=None,
        metrics=None,
        secrets=None,
        cancel_event=None,
        llm=None,
    )


def test_jsonl_auto_registered() -> None:
    """AC-1: import 后 LoaderRegistry 含 "jsonl"。"""
    from dataplat_core.loaders import JsonlLoader, LoaderRegistry

    assert "jsonl" in LoaderRegistry.list_names()
    assert LoaderRegistry.get("jsonl") is JsonlLoader


def test_jsonl_load_plain_happy() -> None:
    """AC-2: jsonl 明文 happy path。

    blob 内容：
      line 1: {"text": "hello"}      ← 有效
      line 2: (空行)                   ← 跳过，不计入任何计数
      line 3: {"text": "world"}      ← 有效
      line 4: not a json line        ← 坏 json，error_count++
      line 5: {"foo": "bar"}         ← 缺 text 字段，error_count++
      line 6: {"text": "third"}      ← 有效

    期望：total_count=3, notes 含 "line_count=3, error_count=2"
          rows[i].text 依次 "hello" / "world" / "third"
          stats.format == "jsonl"
          source_ref.line_no 是 1-based 原行号（1 / 3 / 6）
    """
    from dataplat_core.loaders import JsonlLoader

    sha = "a" * 64
    jsonl_text = (
        '{"text": "hello"}\n'
        "\n"
        '{"text": "world"}\n'
        "not a json line\n"
        '{"foo": "bar"}\n'
        '{"text": "third"}\n'
    )
    ctx = _make_ctx(_StubBlobStore({sha: jsonl_text.encode("utf-8")}))

    loader = JsonlLoader()
    result = loader.load(sha, {}, ctx)

    assert result.total_count == 3
    assert len(result.rows) == 3
    assert result.notes is not None
    assert "line_count=3" in result.notes
    assert "error_count=2" in result.notes

    texts = [r.text for r in result.rows]
    assert texts == ["hello", "world", "third"]

    for row in result.rows:
        assert row.stats["format"] == "jsonl"
        assert "char_count" in row.stats
        assert row.images == []
        assert row.lineage_ops == []
        assert row.source_ref["blob_sha"] == sha
        assert row.source_ref["loader"] == "jsonl"
        assert row.source_ref["loader_version"] == "0.1"

    # source_ref.line_no は 1-based 原行号
    line_nos = [r.source_ref["line_no"] for r in result.rows]
    assert line_nos == [1, 3, 6]


def test_jsonl_load_gz_happy() -> None:
    """AC-3: jsonl.gz happy path。

    gzip.compress(b'{"text":"a"}\\n{"text":"b"}\\n') → blob
    load with config={"format":"jsonl.gz"} → total_count=2, stats.format=="jsonl.gz"
    """
    from dataplat_core.loaders import JsonlLoader

    sha = "c" * 64
    raw = b'{"text":"a"}\n{"text":"b"}\n'
    gz_data = gzip.compress(raw)
    ctx = _make_ctx(_StubBlobStore({sha: gz_data}))

    loader = JsonlLoader()
    result = loader.load(sha, {"format": "jsonl.gz"}, ctx)

    assert result.total_count == 2
    assert len(result.rows) == 2
    assert result.rows[0].text == "a"
    assert result.rows[1].text == "b"
    for row in result.rows:
        assert row.stats["format"] == "jsonl.gz"


def test_jsonl_requires_blob_store() -> None:
    """AC-4: ctx.blob_store 缺失 → raise ValueError 含 "ctx.blob_store"。"""
    from dataplat_core.loaders import JsonlLoader

    loader = JsonlLoader()
    ctx = _make_ctx(None)

    with pytest.raises(ValueError, match="ctx.blob_store"):
        loader.load("a" * 64, {}, ctx)
