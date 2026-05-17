"""Ingest HTTP schemas（spec adapter-framework-20260517 AC-6）。

`IngestRequest` 不含 `created_at`（沿用 commit-api-mvp 方案 B：服务端记录但不入 hash）。
"""

from __future__ import annotations

from typing import Any

from dataplat_core.domain.types import SHA256
from pydantic import BaseModel, ConfigDict, Field

from dataplat_api.schemas.commit import CommitRead


class IngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adapter_name: str
    adapter_version: str
    spec: dict[str, Any]
    author_id: str
    message: str | None = None
    ref: str | None = None
    parents: list[SHA256] = Field(default_factory=list)


class IngestSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_count: int = 0
    file_count: int = 0
    bytes_written: int = 0
    notes: str | None = None


class IngestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commit: CommitRead
    ingest_summary: IngestSummary
