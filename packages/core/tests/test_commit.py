"""Commit：含 Lineage 嵌入 + parents 列表 + hash 校验。"""

from __future__ import annotations

import pytest
from dataplat_core.domain.commit import Commit
from dataplat_core.domain.lineage import InputRef, Lineage, ProducedBy
from pydantic import ValidationError


def test_commit_root_no_parents_no_lineage() -> None:
    c = Commit(hash="a" * 64, repo_id="r1", tree_hash="b" * 64, parents=[], author_id="u1")
    assert c.parents == []
    assert c.lineage is None


def test_commit_with_lineage_embedded() -> None:
    pb = ProducedBy(kind="processor", name="x", version="0.1", config_hash="c" * 64)
    inp = InputRef(repo="bronze/x/y", commit="d" * 64)
    lineage = Lineage(produced_by=pb, inputs=[inp], run_id="run-1", env={})

    c = Commit(
        hash="e" * 64,
        repo_id="r1",
        tree_hash="f" * 64,
        parents=["d" * 64],
        author_id="u1",
        message="initial normalize",
        lineage=lineage,
    )

    j = c.model_dump_json()
    parsed = Commit.model_validate_json(j)
    assert parsed.lineage is not None
    assert parsed.lineage.produced_by.kind == "processor"
    assert parsed.lineage.inputs[0].repo == "bronze/x/y"


def test_commit_hash_rejects_invalid_hex() -> None:
    with pytest.raises(ValidationError):
        Commit(hash="g" * 64, repo_id="r1", tree_hash="b" * 64, parents=[], author_id="u1")
