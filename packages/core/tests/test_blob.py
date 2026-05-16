"""BlobRef：sha256 64-hex 校验 + round-trip。"""

from __future__ import annotations

import pytest
from dataplat_core.domain.blob import BlobRef
from pydantic import ValidationError


def test_blobref_roundtrip() -> None:
    b = BlobRef(sha256="a" * 64, size=1024, storage_key="blobs/aa/" + "a" * 64)
    assert BlobRef.model_validate_json(b.model_dump_json()) == b


def test_blobref_rejects_non_hex_sha256() -> None:
    with pytest.raises(ValidationError):
        BlobRef(sha256="z" * 64, size=10, storage_key="blobs/zz/z..")


def test_blobref_rejects_wrong_length_sha256() -> None:
    with pytest.raises(ValidationError):
        BlobRef(sha256="a" * 63, size=10, storage_key="blobs/aa/short")


def test_blobref_rejects_negative_size() -> None:
    with pytest.raises(ValidationError):
        BlobRef(sha256="a" * 64, size=-1, storage_key="blobs/aa/x")
