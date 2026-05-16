"""Repository round-trip + 分层 Subtype Literal 严格校验。"""

from __future__ import annotations

import pytest
from dataplat_core.domain.repository import Repository
from pydantic import ValidationError


def test_repository_roundtrip_bronze() -> None:
    r = Repository(
        id="r1",
        owner="cn-lit",
        name="honglou",
        layer="bronze",
        subtype="book",
        visibility="internal",
    )
    j = r.model_dump_json()
    assert Repository.model_validate_json(j) == r


def test_repository_subtype_literal_rejects_unknown() -> None:
    with pytest.raises(ValidationError):
        Repository(
            id="r2",
            owner="o",
            name="n",
            layer="bronze",
            subtype="bogus-subtype",  # 非 BronzeSubtype 列表中的值
            visibility="private",
        )


def test_repository_layer_literal_rejects_unknown() -> None:
    with pytest.raises(ValidationError):
        Repository(
            id="r3",
            owner="o",
            name="n",
            layer="invalid-layer",  # 非 bronze/silver/gold
            subtype="pdf",
            visibility="private",
        )


def test_repository_silver_subtype_accepted() -> None:
    r = Repository(
        id="r4",
        owner="x",
        name="y",
        layer="silver",
        subtype="text-corpus",
        visibility="private",
    )
    assert r.subtype == "text-corpus"


def test_repository_gold_subtype_accepted() -> None:
    r = Repository(
        id="r5",
        owner="x",
        name="y",
        layer="gold",
        subtype="sft",
        visibility="public",
    )
    assert r.subtype == "sft"
