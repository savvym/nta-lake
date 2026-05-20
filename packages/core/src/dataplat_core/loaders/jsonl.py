"""JsonlLoader：Bronze .jsonl / .jsonl.gz blob → SilverRow 列表（每行 1 row）。

stats per row:
  - format: "jsonl" / "jsonl.gz"
  - char_count: int

全局量放 LoadResult.notes："line_count={N}, error_count={N}"
  - line_count = 有效行数（= total_count = len(rows)）
  - error_count = 坏行数（坏 json + 非 dict + 缺 text_field）
"""

from __future__ import annotations

import asyncio
import gzip
import json
from typing import Any

from dataplat_core.domain.types import SHA256
from dataplat_core.protocols.loader import LoadResult, SilverRow
from dataplat_core.protocols.runcontext import RunContext


class JsonlLoader:
    """Bronze .jsonl / .jsonl.gz blob → SilverRow loader。"""

    name: str = "jsonl"
    version: str = "0.1"
    input_subtype: str = "jsonl"
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
                "loader jsonl 需 ctx.blob_store；当前 RunContext 未注入"
            )

        cfg = config or {}
        format_hint: str | None = cfg.get("format")
        path_hint: str | None = cfg.get("path")
        # 决策 3：空串 / None 都走默认 "text"
        text_field: str = cfg.get("text_field") or "text"

        async def _run() -> LoadResult:
            data = await blob_store.get(bronze_blob_sha)
            if not isinstance(data, bytes):
                chunks = []
                async for chunk in data:
                    chunks.append(chunk)
                data = b"".join(chunks)

            # 决策 5：format hint 或 path hint 命中 .jsonl.gz → 解压
            is_gz = format_hint == "jsonl.gz" or (
                path_hint is not None and path_hint.lower().endswith(".jsonl.gz")
            )
            if is_gz:
                data = gzip.decompress(data)
                fmt = "jsonl.gz"
            else:
                fmt = "jsonl"

            text = data.decode("utf-8", errors="replace")

            rows: list[SilverRow] = []
            error_count = 0

            for idx, raw_line in enumerate(text.splitlines(), start=1):
                # 决策 8：空行跳过，不计 error，不计 line_count
                if not raw_line.strip():
                    continue

                try:
                    obj = json.loads(raw_line)
                except json.JSONDecodeError:
                    error_count += 1
                    continue

                if not isinstance(obj, dict):
                    error_count += 1
                    continue

                val = obj.get(text_field)
                if not isinstance(val, str):
                    # 决策 9：缺 text_field 或非 str → error
                    error_count += 1
                    continue

                rows.append(
                    SilverRow(
                        text=val,
                        images=[],
                        source_ref={
                            "blob_sha": bronze_blob_sha,
                            "loader": "jsonl",
                            "loader_version": "0.1",
                            "line_no": idx,  # 决策 7：1-based 原行号
                        },
                        stats={
                            "format": fmt,
                            "char_count": len(val),  # 决策 6：per-row 极简
                        },
                        lineage_ops=[],
                    )
                )

            # AC-2 澄清：line_count = len(rows)（有效行数）；error_count = 坏行数
            notes = f"line_count={len(rows)}, error_count={error_count}"
            return LoadResult(rows=rows, total_count=len(rows), notes=notes)

        return asyncio.run(_run())
