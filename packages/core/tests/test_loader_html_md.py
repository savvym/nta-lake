"""W3-4 HtmlMdLoader behavioral tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest


class _StubBlobStore:
    """In-memory BlobStore stub: sha → bytes."""

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


def test_html_md_auto_registered() -> None:
    """AC-1: import 后 LoaderRegistry 含 html-md。"""
    from dataplat_core.loaders import HtmlMdLoader, LoaderRegistry

    assert "html-md" in LoaderRegistry.list_names()
    assert LoaderRegistry.get("html-md") is HtmlMdLoader


def test_html_md_load_markdown_happy() -> None:
    """AC-2: md 内容 → 1 row + 正确 stats。"""
    from dataplat_core.loaders import HtmlMdLoader

    sha = "a" * 64
    md_text = "# Title\n\n## Sub\n\ntext ![alt](img.png)"
    ctx = _make_ctx(_StubBlobStore({sha: md_text.encode("utf-8")}))

    loader = HtmlMdLoader()
    result = loader.load(sha, {}, ctx)

    assert result.total_count == 1
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.stats["format"] == "md"
    assert row.stats["heading_count"] == 2
    assert row.stats["image_ref_count"] == 1
    assert row.stats["char_count"] == len(md_text)
    assert row.source_ref["blob_sha"] == sha
    assert row.source_ref["loader"] == "html-md"
    assert row.images == []
    assert row.text == md_text


def test_html_md_load_html_happy() -> None:
    """AC-3: html 内容 + config['format']='html' → 正确 stats。"""
    from dataplat_core.loaders import HtmlMdLoader

    sha = "b" * 64
    html_text = "<h1>X</h1><h2>Y</h2><img src=\"a.png\">"
    ctx = _make_ctx(_StubBlobStore({sha: html_text.encode("utf-8")}))

    loader = HtmlMdLoader()
    result = loader.load(sha, {"format": "html"}, ctx)

    assert result.total_count == 1
    row = result.rows[0]
    assert row.stats["format"] == "html"
    assert row.stats["heading_count"] == 2
    assert row.stats["image_ref_count"] == 1
    assert row.images == []


def test_html_md_requires_blob_store() -> None:
    """AC-4: ctx.blob_store 缺失 → ValueError 含 'ctx.blob_store'。"""
    from dataplat_core.loaders import HtmlMdLoader

    ctx = _make_ctx(None)
    loader = HtmlMdLoader()

    with pytest.raises(ValueError, match="ctx.blob_store"):
        loader.load("a" * 64, {}, ctx)
