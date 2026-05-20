"""ScoreOperator：对 SilverRow 打分并写入 stats。

支持两种 metric：
- text_chars:  len(row.text)（字符数）
- alpha_ratio: 字母字符占比（保留 4 位小数）
"""

from __future__ import annotations

from typing import Any

from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.operator import OperatorSpec
from dataplat_core.protocols.runcontext import RunContext


class ScoreOperator:
    """打分算子。run() 返追加 stats 与 lineage_ops 的新 row；输入 row 不被 mutate。"""

    name: str = "score"
    version: str = "1.0"
    spec: OperatorSpec = OperatorSpec(
        name="score",
        version="1.0",
        config_schema={
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": ["text_chars", "alpha_ratio"],
                }
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
        """计算 metric 得分并合并到 stats；返含追加 lineage_ops 的新 row。

        使用 model_copy(update=...) + dict literal 保证不共享 stats / lineage_ops 引用。
        """
        metric = config.get("metric", "text_chars")
        if metric == "text_chars":
            score: int | float = len(row.text)
        else:  # alpha_ratio
            score = round(
                sum(1 for c in row.text if c.isalpha()) / max(len(row.text), 1),
                4,
            )

        new_stats = {**row.stats, f"score_{metric}": score}
        new_row = row.model_copy(
            update={
                "stats": new_stats,
                "lineage_ops": [
                    *row.lineage_ops,
                    {"op": "score", "version": "1.0", "metric": metric},
                ],
            }
        )
        return [new_row]
