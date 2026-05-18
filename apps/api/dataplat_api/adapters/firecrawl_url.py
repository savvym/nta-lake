"""FirecrawlURLAdapter：抓 URL → ctx.llm 转 markdown → blob 写。

按 design.md §2.3 / §4.1 / §11.6。MVP 不引入 firecrawl-py SDK；用 httpx
拉 HTML + 调 ctx.llm.call 让 LLM 转 markdown，再可选地提取 markdown 中的
image URL 下载，输出 `assets/<idx>/content.md` + `assets/<idx>/images/<sha[:16]>{ext}`。

约束（spec）：
- urls 必须 http(s)://（spec.field_validator 校验）
- 多 URL 串行（spec AC-7 反向 grep 拦并发原语；并发由 follow-up 解决）
- image 下载失败"吞掉不阻塞"（单图 GET 异常 → log warn + 跳过 → 不影响其他图与 content.md）
"""

from __future__ import annotations

import asyncio
import logging
import mimetypes
import os
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
from dataplat_core.protocols.adapter import IngestFileRef, IngestResult
from dataplat_core.protocols.llm import LLMMessage, LLMRequest
from dataplat_core.protocols.runcontext import RunContext
from pydantic import BaseModel, ConfigDict, field_validator

from dataplat_api.adapters._image_extract import extract_image_urls

_logger = logging.getLogger("dataplat.adapter.firecrawl")

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_DEFAULT_MAX_TOKENS = 1024
_DEFAULT_TIMEOUT = 30.0
_HTML_TRUNCATE = 8000
_USER_AGENT = os.environ.get(
    "DATAPLAT_FIRECRAWL_USER_AGENT", "dataplat-firecrawl/0.1"
)


class FirecrawlURLSpec(BaseModel):
    """firecrawl-url adapter spec。"""

    model_config = ConfigDict(extra="forbid")

    urls: list[str]
    extract_images: bool = True
    llm_model: str = _DEFAULT_MODEL
    max_tokens: int = _DEFAULT_MAX_TOKENS
    request_timeout_seconds: float = _DEFAULT_TIMEOUT

    @field_validator("urls")
    @classmethod
    def _validate_urls(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("urls 不能为空")
        for url in value:
            if not isinstance(url, str) or not url.lower().startswith(
                ("http://", "https://")
            ):
                raise ValueError(f"urls 中每条必须以 http:// 或 https:// 起头: {url!r}")
        return value


_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "urls": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "pattern": "^https?://"},
        },
        "extract_images": {"type": "boolean"},
        "llm_model": {"type": "string"},
        "max_tokens": {"type": "integer", "minimum": 1},
        "request_timeout_seconds": {"type": "number", "exclusiveMinimum": 0},
    },
    "required": ["urls"],
    "additionalProperties": False,
}


def _guess_ext(url: str, content_type: str) -> str:
    """从 URL 后缀或 Content-Type 推断扩展名，找不到回 ''."""
    suffix = Path(url.split("?", 1)[0]).suffix
    if suffix and len(suffix) <= 5:
        return suffix.lower()
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
        if guessed:
            return guessed
    return ""


class FirecrawlURLAdapter:
    """httpx + ctx.llm + ctx.blob_store 组合。"""

    name: str = "firecrawl-url"
    version: str = "0.1"
    input_schema: dict[str, Any] = _INPUT_SCHEMA
    output_subtype: str = "webpage-collection"

    def ingest(
        self,
        spec: dict[str, Any],
        workspace: Path | None,
        ctx: RunContext | None,
    ) -> IngestResult:
        del workspace  # 不写文件，blob 直接走 ctx.blob_store
        try:
            parsed = FirecrawlURLSpec.model_validate(spec)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"FirecrawlURLSpec 非法：{exc}") from exc

        if ctx is None:
            raise ValueError("firecrawl-url 需 RunContext；当前为 None")
        llm = getattr(ctx, "llm", None)
        if llm is None:
            raise ValueError("firecrawl-url 需 ctx.llm；AdapterRunner 未注入 gateway")
        blob_store = getattr(ctx, "blob_store", None)
        if blob_store is None:
            raise ValueError(
                "firecrawl-url 需 ctx.blob_store；AdapterRunner 未注入 store"
            )

        files, bytes_written = asyncio.run(_run_all(parsed, llm, blob_store))
        return IngestResult(
            file_count=len(files),
            bytes_written=bytes_written,
            notes=f"firecrawl-url: {len(parsed.urls)} urls, {len(files)} blobs",
            files=files,
        )


async def _run_all(
    parsed: FirecrawlURLSpec, llm: Any, blob_store: Any
) -> tuple[list[IngestFileRef], int]:
    files: list[IngestFileRef] = []
    bytes_written = 0
    timeout = httpx.Timeout(parsed.request_timeout_seconds)
    headers = {"User-Agent": _USER_AGENT}
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        for idx, url in enumerate(parsed.urls):
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

            llm_resp = await llm.call(
                LLMRequest(
                    model_id=parsed.llm_model,
                    messages=[
                        LLMMessage(
                            role="user",
                            content=(
                                "Convert this HTML to clean Markdown. Keep links "
                                "and image references. Output only the Markdown.\n\n"
                                f"{html[:_HTML_TRUNCATE]}"
                            ),
                        )
                    ],
                    max_tokens=parsed.max_tokens,
                )
            )
            md_bytes = llm_resp.text.encode("utf-8")
            content_put = await blob_store.put(
                BytesIO(md_bytes), declared_size=len(md_bytes)
            )
            files.append(
                IngestFileRef(
                    path=f"assets/{idx}/content.md", sha256=content_put.sha256
                )
            )
            bytes_written += content_put.size

            if not parsed.extract_images:
                continue

            image_urls = extract_image_urls(llm_resp.text, url)
            for img_url in image_urls:
                try:
                    img_resp = await client.get(img_url)
                    img_resp.raise_for_status()
                except Exception as exc:  # noqa: BLE001
                    _logger.warning(
                        "firecrawl-url: image GET 失败 url=%s err=%s; 跳过",
                        img_url,
                        exc,
                    )
                    continue
                img_bytes = img_resp.content
                img_put = await blob_store.put(
                    BytesIO(img_bytes), declared_size=len(img_bytes)
                )
                ext = _guess_ext(img_url, img_resp.headers.get("content-type", ""))
                files.append(
                    IngestFileRef(
                        path=f"assets/{idx}/images/{img_put.sha256[:16]}{ext}",
                        sha256=img_put.sha256,
                    )
                )
                bytes_written += img_put.size
    return files, bytes_written
