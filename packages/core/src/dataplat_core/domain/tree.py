"""Tree 与 TreeEntry：类 Git 的 Tree 对象。

落库结构（见 spec AC-9）：
- `trees(hash, repo_id, created_at)`
- `tree_entries(tree_hash FK, position, name, mode, entry_type, target_hash)`

不嵌 JSONB；理由：单行可被外键引用、平展索引便于查询 / diff。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from dataplat_core.domain.types import SHA256


class TreeEntry(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    name: str = Field(min_length=1, description="文件 / 子目录名（仅本级）")
    mode: int = Field(
        description="POSIX mode（如普通文件 0o100644 = 33188；子目录 0o040000）",
    )
    entry_type: Literal["blob", "tree"]
    target_hash: SHA256


class Tree(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    hash: SHA256
    entries: list[TreeEntry] = Field(
        default_factory=list,
        description="按 name 字典序稳定排列；空 tree 也合法（表示空目录）",
    )
