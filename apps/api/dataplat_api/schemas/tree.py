"""Tree HTTP schemas（spec commit-api-mvp-20260517 AC-1）。

MVP 仅支持单层 entry_type='blob'；嵌套 tree 留 follow-up tree-nested-*。
"""

from __future__ import annotations

from typing import Literal

from dataplat_core.domain.types import SHA256
from pydantic import BaseModel, ConfigDict


class TreeEntryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    mode: int
    entry_type: Literal["blob"] = "blob"
    target_hash: SHA256


class TreeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entries: list[TreeEntryCreate]


class TreeEntryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    mode: int
    entry_type: Literal["blob"]
    target_hash: SHA256


class TreeRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hash: SHA256
    entries: list[TreeEntryRead]
