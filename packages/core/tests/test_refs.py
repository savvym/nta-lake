"""Ref：name pattern + commit_hash 64-hex 校验。"""

from __future__ import annotations

import pytest
from dataplat_core.domain.refs import Ref
from pydantic import ValidationError


def test_ref_basic() -> None:
    r = Ref(repo_id="r1", name="main", commit_hash="a" * 64)
    assert r.name == "main"


def test_ref_versioned_name() -> None:
    r = Ref(repo_id="r1", name="v1.0", commit_hash="a" * 64)
    assert r.name == "v1.0"


def test_ref_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        Ref(repo_id="r1", name="", commit_hash="a" * 64)


def test_ref_rejects_invalid_commit_hash() -> None:
    with pytest.raises(ValidationError):
        Ref(repo_id="r1", name="main", commit_hash="not-a-hash")
