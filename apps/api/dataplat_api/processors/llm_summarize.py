"""LLMSummarizeProcessor：上游 markdown / 文本 → 下游 summary blob。

设计目标：作为 LLM Gateway 端到端验证 processor。
- 找 source repo_view 中第一个 .md / .txt / .markdown 文件
- 用 `ctx.llm.call(LLMRequest(...))` 让 LLM 总结（max_tokens=256）
- 把 response.text 写成 `summary.md` blob 到下游 tree

不读多文件 / 不分块 / 不递归——这些都是后续 processor 的事；本处理器只
为验证 ctx.llm 注入链路通。
"""

from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path
from typing import Any

from dataplat_core.protocols.adapter import IngestFileRef
from dataplat_core.protocols.llm import LLMMessage, LLMRequest
from dataplat_core.protocols.processor import (
    ProcessResult,
    RepoSelector,
    RepoSpec,
    RepoView,
)
from dataplat_core.protocols.runcontext import RunContext

_TEXT_SUFFIXES = (".md", ".txt", ".markdown")
_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_DEFAULT_MAX_TOKENS = 256


class LLMSummarizeProcessor:
    """无 state；调 ctx.llm.call 完成单文件 summary。"""

    name: str = "llm-summarize"
    version: str = "0.1"
    config_schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "model_id": {"type": "string"},
            "max_tokens": {"type": "integer"},
        },
    }
    accepts: list[RepoSelector] = [RepoSelector()]
    produces: RepoSpec = RepoSpec(layer="gold", subtype="summary")

    def run(
        self,
        inputs: list[RepoView],
        config: dict[str, Any],
        workspace: Path,
        ctx: RunContext,
    ) -> ProcessResult:
        del workspace
        if not inputs:
            raise ValueError("llm-summarize 需至少 1 个上游 RepoView")
        llm = getattr(ctx, "llm", None)
        if llm is None:
            raise ValueError("llm-summarize 需 ctx.llm；当前 RunContext 未注入 gateway")
        blob_store = getattr(ctx, "blob_store", None)
        if blob_store is None:
            raise ValueError("llm-summarize 需 ctx.blob_store；当前 RunContext 未注入")

        view = inputs[0]
        paths = list(view.iter_paths())  # type: ignore[attr-defined]
        text_paths = [p for p in paths if p.lower().endswith(_TEXT_SUFFIXES)]
        if not text_paths:
            raise ValueError(
                f"llm-summarize 在上游找不到 .md/.txt/.markdown 文件（共 {len(paths)} 个）"
            )

        source_path = text_paths[0]
        stream = view.open(source_path)
        raw = stream.read() if hasattr(stream, "read") else b"".join(stream)
        if not isinstance(raw, bytes):
            raw = bytes(raw)
        text = raw.decode("utf-8", errors="replace")

        model_id = config.get("model_id", _DEFAULT_MODEL)
        max_tokens = int(config.get("max_tokens", _DEFAULT_MAX_TOKENS))
        req = LLMRequest(
            model_id=model_id,
            messages=[
                LLMMessage(
                    role="user",
                    content=f"Summarize concisely in 2-3 sentences:\n\n{text[:4000]}",
                )
            ],
            max_tokens=max_tokens,
        )

        async def _do() -> tuple[str, int]:
            resp = await llm.call(req)
            summary_bytes = resp.text.encode("utf-8")
            put = await blob_store.put(
                BytesIO(summary_bytes), declared_size=len(summary_bytes)
            )
            return put.sha256, put.size

        sha, size = asyncio.run(_do())
        return ProcessResult(
            record_count=0,
            file_count=1,
            bytes_written=size,
            notes=f"summarized {source_path} → summary.md ({size} bytes; model={model_id})",
            files=[IngestFileRef(path="summary.md", sha256=sha)],
        )
