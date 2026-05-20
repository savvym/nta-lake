"""Repository HTTP schemas（request / response）。

与 dataplat_core.domain.repository.Repository 在字段上对齐但**不复用**：
domain 模型是跨 service/SDK/worker 的通用类型，HTTP schema 含
HTTP 专属的输入约束 + Optional 字段（partial update）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from dataplat_core.domain.repository import Layer, Subtype, Visibility
from pydantic import BaseModel, ConfigDict


class RepositoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner: str
    name: str
    layer: Layer
    subtype: Subtype
    visibility: Visibility = "private"
    description: str | None = None
    schema_id: str | None = None
    row_format: Literal["parquet", "jsonl"] | None = None


class RepositoryRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    owner: str
    name: str
    layer: Layer
    subtype: Subtype
    visibility: Visibility
    description: str | None
    schema_id: str | None
    row_format: str | None
    created_at: datetime
    updated_at: datetime


class RepositoryListItem(BaseModel):
    """list 响应的简化条目（与 Read 字段相同，但单独类型便于后续演进）。"""

    model_config = ConfigDict(extra="forbid")

    id: str
    owner: str
    name: str
    layer: Layer
    subtype: Subtype
    visibility: Visibility
    description: str | None
    schema_id: str | None
    row_format: str | None
    created_at: datetime
    updated_at: datetime


class RepositoryUpdate(BaseModel):
    """PATCH partial update：全 Optional 默认 None；只更新非 None 字段。

    spec MUST FIX #4：避免误清——None 表示"未传"而非"清空"。
    """

    model_config = ConfigDict(extra="forbid")

    visibility: Visibility | None = None
    description: str | None = None


class RepositoryListResponse(BaseModel):
    """GET /repos 响应。"""

    model_config = ConfigDict(extra="forbid")

    items: list[RepositoryListItem]
    total: int
