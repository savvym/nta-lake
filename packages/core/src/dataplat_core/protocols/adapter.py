"""SourceAdapter Protocol：把外部世界变成 Bronze Repository 的一个 commit。

按 .harness/design.md §4.1。具体 plugin 实现见 plugins/adapter-*。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from dataplat_core.domain.types import SHA256
from dataplat_core.protocols.runcontext import RunContext


class IngestFileRef(BaseModel):
    """adapter.ingest() 产出的 (path → blob_sha256) 映射。

    Runner 用此构造 Tree entries 调 CommitService（spec adapter-framework AC-1）。
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    path: str
    sha256: SHA256
    mode: int = 33188  # 0o100644 unix regular file


class IngestResult(BaseModel):
    """adapter.ingest() 的产出元信息 + 文件清单。

    `files` 是 runner commit 的 ground truth（路径 + blob sha256）；
    其他字段是统计 / notes。
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    asset_count: int = 0
    file_count: int = 0
    bytes_written: int = 0
    notes: str | None = None
    files: list[IngestFileRef] = Field(default_factory=list)


@runtime_checkable
class SourceAdapter(Protocol):
    """获取器协议。Adapter 用 entry_point 注册到平台。"""

    name: str
    version: str
    input_schema: dict[str, Any]
    output_subtype: str

    def ingest(
        self,
        spec: dict[str, Any],
        workspace: Path,
        ctx: RunContext,
    ) -> IngestResult: ...
