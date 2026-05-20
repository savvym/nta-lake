"""DedupOperator：按 text 或 source_blob 去重 SilverRow。

在 ctx 上维护 _dedup_seen set；同一 pipeline run 内重复 hash_key 的行丢弃。
"""

from __future__ import annotations

import hashlib
from typing import Any

from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.operator import OperatorSpec
from dataplat_core.protocols.runcontext import RunContext


class DedupOperator:
    """去重算子。run() 首次出现的 hash_key 返新 row；重复返空列表；输入不被 mutate。"""

    name: str = "dedup"
    version: str = "1.0"
    spec: OperatorSpec = OperatorSpec(
        name="dedup",
        version="1.0",
        config_schema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "enum": ["text", "source_blob"]}
            },
            "additionalProperties": False,
        },
    )

    def run(
        self,
        row: SilverRow,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> list[SilverRow]:
        """按 key 计算 hash；首次出现写入 ctx._dedup_seen 并返新 row；重复返 []。

        使用 model_copy(update=...) + list literal 保证不共享 lineage_ops 引用。
        """
        key = config.get("key", "text")
        if key == "text":
            hash_key = hashlib.sha256(row.text.encode("utf-8")).hexdigest()
        else:  # source_blob
            hash_key = row.source_ref["blob_sha"]

        seen = getattr(ctx, "_dedup_seen", None)
        if seen is None:
            seen = set()
            setattr(ctx, "_dedup_seen", seen)

        if hash_key in seen:
            return []

        seen.add(hash_key)
        new_row = row.model_copy(
            update={
                "lineage_ops": [
                    *row.lineage_ops,
                    {"op": "dedup", "version": "1.0", "key": key},
                ]
            }
        )
        return [new_row]
