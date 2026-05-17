"""dataplat blob storage 模块。

暴露 `MinioBlobStore` 与 `get_blob_store()` 工厂；后续 service 层用 `Depends(get_blob_store)`。
"""

from __future__ import annotations

import os

from dataplat_api.storage.keys import storage_key_for
from dataplat_api.storage.minio_store import HashingStream, MinioBlobStore

__all__ = [
    "MinioBlobStore",
    "HashingStream",
    "storage_key_for",
    "get_blob_store",
]

_blob_store: MinioBlobStore | None = None


def get_blob_store() -> MinioBlobStore:
    """从环境变量懒构造 MinioBlobStore 单例。

    环境变量：
    - DATAPLAT_MINIO_ENDPOINT（默认 http://localhost:9000）
    - DATAPLAT_MINIO_ACCESS_KEY（默认 dataplat）
    - DATAPLAT_MINIO_SECRET_KEY（默认 dataplat-dev-secret）
    - DATAPLAT_BLOB_BUCKET（默认 dataplat-blobs）
    - DATAPLAT_MINIO_REGION（默认 us-east-1）

    测试 fixture 应直接 `MinioBlobStore(...)` 显式 override 参数（含 uuid 前缀 bucket），
    不调用本工厂——避免污染默认 bucket。
    """
    global _blob_store
    if _blob_store is None:
        _blob_store = MinioBlobStore(
            endpoint_url=os.environ.get(
                "DATAPLAT_MINIO_ENDPOINT", "http://localhost:9000"
            ),
            access_key=os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat"),
            secret_key=os.environ.get(
                "DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret"
            ),
            bucket=os.environ.get("DATAPLAT_BLOB_BUCKET", "dataplat-blobs"),
            region=os.environ.get("DATAPLAT_MINIO_REGION", "us-east-1"),
        )
    return _blob_store
