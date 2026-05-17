"""Job HTTP schemas（spec rq-worker-skeleton-20260517 AC-6）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from dataplat_api.schemas.ingest import IngestRequest


class JobIngestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner: str
    name: str
    request: IngestRequest


class JobRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    status: str
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
