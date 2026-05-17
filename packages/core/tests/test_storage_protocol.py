"""BlobStore Protocol + BlobPutResult 单元测试。

不依赖 MinIO；仅校验 Protocol / BaseModel 形态。
"""

from __future__ import annotations

from typing import Protocol

import pytest
from dataplat_core.protocols.storage import BlobPutResult, BlobStore
from pydantic import BaseModel, ValidationError


def test_blobstore_is_runtime_checkable_protocol() -> None:
    assert issubclass(BlobStore, Protocol)
    # runtime_checkable 装饰器会设 _is_runtime_protocol=True
    assert getattr(BlobStore, "_is_runtime_protocol", False) is True


def test_blobput_result_roundtrip() -> None:
    r = BlobPutResult(
        sha256="a" * 64,
        size=42,
        storage_key="blobs/aa/" + "a" * 64,
        deduplicated=False,
    )
    j = r.model_dump_json()
    assert BlobPutResult.model_validate_json(j) == r
    assert issubclass(BlobPutResult, BaseModel)


def test_blobput_result_storage_key_matches_helper() -> None:
    from dataplat_api.storage.keys import storage_key_for

    sha = "b" * 64
    r = BlobPutResult(
        sha256=sha,
        size=0,
        storage_key=storage_key_for(sha),
        deduplicated=True,
    )
    assert r.storage_key == f"blobs/bb/{sha}"


def test_blobput_result_rejects_negative_size() -> None:
    with pytest.raises(ValidationError):
        BlobPutResult(
            sha256="c" * 64,
            size=-1,
            storage_key="blobs/cc/x",
            deduplicated=False,
        )
