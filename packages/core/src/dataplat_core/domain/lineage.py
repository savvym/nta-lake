"""Lineage / ProducedBy / InputRef：commit 内嵌的来源元信息。

落库：以 JSONB 形式嵌在 `commits.lineage_json` 列（design.md §4.4 + §8 决策）。
不拆 lineage_edges 衍生表——查询需要时由独立 follow-up 派生。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from dataplat_core.domain.types import SHA256


class ProducedBy(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    kind: Literal["adapter", "processor", "manual"]
    name: str
    version: str
    config_hash: SHA256


class InputRef(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    repo: str = Field(description="上游 repository 的 fully qualified id")
    commit: SHA256


class Lineage(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    produced_by: ProducedBy
    inputs: list[InputRef] = Field(
        default_factory=list,
        description="本 commit 的上游 commits；adapter 产出的 Bronze 通常为空",
    )
    run_id: str
    env: dict[str, Any] = Field(
        default_factory=dict,
        description="运行环境：python 版本、model id（LLM）、依赖摘要等",
    )
