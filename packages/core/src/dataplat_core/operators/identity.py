"""IdentityOperator：标杆 Operator，原样透传 SilverRow 并追加 lineage_ops。

作为所有 Operator 实现的参考范本：
- 属性声明与 OperatorSpec 同形；
- run() 必须返新 row（model_copy），不得原地修改输入；
- lineage_ops 追加用 list literal，保证不 mutate 原 list。
"""

from __future__ import annotations

from typing import Any

from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.operator import OperatorSpec
from dataplat_core.protocols.runcontext import RunContext


class IdentityOperator:
    """原样透传算子。run() 返回含追加一条 lineage_ops 记录的新 SilverRow。"""

    name: str = "identity"
    version: str = "1.0"
    spec: OperatorSpec = OperatorSpec(name="identity", version="1.0", config_schema={})

    def run(
        self,
        row: SilverRow,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> list[SilverRow]:
        """返回含追加 identity op 记录的新 row；输入 row 不被 mutate。

        使用 model_copy(update=...) + list literal 保证不共享 lineage_ops 引用。
        """
        new_row = row.model_copy(
            update={
                "lineage_ops": [*row.lineage_ops, {"op": "identity", "version": "1.0"}]
            }
        )
        return [new_row]
