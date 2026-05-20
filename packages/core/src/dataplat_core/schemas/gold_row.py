"""Gold 层行 schema。

GoldSFTRow：Gold SFT（Supervised Fine-Tuning）标准行格式，
含 prompt / completion / source_ref / stats / lineage_ops。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GoldSFTRow(BaseModel):
    """Gold SFT 一行数据。

    - `prompt`：输入提示词，必填。
    - `completion`：期望输出，必填。
    - `source_ref`：溯源信息（如 silver 行的 sha + repo 路径）。
    - `stats`：token 数、字符数等统计；stats-first 原则。
    - `lineage_ops`：已执行的 Operator 链，每项 ``{"op": name, "version": ver, ...}``。
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    prompt: str
    completion: str
    source_ref: dict
    stats: dict = Field(default_factory=dict)
    lineage_ops: list[dict] = Field(default_factory=list)
