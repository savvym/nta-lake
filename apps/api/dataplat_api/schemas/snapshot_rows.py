"""Snapshot rows API schemas（W4-1 web-pdf-mineru-ui-v2-20260520）。

SilverRowRead：SilverRow 在 API 边界的薄包装（apps/api schema 层与 dataplat_core 解耦）。
SnapshotRowsResponse：分页列表响应。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SilverRowRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    images: list
    source_ref: dict
    stats: dict
    lineage_ops: list


class SnapshotRowsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: list[SilverRowRead]
    total: int
    offset: int
    limit: int
    blob_sha: str
