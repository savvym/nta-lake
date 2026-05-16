"""SourceAdapter Protocol：把外部世界变成 Bronze Repository 的一个 commit。

按 .harness/design.md §4.1。具体 plugin 实现见 plugins/adapter-*。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from dataplat_core.protocols.runcontext import RunContext


class IngestResult(BaseModel):
    """adapter.ingest() 的产出元信息。

    实际文件由 adapter 写入 workspace，平台据此 commit；本对象只回传统计。
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    asset_count: int = 0
    file_count: int = 0
    bytes_written: int = 0
    notes: str | None = None


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
