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
import time
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

from dataplat_api.processors._mineru_client import (
    _TERMINAL_FAIL,
    _TERMINAL_OK,
    MinerUClient,
)

_logger = logging.getLogger("dataplat.processor.pdf_mineru")

_PDF_SUFFIXES = (".pdf",)
_ENV_URL = "MINERU_API_URL"
_ENV_TOKEN = "MINERU_API_TOKEN"


async def _wait_terminal(
    client: MinerUClient,
    task_id: str,
    poll_interval: float,
    poll_timeout: float,
) -> str:
    """轮询直到终态；返 status 字符串。failed → ValueError；超时 → ValueError。"""
    deadline = time.monotonic() + poll_timeout
    while True:
        data = await client.poll(task_id)
        status_raw = data.get("status") or data.get("state") or ""
        status = status_raw.lower() if isinstance(status_raw, str) else ""
        if status in _TERMINAL_OK:
            return status
        if status in _TERMINAL_FAIL:
            err = data.get("error") or data.get("message") or "(no error message)"
            raise ValueError(f"MinerU task {task_id} failed: {err}")
        if time.monotonic() >= deadline:
            raise ValueError(
                f"MinerU task {task_id} 轮询超时：> {poll_timeout}s"
            )
        _logger.debug(
            "MinerU task %s status=%s, sleeping %.1fs",
            task_id,
            status,
            poll_interval,
        )
        await asyncio.sleep(poll_interval)


class PdfMineruSpec(BaseModel):
    """pdf-mineru processor config（落到 ProcessRequest.config）。"""

    model_config = ConfigDict(extra="forbid")

    parse_method: str = "auto"
    backend: str = "hybrid-auto-engine"
    return_images: bool = True
    return_content_list: bool = True
    poll_interval_seconds: float = 5.0
    poll_timeout_seconds: float = 600.0


_CONFIG_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "parse_method": {"type": "string"},
        "backend": {"type": "string"},
        "return_images": {"type": "boolean"},
        "return_content_list": {"type": "boolean"},
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

        async def _process_one(
            pdf_bytes: bytes, filename: str, src_path: str
        ) -> tuple[list[IngestFileRef], int]:
            task_id = await client.submit(
                pdf_bytes,
                filename,
                parse_method=spec.parse_method,
                backend=spec.backend,
                return_images=spec.return_images,
                return_content_list=spec.return_content_list,
            )
            # poll 到终态，然后取完整结果（含 images / content_list）
            deadline_status = await _wait_terminal(
                client, task_id, spec.poll_interval_seconds, spec.poll_timeout_seconds
            )
            del deadline_status  # 仅用于副作用：等到 succeeded 再 fetch_full_result
            full = await client.fetch_full_result(task_id)

            refs: list[IngestFileRef] = []
            total_bytes = 0

            # 1) <basename>.md
            md_bytes = full["markdown"].encode("utf-8")
            md_res = await blob_store.put(
                BytesIO(md_bytes), declared_size=len(md_bytes)
            )
            md_path = str(Path(src_path).with_suffix(".md"))
            refs.append(IngestFileRef(path=md_path, sha256=md_res.sha256))
            total_bytes += md_res.size

            # 2) images/<filename>（MinerU 已用 sha-named filename；CAS 天然 dedup）
            images = full.get("images") or {}
            for img_filename, img_bytes in images.items():
                img_res = await blob_store.put(
                    BytesIO(img_bytes), declared_size=len(img_bytes)
                )
                refs.append(
                    IngestFileRef(
                        path=f"images/{img_filename}", sha256=img_res.sha256
                    )
                )
                total_bytes += img_res.size

            # 3) <basename>.content_list.json（如有）
            content_list = full.get("content_list")
            if isinstance(content_list, str) and content_list:
                cl_bytes = content_list.encode("utf-8")
                cl_res = await blob_store.put(
                    BytesIO(cl_bytes), declared_size=len(cl_bytes)
                )
                stem = Path(src_path).stem
                parent = str(Path(src_path).parent)
                cl_path = (
                    f"{parent}/{stem}.content_list.json"
                    if parent and parent != "."
                    else f"{stem}.content_list.json"
                )
                refs.append(IngestFileRef(path=cl_path, sha256=cl_res.sha256))
                total_bytes += cl_res.size

            return refs, total_bytes

        files: list[IngestFileRef] = []
        bytes_written = 0
        for src_path in pdf_paths:
            stream = view.open(src_path)
            raw = stream.read() if hasattr(stream, "read") else b"".join(stream)
            if not isinstance(raw, bytes):
                raw = bytes(raw)
            filename = Path(src_path).name
            refs, sub_bytes = asyncio.run(_process_one(raw, filename, src_path))
            files.extend(refs)
            bytes_written += sub_bytes
            _logger.info(
                "pdf-mineru converted %s -> %d artifacts (%d bytes)",
                src_path,
                len(refs),
                sub_bytes,
            )

        return ProcessResult(
            record_count=0,
            file_count=len(files),
            bytes_written=bytes_written,
            notes=f"pdf-mineru: {len(files)} PDF(s) → markdown via {api_url}",
            files=files,
        )
