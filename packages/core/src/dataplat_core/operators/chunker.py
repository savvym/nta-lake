"""ChunkerOperator：按 max_chars 把 1 个 SilverRow 切成 N 个新 row（演示 1→N 语义）。"""
from __future__ import annotations

from typing import Any

from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.operator import OperatorSpec
from dataplat_core.protocols.runcontext import RunContext


class ChunkerOperator:
    """按字符数硬切算子。run() 返回 N 个新 SilverRow；输入 row 不被 mutate。"""

    name: str = "chunker"
    version: str = "1.0"
    spec: OperatorSpec = OperatorSpec(
        name="chunker",
        version="1.0",
        config_schema={
            "type": "object",
            "properties": {"max_chars": {"type": "integer", "minimum": 1}},
            "required": ["max_chars"],
            "additionalProperties": False,
        },
    )

    def run(
        self,
        row: SilverRow,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> list[SilverRow]:
        """按 max_chars 切分 text；空 text 返 []；每个切片追加 lineage_ops 记录。

        使用 model_copy(update=...) + dict/list literal 保证不共享 stats / lineage_ops 引用。
        """
        max_chars = config["max_chars"]
        text = row.text
        if text == "":
            return []
        chunks = [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
        n = len(chunks)
        result: list[SilverRow] = []
        for i, chunk_str in enumerate(chunks):
            new_row = row.model_copy(
                update={
                    "text": chunk_str,
                    "stats": {
                        **row.stats,
                        "chunk_index": i,
                        "chunk_total": n,
                        "text_chars": len(chunk_str),
                    },
                    "lineage_ops": [
                        *row.lineage_ops,
                        {
                            "op": "chunker",
                            "version": "1.0",
                            "max_chars": max_chars,
                            "chunk_index": i,
                            "chunk_total": n,
                        },
                    ],
                }
            )
            result.append(new_row)
        return result
