"""MarkdownNormalizeProcessor：上游 Bronze 文本 → 下游 Silver 规范化文本
（spec processor-framework-20260517 AC-4）。

规范化规则：
- CRLF → LF
- trailing whitespace 去掉
- 多于 2 个连续空行折叠为 2 个
- BOM 去掉

只处理 `.md` / `.txt` / `.markdown` 后缀的文件；其他文件**原封不动**复制到下游
（保证 sha256 不变 → CAS dedup）。
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

from dataplat_core.protocols.adapter import IngestFileRef
from dataplat_core.protocols.processor import (
    ProcessResult,
    RepoSelector,
    RepoSpec,
    RepoView,
)
from dataplat_core.protocols.runcontext import RunContext

_TEXT_SUFFIXES = (".md", ".txt", ".markdown")
_TRAILING_WS_RE = re.compile(r"[ \t]+(\n|$)")
_MULTI_BLANK_RE = re.compile(r"\n{3,}")


def _normalize(content: bytes) -> bytes:
    # 去 UTF-8 BOM
    if content.startswith(b"\xef\xbb\xbf"):
        content = content[3:]
    text = content.decode("utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _TRAILING_WS_RE.sub(r"\1", text)
    text = _MULTI_BLANK_RE.sub("\n\n", text)
    return text.encode("utf-8")


class MarkdownNormalizeProcessor:
    """无 state；纯函数处理器。"""

    name: str = "markdown-normalize"
    version: str = "0.1"
    config_schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {},
    }
    accepts: list[RepoSelector] = [RepoSelector()]  # 任意 layer
    produces: RepoSpec = RepoSpec(layer="silver", subtype="text-corpus")

    def run(
        self,
        inputs: list[RepoView],
        config: dict[str, Any],
        workspace: Path,
        ctx: RunContext,
    ) -> ProcessResult:
        del config, workspace  # 不使用
        if not inputs:
            raise ValueError("markdown-normalize 需至少 1 个上游 RepoView")
        view = inputs[0]
        blob_store = getattr(ctx, "blob_store", None)
        if blob_store is None:
            raise ValueError(
                "markdown-normalize 需 ctx.blob_store；当前 RunContext 未注入"
            )

        # view 必须暴露 iter_paths（DbRepoView 的扩展方法）
        paths = view.iter_paths()  # type: ignore[attr-defined]
        files: list[IngestFileRef] = []
        bytes_written = 0
        normalized_count = 0

        # processor 跑在 to_thread 线程；上传 blob 走 async；用 asyncio.run
        import asyncio

        async def _upload(content: bytes) -> tuple[str, int]:
            from io import BytesIO

            res = await blob_store.put(BytesIO(content), declared_size=len(content))
            return res.sha256, res.size

        for path in paths:
            stream = view.open(path)
            raw = stream.read() if hasattr(stream, "read") else b"".join(stream)
            if not isinstance(raw, bytes):
                raw = bytes(raw)
            if path.lower().endswith(_TEXT_SUFFIXES):
                normalized = _normalize(raw)
                if normalized != raw:
                    normalized_count += 1
                content = normalized
            else:
                content = raw
            sha, size = asyncio.run(_upload(content))
            files.append(IngestFileRef(path=path, sha256=sha))
            bytes_written += size

        return ProcessResult(
            record_count=0,
            file_count=len(files),
            bytes_written=bytes_written,
            notes=f"normalized {normalized_count}/{len(files)} text files",
            files=files,
        )


# convenience for callers
_ = io  # 抑制 unused
