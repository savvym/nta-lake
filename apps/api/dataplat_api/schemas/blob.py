"""Blob HTTP schemas（spec commit-api-mvp-20260517 AC-1）。"""

from __future__ import annotations

from dataplat_core.domain.types import SHA256
from pydantic import BaseModel, ConfigDict


class BlobUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sha256: SHA256
    size: int
    storage_key: str
    deduplicated: bool
