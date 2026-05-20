"""Snapshot HTTP schemas（W1-1 api-snapshot-rename-20260520；前称 CommitCreate / CommitRead）。

SnapshotCreate **不含 `created_at`**（spec v2 AC-9 方案 B）——服务端记录 created_at
但**不参与 snapshot canonical hash**，与 CAS"同内容同 hash"语义一致。

DB 内部仍用 commits 表（D-1）；API 边界在 _snapshot_to_read 做翻译。
parents list[SHA256] 退化为 parent: SHA256 | None（data-not-code-pivot § 旧→新术语表）。
"""

from __future__ import annotations

from datetime import datetime

from dataplat_core.domain.lineage import Lineage
from dataplat_core.domain.types import SHA256
from pydantic import BaseModel, ConfigDict

from dataplat_api.schemas.tree import TreeCreate, TreeRead


class SnapshotCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tree: TreeCreate
    parent: SHA256 | None = None
    author_id: str
    message: str | None = None
    lineage: Lineage | None = None
    ref: str | None = None


class SnapshotRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hash: SHA256
    repo_id: str
    tree_hash: SHA256
    parent: SHA256 | None
    author_id: str
    created_at: datetime
    message: str | None
    lineage: Lineage | None
    tree: TreeRead
    deduplicated: bool
