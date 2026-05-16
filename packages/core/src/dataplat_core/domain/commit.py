"""Commit：Repository 的原子变更。

类 Git Commit + 内嵌 lineage（design.md §4.4）。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from dataplat_core.domain.lineage import Lineage
from dataplat_core.domain.types import SHA256


class Commit(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    hash: SHA256
    repo_id: str
    tree_hash: SHA256
    parents: list[SHA256] = Field(
        default_factory=list,
        description="0 个 = root commit；>=2 个 = merge commit",
    )
    author_id: str
    created_at: datetime | None = None
    message: str | None = None
    lineage: Lineage | None = Field(
        default=None,
        description="adapter / processor 产出的 commit 必有；纯手工提交可为 None",
    )
