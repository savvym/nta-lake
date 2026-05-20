"""ImageStripOperator：清空 SilverRow.images 列表，写 stats.image_count=0。

将 images 清空（配合 ImageCaptionStubOperator 实现"先抽 caption 再丢图"模式）。
始终 1→1，即使原 images 已为空也追加 lineage_ops 保证血缘完整性。
"""

from __future__ import annotations

from typing import Any

from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.operator import OperatorSpec
from dataplat_core.protocols.runcontext import RunContext


class ImageStripOperator:
    """清空图片算子。run() 返回 images=[] + stats.image_count=0 的新 row；输入 row 不被 mutate。"""

    name: str = "image_strip"
    version: str = "1.0"
    spec: OperatorSpec = OperatorSpec(
        name="image_strip",
        version="1.0",
        config_schema={"type": "object", "additionalProperties": False},
    )

    def run(
        self,
        row: SilverRow,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> list[SilverRow]:
        """清空 images 字段并将 stats.image_count 设为 0；返含追加 lineage_ops 的新 row。

        使用 model_copy(update=...) + dict literal 保证不共享 stats / lineage_ops / images 引用。
        """
        new_row = row.model_copy(
            update={
                "images": [],
                "stats": {**row.stats, "image_count": 0},
                "lineage_ops": [
                    *row.lineage_ops,
                    {"op": "image_strip", "version": "1.0"},
                ],
            }
        )
        return [new_row]
