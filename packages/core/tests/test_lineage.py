"""Lineage / ProducedBy / InputRef：kind Literal + config_hash 64-hex 校验。"""

from __future__ import annotations

import pytest
from dataplat_core.domain.lineage import InputRef, Lineage, ProducedBy
from pydantic import ValidationError


def test_lineage_with_processor_produced_by() -> None:
    pb = ProducedBy(kind="processor", name="llm-qa-gen", version="0.5", config_hash="c" * 64)
    inp = InputRef(repo="silver/cn-lit/normalized-text-v1", commit="a" * 64)
    lineage = Lineage(produced_by=pb, inputs=[inp], run_id="r1", env={"python": "3.11"})
    assert lineage.produced_by.kind == "processor"
    assert len(lineage.produced_by.config_hash) == 64
    assert all(c in "0123456789abcdef" for c in lineage.produced_by.config_hash)


def test_lineage_produced_by_kind_literal_rejects_unknown() -> None:
    with pytest.raises(ValidationError):
        ProducedBy(kind="bot", name="x", version="0.1", config_hash="a" * 64)


def test_lineage_config_hash_rejects_prefix() -> None:
    with pytest.raises(ValidationError):
        ProducedBy(
            kind="adapter",
            name="x",
            version="0.1",
            config_hash="sha256:" + "a" * 56,  # 含前缀，违反"纯 64-hex"
        )


def test_lineage_adapter_empty_inputs() -> None:
    pb = ProducedBy(kind="adapter", name="upload", version="1.0", config_hash="a" * 64)
    lineage = Lineage(produced_by=pb, inputs=[], run_id="r2", env={})
    assert lineage.inputs == []
