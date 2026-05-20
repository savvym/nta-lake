"""SnapshotSampleOperator：基于 row 内容确定性哈希做按权重抽样。

典型用法：recipe v2 mixing 场景——snapshot A 配 weight=0.7，snapshot B 配
weight=0.3，两者 union 后 row 比例稳定（与 GPT-3/Gopher data-mixing 同模式）。

核心算法：sha256((seed + row.text).encode("utf-8")) 取前 16 hex → uint64 / 2^64
得 uniform [0, 1) 确定性值 u；u >= weight → drop；否则 keep。
- weight=1.0 时 max(u) < 1.0 → 永远 keep
- weight=0.0 时 u >= 0 → 永远 drop
"""

from __future__ import annotations

import hashlib
from typing import Any

from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.operator import OperatorSpec
from dataplat_core.protocols.runcontext import RunContext


class SnapshotSampleOperator:
    """确定性加权抽样算子。run() 按 sha256 哈希决定 keep/drop；相同 (text, seed) 永远同 decision；输入 row 不被 mutate。"""

    name: str = "snapshot_sample"
    version: str = "1.0"
    spec: OperatorSpec = OperatorSpec(
        name="snapshot_sample",
        version="1.0",
        config_schema={
            "type": "object",
            "properties": {
                "weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "seed": {"type": "string"},
            },
            "required": ["weight"],
            "additionalProperties": False,
        },
    )

    def run(
        self,
        row: SilverRow,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> list[SilverRow]:
        """用 sha256 确定性哈希决定是否保留当前 row。

        u = int(sha256((seed + row.text).encode("utf-8")).hexdigest()[:16], 16) / (1 << 64)
        u >= weight → return []（drop）；否则追加 lineage_ops 返 [new_row]（keep）。

        使用 model_copy(update=...) + list literal 保证不共享 lineage_ops 引用。
        """
        weight: float = config["weight"]  # 必填；0.0 ≤ w ≤ 1.0，v1 不做校验
        seed: str = config.get("seed", "")  # 可选，默认空串

        # 确定性哈希：sha256 前 16 hex → uint64 / 2^64 得 uniform [0, 1)
        h = hashlib.sha256((seed + row.text).encode("utf-8")).hexdigest()
        u = int(h[:16], 16) / (1 << 64)

        if u >= weight:
            return []  # drop

        # keep：追加 lineage_ops 后返新 row
        new_row = row.model_copy(
            update={
                "lineage_ops": [
                    *row.lineage_ops,
                    {
                        "op": "snapshot_sample",
                        "version": "1.0",
                        "weight": weight,
                        "seed": seed,
                    },
                ]
            }
        )
        return [new_row]
