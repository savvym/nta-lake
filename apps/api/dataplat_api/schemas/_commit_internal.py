"""内部 runner / service 层 Commit schema（W1-1 保留；不面向外部 API）。

外部 API 接收 SnapshotCreate（parent: SHA256 | None），
CommitService.create_snapshot 负责桥接 SnapshotCreate → CommitCreate。
AdapterRunner / ProcessorRunner 直接构造 CommitCreate 调 CommitService.create_commit。

DB 层 commits 表以 parents: list[str] 存储（D-1 决策；不动 DB schema）。
"""

from __future__ import annotations

from dataplat_core.domain.lineage import Lineage
from dataplat_core.domain.types import SHA256
from pydantic import BaseModel, ConfigDict, Field

from dataplat_api.schemas.tree import TreeCreate


class CommitCreate(BaseModel):
    """内部 CommitService.create_commit 参数；parents 保留 list 与 DB 兼容。"""

    model_config = ConfigDict(extra="forbid")

    tree: TreeCreate
    parents: list[SHA256] = Field(default_factory=list)
    author_id: str
    message: str | None = None
    lineage: Lineage | None = None
    ref: str | None = None
