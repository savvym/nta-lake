"""Process HTTP schemas（spec processor-framework-20260517 AC-5）。"""

from __future__ import annotations

from typing import Any

from dataplat_core.domain.types import SHA256
from pydantic import BaseModel, ConfigDict, Field


class ProcessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_owner: str
    source_name: str
    source_ref: str | None = "main"
    source_commit_hash: SHA256 | None = None  # 优先 commit_hash；否则 source_ref
    target_owner: str
    target_name: str
    processor_name: str
    processor_version: str
    config: dict[str, Any] = Field(default_factory=dict)
    author_id: str
    message: str | None = None
    ref: str | None = None  # 下游 ref 名（如 main）
