"""MinioBlobStore：基于 boto3 S3 兼容客户端的 CAS BlobStore 实现。

实现 `dataplat_core.protocols.storage.BlobStore` Protocol。

核心算法（spec AC-7 6 步）：
  1. tmp_key = `_tmp/{uuid4}.part`
  2. HashingStream 包装 BinaryIO（read 同步 update sha256 + size）
  3. asyncio.to_thread(s3.upload_fileobj, hashing_stream, bucket, tmp_key)
  4. final_key = storage_key_for(hex_sha256)
  5. head_object(final_key)：
       - 存在 → delete tmp + deduplicated=True
       - 404/NoSuchKey → copy_object + delete tmp + deduplicated=False
  6. 异常路径 → best-effort delete tmp（孤儿对象由 retention follow-up 兜底）
"""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from collections.abc import AsyncIterator
from typing import Any, BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dataplat_core.protocols.storage import BlobPutResult

from dataplat_api.storage.keys import storage_key_for

_NOT_FOUND_CODES = {"404", "NoSuchKey", "NotFound"}
_CHUNK_SIZE = 64 * 1024


class HashingStream:
    """包装 BinaryIO，read 时同步累加 sha256 + size。

    boto3 `upload_fileobj` 只依赖 `read(size)` 接口；本类满足且不复制字节。
    """

    def __init__(self, inner: BinaryIO) -> None:
        self._inner = inner
        self._hasher = hashlib.sha256()
        self._size = 0

    def read(self, size: int = -1) -> bytes:
        chunk = self._inner.read(size)
        if chunk:
            self._hasher.update(chunk)
            self._size += len(chunk)
        return chunk

    @property
    def hex_sha256(self) -> str:
        return self._hasher.hexdigest()

    @property
    def size(self) -> int:
        return self._size


class MinioBlobStore:
    """boto3-based CAS BlobStore（兼容 MinIO / AWS S3）。"""

    def __init__(
        self,
        *,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "us-east-1",
    ) -> None:
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )
        self._ensure_bucket_sync()

    def _ensure_bucket_sync(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            code = _client_error_code(exc)
            if code in _NOT_FOUND_CODES:
                self._client.create_bucket(Bucket=self._bucket)
            else:
                raise

    async def put(
        self,
        stream: BinaryIO,
        *,
        declared_size: int | None = None,
    ) -> BlobPutResult:
        del declared_size  # 当前未做早 fail；后续 follow-up 加 size limit
        tmp_key = f"_tmp/{uuid.uuid4().hex}.part"
        hashing = HashingStream(stream)

        try:
            await asyncio.to_thread(
                self._client.upload_fileobj,
                hashing,
                self._bucket,
                tmp_key,
            )
            hex_sha = hashing.hex_sha256
            final_key = storage_key_for(hex_sha)

            existed = await self._head_exists(final_key)

            if existed:
                await self._delete_obj(tmp_key)
                deduplicated = True
            else:
                await asyncio.to_thread(
                    self._client.copy_object,
                    Bucket=self._bucket,
                    Key=final_key,
                    CopySource={"Bucket": self._bucket, "Key": tmp_key},
                )
                await self._delete_obj(tmp_key)
                deduplicated = False

            return BlobPutResult(
                sha256=hex_sha,
                size=hashing.size,
                storage_key=final_key,
                deduplicated=deduplicated,
            )
        except Exception:
            # best-effort 清理 tmp；异常仍 bubble up
            await self._best_effort_delete(tmp_key)
            raise

    def get(self, sha256: str) -> AsyncIterator[bytes]:
        return self._iter_blob(sha256)

    async def _iter_blob(self, sha256: str) -> AsyncIterator[bytes]:
        key = storage_key_for(sha256)
        try:
            resp = await asyncio.to_thread(
                self._client.get_object, Bucket=self._bucket, Key=key
            )
        except ClientError as exc:
            if _client_error_code(exc) in _NOT_FOUND_CODES:
                raise KeyError(sha256) from exc
            raise

        body = resp["Body"]
        try:
            while True:
                chunk = await asyncio.to_thread(body.read, _CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk
        finally:
            await asyncio.to_thread(body.close)

    async def exists(self, sha256: str) -> bool:
        return await self._head_exists(storage_key_for(sha256))

    async def get_size(self, sha256: str) -> int | None:
        key = storage_key_for(sha256)
        try:
            resp = await asyncio.to_thread(
                self._client.head_object, Bucket=self._bucket, Key=key
            )
        except ClientError as exc:
            if _client_error_code(exc) in _NOT_FOUND_CODES:
                return None
            raise
        return int(resp["ContentLength"])

    async def delete(self, sha256: str) -> bool:
        key = storage_key_for(sha256)
        existed = await self._head_exists(key)
        await self._delete_obj(key)
        return existed

    async def _head_exists(self, key: str) -> bool:
        try:
            await asyncio.to_thread(
                self._client.head_object, Bucket=self._bucket, Key=key
            )
        except ClientError as exc:
            if _client_error_code(exc) in _NOT_FOUND_CODES:
                return False
            raise
        return True

    async def _delete_obj(self, key: str) -> None:
        await asyncio.to_thread(
            self._client.delete_object, Bucket=self._bucket, Key=key
        )

    async def _best_effort_delete(self, key: str) -> None:
        try:
            await self._delete_obj(key)
        except Exception:
            # 孤儿对象由 retention follow-up 兜底
            pass


def _client_error_code(exc: ClientError) -> str:
    err: Any = exc.response.get("Error") if hasattr(exc, "response") else None
    if isinstance(err, dict):
        return str(err.get("Code", ""))
    return ""
