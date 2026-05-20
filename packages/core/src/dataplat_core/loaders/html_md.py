"""HtmlMdLoader：Bronze HTML/MD blob → SilverRow。

stats:
  - format: "md" / "html"
  - heading_count: int
  - char_count: int
  - image_ref_count: int

图片仅占位（不抓 blob_store）；images=[]。
"""

from __future__ import annotations

import asyncio
import re
from html.parser import HTMLParser
from typing import Any

from dataplat_core.domain.types import SHA256
from dataplat_core.protocols.loader import LoadResult, SilverRow
from dataplat_core.protocols.runcontext import RunContext

_MD_HEADING_RE = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)
_MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")


class _HtmlStatsParser(HTMLParser):
    """html.parser 子类：统计 h1..h6 / img 标签数。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.heading_count = 0
        self.image_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_count += 1
        elif tag == "img":
            self.image_count += 1

    # html.parser 对 self-closing 也需要重写
    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


class HtmlMdLoader:
    """Bronze HTML/MD blob → SilverRow loader。"""

    name: str = "html-md"
    version: str = "0.1"
    input_subtype: str = "html-md"
    output_schema_id: str = "silver-text-v1"

    def load(
        self,
        bronze_blob_sha: SHA256,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> LoadResult:
        blob_store = getattr(ctx, "blob_store", None)
        if blob_store is None:
            raise ValueError(
                "loader html-md 需 ctx.blob_store；当前 RunContext 未注入"
            )

        cfg = config or {}
        format_hint: str | None = cfg.get("format")
        path_hint: str | None = cfg.get("path")

        async def _run() -> LoadResult:
            data = await blob_store.get(bronze_blob_sha)
            if not isinstance(data, bytes):
                chunks = []
                async for chunk in data:
                    chunks.append(chunk)
                data = b"".join(chunks)

            text = data.decode("utf-8", errors="replace")

            fmt = format_hint
            if fmt not in {"md", "html"}:
                if path_hint:
                    p = path_hint.lower()
                    if p.endswith((".html", ".htm")):
                        fmt = "html"
                    elif p.endswith((".md", ".markdown")):
                        fmt = "md"
                if fmt not in {"md", "html"}:
                    fmt = "md"  # 默认

            if fmt == "md":
                heading_count = len(_MD_HEADING_RE.findall(text))
                image_ref_count = len(_MD_IMAGE_RE.findall(text))
            else:
                parser = _HtmlStatsParser()
                parser.feed(text)
                heading_count = parser.heading_count
                image_ref_count = parser.image_count

            row = SilverRow(
                text=text,
                images=[],
                source_ref={
                    "blob_sha": bronze_blob_sha,
                    "loader": "html-md",
                    "loader_version": "0.1",
                },
                stats={
                    "format": fmt,
                    "heading_count": heading_count,
                    "char_count": len(text),
                    "image_ref_count": image_ref_count,
                },
                lineage_ops=[],
            )

            return LoadResult(
                rows=[row],
                total_count=1,
                notes=f"format={fmt}",
            )

        return asyncio.run(_run())
