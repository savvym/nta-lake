"""PdfMineruProcessor：上游 Bronze PDF → 下游 Silver Markdown（via MinerU HTTP API）。

按 spec.md（processor-pdf-mineru-20260519 v2）。

约束：
- 严格串行（不并发多 PDF）
- env MINERU_API_URL 必需；缺失 → ValueError
- env MINERU_API_TOKEN 可选；存在则 X-API-Key: <token>（MinerU 3.1.x 鉴权）
- 输出文件名用 Path(path).with_suffix(".md")
- 非 .pdf 文件被跳过（不进产出 tree）
- 上游无 .pdf → ValueError
"""

from __future__ import annotations

import asyncio
import logging
import os
from io import BytesIO
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
from pydantic import BaseModel, ConfigDict

from dataplat_api.processors._mineru_client import MinerUClient

_logger = logging.getLogger("dataplat.processor.pdf_mineru")

_PDF_SUFFIXES = (".pdf",)
_ENV_URL = "MINERU_API_URL"
_ENV_TOKEN = "MINERU_API_TOKEN"


class PdfMineruSpec(BaseModel):
    """pdf-mineru processor config（落到 ProcessRequest.config）。"""

    model_config = ConfigDict(extra="forbid")

    parse_method: str = "auto"
    backend: str = "hybrid-auto-engine"
    poll_interval_seconds: float = 5.0
    poll_timeout_seconds: float = 600.0


_CONFIG_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "parse_method": {"type": "string"},
        "backend": {"type": "string"},
        "poll_interval_seconds": {"type": "number", "exclusiveMinimum": 0},
        "poll_timeout_seconds": {"type": "number", "exclusiveMinimum": 0},
    },
}


class PdfMineruProcessor:
    """无 state；调 MinerU HTTP API 把每个 PDF 转 markdown 并写 blob。"""

    name: str = "pdf-mineru"
    version: str = "0.1"
    config_schema: dict[str, Any] = _CONFIG_SCHEMA
    accepts: list[RepoSelector] = [RepoSelector()]
    produces: RepoSpec = RepoSpec(layer="silver", subtype="pdf-markdown")

    def run(
        self,
        inputs: list[RepoView],
        config: dict[str, Any],
        workspace: Path,
        ctx: RunContext,
    ) -> ProcessResult:
        del workspace
        if not inputs:
            raise ValueError("pdf-mineru 需至少 1 个上游 RepoView")
        blob_store = getattr(ctx, "blob_store", None)
        if blob_store is None:
            raise ValueError(
                "pdf-mineru 需 ctx.blob_store；当前 RunContext 未注入"
            )

        api_url = os.environ.get(_ENV_URL, "").strip()
        if not api_url:
            raise ValueError(
                f"pdf-mineru 需环境变量 {_ENV_URL}；当前未设置或为空"
            )
        api_token = os.environ.get(_ENV_TOKEN, "").strip() or None

        spec = PdfMineruSpec.model_validate(config or {})

        view = inputs[0]
        paths = list(view.iter_paths())  # type: ignore[attr-defined]
        pdf_paths = [p for p in paths if p.lower().endswith(_PDF_SUFFIXES)]
        if not pdf_paths:
            raise ValueError(
                f"pdf-mineru 在上游找不到 .pdf 文件（共 {len(paths)} 个）"
            )

        client = MinerUClient(base_url=api_url, token=api_token)

        async def _process_one(pdf_bytes: bytes, filename: str) -> tuple[str, int]:
            task_id = await client.submit(
                pdf_bytes, filename, spec.parse_method, spec.backend
            )
            md_text = await client.fetch_markdown(
                task_id,
                poll_interval=spec.poll_interval_seconds,
                poll_timeout=spec.poll_timeout_seconds,
            )
            md_bytes = md_text.encode("utf-8")
            res = await blob_store.put(
                BytesIO(md_bytes), declared_size=len(md_bytes)
            )
            return res.sha256, res.size

        files: list[IngestFileRef] = []
        bytes_written = 0
        for src_path in pdf_paths:
            stream = view.open(src_path)
            raw = stream.read() if hasattr(stream, "read") else b"".join(stream)
            if not isinstance(raw, bytes):
                raw = bytes(raw)
            filename = Path(src_path).name
            sha, size = asyncio.run(_process_one(raw, filename))
            out_path = str(Path(src_path).with_suffix(".md"))
            files.append(IngestFileRef(path=out_path, sha256=sha))
            bytes_written += size
            _logger.info(
                "pdf-mineru converted %s -> %s (%d bytes)", src_path, out_path, size
            )

        return ProcessResult(
            record_count=0,
            file_count=len(files),
            bytes_written=bytes_written,
            notes=f"pdf-mineru: {len(files)} PDF(s) → markdown via {api_url}",
            files=files,
        )
