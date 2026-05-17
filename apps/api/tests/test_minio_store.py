"""MinioBlobStore 集成测试：依赖 MinIO 容器。

Fixture：每测一个唯一 bucket `dataplat-test-{uuid4().hex[:8]}`；teardown 清空对象后 delete_bucket，
避免污染默认 bucket（spec AC-15 v2）。

需要环境变量：
- DATAPLAT_MINIO_ENDPOINT（必须，否则 skipif）
- DATAPLAT_MINIO_ACCESS_KEY / DATAPLAT_MINIO_SECRET_KEY（默认 dataplat / dataplat-dev-secret）
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import secrets
import uuid
from collections.abc import AsyncGenerator

import boto3
import pytest
from dataplat_api.storage.minio_store import MinioBlobStore


def _minio_endpoint() -> str | None:
    return os.environ.get("DATAPLAT_MINIO_ENDPOINT")


pytestmark = pytest.mark.skipif(
    not _minio_endpoint(),
    reason="DATAPLAT_MINIO_ENDPOINT 未设置；MinIO 集成测试跳过",
)


@pytest.fixture
async def store() -> AsyncGenerator[MinioBlobStore, None]:
    bucket = f"dataplat-test-{uuid.uuid4().hex[:8]}"
    s = MinioBlobStore(
        endpoint_url=_minio_endpoint() or "",
        access_key=os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat"),
        secret_key=os.environ.get("DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret"),
        bucket=bucket,
    )
    try:
        yield s
    finally:
        # teardown：清空对象后 delete_bucket
        raw = boto3.client(
            "s3",
            endpoint_url=_minio_endpoint() or "",
            aws_access_key_id=os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat"),
            aws_secret_access_key=os.environ.get(
                "DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret"
            ),
            region_name="us-east-1",
        )
        paginator = raw.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get("Contents") or []:
                raw.delete_object(Bucket=bucket, Key=obj["Key"])
        try:
            raw.delete_bucket(Bucket=bucket)
        except Exception:  # noqa: BLE001
            pass


@pytest.mark.asyncio
async def test_put_get_roundtrip_and_missing_keyerror(store: MinioBlobStore) -> None:
    data = b"hello dataplat"
    expected_sha = hashlib.sha256(data).hexdigest()

    result = await store.put(io.BytesIO(data))
    assert result.sha256 == expected_sha
    assert result.size == len(data)
    assert result.storage_key == f"blobs/{expected_sha[:2]}/{expected_sha}"
    assert result.deduplicated is False

    # round-trip
    chunks: list[bytes] = []
    async for c in store.get(result.sha256):
        chunks.append(c)
    assert b"".join(chunks) == data

    # 不存在 → KeyError
    missing = "9" * 64
    with pytest.raises(KeyError):
        async for _ in store.get(missing):
            break


@pytest.mark.asyncio
async def test_put_same_bytes_is_deduplicated(store: MinioBlobStore) -> None:
    data = b"dedup-payload-" + secrets.token_bytes(32)
    r1 = await store.put(io.BytesIO(data))
    assert r1.deduplicated is False

    r2 = await store.put(io.BytesIO(data))
    assert r2.sha256 == r1.sha256
    assert r2.storage_key == r1.storage_key
    assert r2.deduplicated is True

    # bucket 中只有一个 final 对象（_tmp/* 已被清理）
    raw = boto3.client(
        "s3",
        endpoint_url=_minio_endpoint() or "",
        aws_access_key_id=os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat"),
        aws_secret_access_key=os.environ.get(
            "DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret"
        ),
        region_name="us-east-1",
    )
    listing = raw.list_objects_v2(Bucket=store._bucket)  # type: ignore[attr-defined]
    keys = [o["Key"] for o in (listing.get("Contents") or [])]
    assert keys == [r1.storage_key]


@pytest.mark.asyncio
async def test_exists_true_and_false(store: MinioBlobStore) -> None:
    r = await store.put(io.BytesIO(b"exists-test"))
    assert await store.exists(r.sha256) is True
    assert await store.exists("0" * 64) is False


@pytest.mark.asyncio
async def test_get_size_true_and_none(store: MinioBlobStore) -> None:
    data = b"size-test-12345"
    r = await store.put(io.BytesIO(data))
    assert await store.get_size(r.sha256) == len(data)
    assert await store.get_size("0" * 64) is None


@pytest.mark.asyncio
async def test_put_large_object_streaming(store: MinioBlobStore) -> None:
    data = secrets.token_bytes(2 * 1024 * 1024 + 17)  # 2MB + 余量
    expected_sha = hashlib.sha256(data).hexdigest()

    r = await store.put(io.BytesIO(data))
    assert r.sha256 == expected_sha
    assert r.size == len(data)
    assert re.match(r"^blobs/[0-9a-f]{2}/[0-9a-f]{64}$", r.storage_key)

    # round-trip 大对象，逐 chunk 累计 hash 验证流式正确
    h = hashlib.sha256()
    total = 0
    async for c in store.get(r.sha256):
        h.update(c)
        total += len(c)
    assert h.hexdigest() == expected_sha
    assert total == len(data)
