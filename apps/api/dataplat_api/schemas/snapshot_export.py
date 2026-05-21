"""Snapshot export API schemas（W4-4 web-snapshot-export-ui-20260520）。

SnapshotExportFormat：支持的导出格式枚举。
SnapshotExportTriggerBody：POST /repos/{owner}/{name}/snapshots/{hash}/exports 请求体。
"""

from __future__ import annotations

from typing import Literal, Optional

from dataplat_core.domain.types import SHA256
from pydantic import BaseModel, ConfigDict

SnapshotExportFormat = Literal["hf_datasets", "jsonl", "parquet"]


class SnapshotExportTriggerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: SnapshotExportFormat = "hf_datasets"
    blob_sha: Optional[SHA256] = None
    split: str = "train"
