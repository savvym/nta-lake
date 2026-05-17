"""BlobStore Protocol：CAS 字节内容存储抽象。

按 .harness/design.md §1.2 #5 / §4.4 / §5.2：
- 字节内容按 sha256 内容寻址
- key 严格 `blobs/{sha256[0:2]}/{sha256}`（具体由 dataplat_api.storage.keys.storage_key_for 实现）
- 同字节内容 put 多次只产生一个 storage 对象（去重）
- server 端流式计算 sha256（不信任 caller）

具体实现（如 MinioBlobStore）见 apps/api/dataplat_api/storage/。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import BinaryIO, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from dataplat_core.domain.types import SHA256


class BlobPutResult(BaseModel):
    """`BlobStore.put` 的返回值。"""

    model_config = ConfigDict(frozen=False, extra="forbid")

    sha256: SHA256
    size: int = Field(ge=0)
    storage_key: str
    deduplicated: bool = Field(
        description="True 表示同字节内容此前已存在；put 是 idempotent",
    )


@runtime_checkable
class BlobStore(Protocol):
    """CAS blob 存储协议。

    所有方法 async；具体实现内部用 `asyncio.to_thread` 包 sync boto3。
    """

    async def put(
        self,
        stream: BinaryIO,
        *,
        declared_size: int | None = None,
    ) -> BlobPutResult:
        """写入字节内容；server 端流式计算 sha256；去重。

        实现应当：
        1. 用临时 key（如 `_tmp/{uuid4}.part`）upload_fileobj
        2. 流式 update sha256
        3. final_key = storage_key_for(sha256)
        4. head_object(final_key)：存在则 delete tmp + deduplicated=True；
           不存在则 copy_object(src=tmp, dst=final) + delete tmp + deduplicated=False
        5. 任何异常路径：best-effort delete tmp（孤儿对象由 retention follow-up 兜底）

        `declared_size` 是可选的声明大小（caller 已知字节数时传，用于早 fail）。
        """
        ...

    def get(self, sha256: str) -> AsyncIterator[bytes]:
        """以 async generator 形式读取字节流。

        首次 `async for` / `__anext__` 时若 blob 不存在 raise `KeyError(sha256)`。
        NoSuchBucket 或其他 ClientError bubble up（非"不存在"语义）。
        """
        ...

    async def exists(self, sha256: str) -> bool:
        """blob 是否存在。404 / NoSuchKey → False；其他 ClientError bubble up。"""
        ...

    async def get_size(self, sha256: str) -> int | None:
        """blob 大小；不存在返 None。"""
        ...

    async def delete(self, sha256: str) -> bool:
        """删除 blob。返回 True 表示之前存在，False 表示之前不存在。

        本变更不要求集成测试覆盖；retention follow-up 加级联删除测试。
        """
        ...
