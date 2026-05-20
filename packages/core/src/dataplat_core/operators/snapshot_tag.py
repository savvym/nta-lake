"""SnapshotTagOperator：给 SilverRow 打上 source_snapshot 标签。

典型用法：recipe v2 在 union 多个 snapshot 行流前，先对每条 row
打上来源 snapshot 名称（以及可选的混合权重），便于下游识别行来源。
始终 1→1，即使 weight 未提供也追加 lineage_ops 保证血缘完整性。
"""

from __future__ import annotations

from typing import Any

from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.operator import OperatorSpec
from dataplat_core.protocols.runcontext import RunContext


class SnapshotTagOperator:
    """snapshot 来源标签算子。run() 返在 stats 中写入 source_snapshot（及可选 source_snapshot_weight）的新 row；输入 row 不被 mutate。"""

    name: str = "snapshot_tag"
    version: str = "1.0"
    spec: OperatorSpec = OperatorSpec(
        name="snapshot_tag",
        version="1.0",
        config_schema={
            "type": "object",
            "properties": {
                "snapshot_name": {"type": "string"},
                "snapshot_weight": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "required": ["snapshot_name"],
            "additionalProperties": False,
        },
    )

    def run(
        self,
        row: SilverRow,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> list[SilverRow]:
        """将 snapshot_name 写入 stats.source_snapshot；若提供 snapshot_weight 则同时写入 stats.source_snapshot_weight。

        使用 model_copy(update=...) + dict literal 保证不共享 stats / lineage_ops 引用。
        """
        name = config["snapshot_name"]  # 必填；缺失 → KeyError（v1 expected）
        weight = config.get("snapshot_weight")  # 可选

        # 构造新 stats：展开原 stats，追加 source_snapshot（及可选 weight）
        new_stats: dict[str, Any] = {**row.stats, "source_snapshot": name}
        if weight is not None:
            new_stats["source_snapshot_weight"] = weight

        # 构造 lineage_ops 条目
        lineage_entry: dict[str, Any] = {
            "op": "snapshot_tag",
            "version": "1.0",
            "snapshot_name": name,
        }
        if weight is not None:
            lineage_entry["snapshot_weight"] = weight

        new_row = row.model_copy(
            update={
                "stats": new_stats,
                "lineage_ops": [*row.lineage_ops, lineage_entry],
            }
        )
        return [new_row]
