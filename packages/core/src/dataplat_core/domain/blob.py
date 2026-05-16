"""BlobRef：CAS blob 的逻辑引用。

仅领域模型，不含读写实现（cas-storage-<yyyymmdd> 变更引入 BlobStore Protocol
与 MinioBlobStore 实现）。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dataplat_core.domain.types import SHA256


class BlobRef(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    sha256: SHA256
    size: int = Field(ge=0, description="字节数；CAS 写入前 hash 时计入")
    storage_key: str = Field(
        description="对象存储 key，规范：blobs/{sha256[0:2]}/{sha256}",
    )
