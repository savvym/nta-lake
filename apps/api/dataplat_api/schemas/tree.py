"""Tree HTTP schemas（spec commit-api-mvp-20260517 AC-1；tree-nested-domain-20260520 放宽）。

Soft mode：调用方仍可传扁平 name（含 `/`，如 "images/abc.jpg"），CommitService
内部把扁平 entries 自动转为嵌套 tree（递归子 tree + sha256 hash）。entry_type
支持 "blob" / "tree" 两种；type=tree 时 mode = 0o040000 (16384)。
"""

from __future__ import annotations

from typing import Literal

from dataplat_core.domain.types import SHA256
from pydantic import BaseModel, ConfigDict


class TreeEntryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    mode: int
    entry_type: Literal["blob", "tree"] = "blob"
    target_hash: SHA256


class TreeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entries: list[TreeEntryCreate]


class TreeEntryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    mode: int
    entry_type: Literal["blob", "tree"]
    target_hash: SHA256


class TreeRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hash: SHA256
    entries: list[TreeEntryRead]
