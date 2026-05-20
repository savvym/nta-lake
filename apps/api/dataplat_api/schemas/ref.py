"""Ref HTTP schemas（spec repo-files-tab-20260517 AC-1）。"""

from __future__ import annotations

from dataplat_core.domain.types import SHA256
from pydantic import BaseModel, ConfigDict


class RefRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    snapshot_hash: SHA256
