"""PdfMineruLoader：Bronze PDF blob → SilverRow（via MinerU HTTP API）。

实现 Loader Protocol（W1-2），输出 list[SilverRow]。
与老 PdfMineruProcessor 共存；old Processor 保留不撤（见 design.md 决策 1）。

约束：
- env MINERU_API_URL 必需；缺失 → ValueError（含 "MINERU_API_URL" 字样）
- env MINERU_API_TOKEN 可选；存在则 X-API-Key: <token>
- ctx.blob_store 必须注入；否则 ValueError
- 一个 PDF blob → 一个 SilverRow（不按页拆分；批处理由 caller 多次调 load）
"""

from __future__ import annotations

import asyncio
import os
from io import BytesIO
from typing import Any

from dataplat_core.domain.types import SHA256
from dataplat_core.protocols.loader import LoadResult, SilverRow
from dataplat_core.protocols.runcontext import RunContext

from dataplat_api.processors._mineru_client import MinerUClient
from dataplat_api.processors.pdf_mineru import PdfMineruSpec, _wait_terminal

_ENV_URL = "MINERU_API_URL"
_ENV_TOKEN = "MINERU_API_TOKEN"


class PdfMineruLoader:
    """无 state；调 MinerU HTTP API 把 PDF blob 转为 SilverRow。"""

    name: str = "pdf-mineru"
    version: str = "0.1"
    input_subtype: str = "pdf"
    output_schema_id: str = "silver-text-v1"

    def load(
        self,
        bronze_blob_sha: SHA256,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> LoadResult:
        """从 bronze blob sha 读 PDF bytes，调 MinerU，返 1 个 SilverRow。

        Args:
            bronze_blob_sha: CAS sha256（64 hex）。
            config:          PdfMineruSpec 可接受的 dict（空 dict 使用默认值）。
            ctx:             RunContext；必须注入 blob_store。

        Returns:
            LoadResult(rows=[SilverRow], total_count=1)

        Raises:
            ValueError: ctx.blob_store 缺失，或 MINERU_API_URL 未设置，
                        或 MinerU 处理失败。
        """
        blob_store = getattr(ctx, "blob_store", None)
        if blob_store is None:
            raise ValueError(
                "loader pdf-mineru 需 ctx.blob_store；当前 RunContext 未注入"
            )

        api_url = os.environ.get(_ENV_URL, "").strip()
        if not api_url:
            raise ValueError(
                f"loader pdf-mineru 需环境变量 {_ENV_URL}；当前未设置或为空"
            )
        api_token = os.environ.get(_ENV_TOKEN, "").strip() or None

        spec = PdfMineruSpec.model_validate(config or {})

        async def _run() -> LoadResult:
            # 1) 从 blob_store 读 PDF bytes
            pdf_bytes = await blob_store.get(bronze_blob_sha)
            if not isinstance(pdf_bytes, bytes):
                # 有些实现返 AsyncGenerator/stream，尽力拼合
                chunks = []
                async for chunk in pdf_bytes:
                    chunks.append(chunk)
                pdf_bytes = b"".join(chunks)

            filename = f"{bronze_blob_sha[:8]}.pdf"

            # 2) 调 MinerU submit → poll → fetch_full_result
            client = MinerUClient(base_url=api_url, token=api_token)
            task_id = await client.submit(
                pdf_bytes,
                filename,
                parse_method=spec.parse_method,
                backend=spec.backend,
                return_images=spec.return_images,
                return_content_list=spec.return_content_list,
            )
            await _wait_terminal(
                client, task_id, spec.poll_interval_seconds, spec.poll_timeout_seconds
            )
            full = await client.fetch_full_result(task_id)

            markdown: str = full["markdown"]

            # 3) 图片写 blob_store，收集 image 列表
            images_raw: dict[str, bytes] = full.get("images") or {}
            images: list[dict[str, Any]] = []
            for img_filename, img_bytes in images_raw.items():
                img_res = await blob_store.put(
                    BytesIO(img_bytes), declared_size=len(img_bytes)
                )
                images.append({"filename": img_filename, "blob_sha": img_res.sha256})

            # 4) 构造 SilverRow
            row = SilverRow(
                text=markdown,
                images=images,
                source_ref={
                    "blob_sha": bronze_blob_sha,
                    "loader": "pdf-mineru",
                    "loader_version": "0.1",
                },
                stats={
                    "text_chars": len(markdown),
                    "image_count": len(images),
                },
                lineage_ops=[],
            )

            return LoadResult(
                rows=[row],
                total_count=1,
                notes=f"pdf-mineru via {api_url}",
            )

        return asyncio.run(_run())
