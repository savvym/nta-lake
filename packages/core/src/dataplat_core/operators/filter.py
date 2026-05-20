"""FilterOperator：按最小字符数过滤 SilverRow。

- min_chars = 0（默认）：不过滤，所有行透传；
- min_chars > 0：len(row.text) < min_chars 的行丢弃（返回空列表）。
"""

from __future__ import annotations

from typing import Any

from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.operator import OperatorSpec
from dataplat_core.protocols.runcontext import RunContext


class FilterOperator:
    """按 min_chars 过滤行算子。run() 返新 row 或空列表；输入 row 不被 mutate。"""

    name: str = "filter"
    version: str = "1.0"
    spec: OperatorSpec = OperatorSpec(
        name="filter",
        version="1.0",
        config_schema={
            "type": "object",
            "properties": {"min_chars": {"type": "integer", "minimum": 0}},
            "additionalProperties": False,
        },
    )

    def run(
        self,
        row: SilverRow,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> list[SilverRow]:
        """若 len(row.text) < min_chars 返空列表；否则返追加 lineage_ops 的新 row。

        使用 model_copy(update=...) + list literal 保证不共享 lineage_ops 引用。
        """
        min_chars = config.get("min_chars", 0)
        if len(row.text) < min_chars:
            return []
        new_row = row.model_copy(
            update={
                "lineage_ops": [
                    *row.lineage_ops,
                    {"op": "filter", "version": "1.0", "min_chars": min_chars},
                ]
            }
        )
        return [new_row]
