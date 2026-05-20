"""DocxLoader：Bronze .docx blob → SilverRow（via python-docx）。

stats:
  - format: "docx"
  - paragraph_count: int
  - image_count: int
  - char_count: int

图片写 blob_store；images 列含 {filename, blob_sha, content_type}。
"""

from __future__ import annotations

import asyncio
from io import BytesIO
from typing import Any

from dataplat_core.domain.types import SHA256
from dataplat_core.protocols.loader import LoadResult, SilverRow
from dataplat_core.protocols.runcontext import RunContext


class DocxLoader:
    name: str = "docx"
    version: str = "0.1"
    input_subtype: str = "docx"
    output_schema_id: str = "silver-text-v1"

    def load(
        self,
        bronze_blob_sha: SHA256,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> LoadResult:
        del config  # 暂不接受 config 选项
        blob_store = getattr(ctx, "blob_store", None)
        if blob_store is None:
            raise ValueError(
                "loader docx 需 ctx.blob_store；当前 RunContext 未注入"
            )

        async def _run() -> LoadResult:
            from docx import Document

            data = await blob_store.get(bronze_blob_sha)
            if not isinstance(data, bytes):
                chunks = []
                async for chunk in data:
                    chunks.append(chunk)
                data = b"".join(chunks)

            doc = Document(BytesIO(data))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n\n".join(paragraphs)

            images: list[dict[str, Any]] = []
            for rel_id, part in doc.part.related_parts.items():
                ct = getattr(part, "content_type", "") or ""
                if not ct.startswith("image/"):
                    continue
                img_bytes = part.blob
                put_res = await blob_store.put(
                    BytesIO(img_bytes), declared_size=len(img_bytes)
                )
                filename = part.partname.split("/")[-1] if hasattr(part, "partname") else f"image-{rel_id}"
                images.append({
                    "filename": filename,
                    "blob_sha": put_res.sha256,
                    "content_type": ct,
                })

            row = SilverRow(
                text=text,
                images=images,
                source_ref={
                    "blob_sha": bronze_blob_sha,
                    "loader": "docx",
                    "loader_version": "0.1",
                },
                stats={
                    "format": "docx",
                    "paragraph_count": len(paragraphs),
                    "image_count": len(images),
                    "char_count": len(text),
                },
                lineage_ops=[],
            )

            return LoadResult(
                rows=[row],
                total_count=1,
                notes=f"docx paragraphs={len(paragraphs)}, images={len(images)}",
            )

        return asyncio.run(_run())
