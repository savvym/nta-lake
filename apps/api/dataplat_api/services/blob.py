"""BlobService：CAS stream 转发 + 异常翻译（spec commit-api-mvp-20260517 AC-2 / AC-7）。

职责：
- 不写 DB / 不查 role（admin 守卫 + repo visibility 由 router 担）
- 仅做 `BlobStore.put / get` 的薄封装 + 类型映射
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import BinaryIO

from dataplat_core.protocols.storage import BlobStore

from dataplat_api.schemas.blob import BlobUploadResponse


class BlobService:
    """无 state。"""

    @staticmethod
    async def upload(
        store: BlobStore,
        stream: BinaryIO,
        declared_size: int | None = None,
    ) -> BlobUploadResponse:
        result = await store.put(stream, declared_size=declared_size)
        return BlobUploadResponse(
            sha256=result.sha256,
            size=result.size,
            storage_key=result.storage_key,
            deduplicated=result.deduplicated,
        )

    @staticmethod
    def stream_get(store: BlobStore, sha256: str) -> AsyncIterator[bytes]:
        return store.get(sha256)
