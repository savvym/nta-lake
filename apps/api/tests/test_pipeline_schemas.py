"""Recipe schema 单元测试（spec pipeline-orchestrator-mvp-20260518 T-7a，AC-1）。

4 用例：valid / missing required / invalid input ref / invalid output ref。
不依赖 PG / MinIO / Redis；纯 Pydantic 校验。
"""

from __future__ import annotations

import pytest
from dataplat_api.schemas.pipeline import (
    Recipe,
    RecipeNode,
    load_recipe,
)
from pydantic import ValidationError


def test_valid_recipe_minimal() -> None:
    r = Recipe(
        name="demo",
        nodes=[
            RecipeNode(
                id="n1",
                processor="markdown-normalize@0.1",
                inputs=["bronze/demo/raw@main"],
                config={},
                output="silver/demo/clean@auto",
            )
        ],
    )
    assert r.name == "demo"
    assert r.nodes[0].id == "n1"


def test_missing_required_field_raises() -> None:
    with pytest.raises(ValidationError):
        Recipe.model_validate({"name": "demo"})  # 缺 nodes


def test_invalid_input_ref_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        RecipeNode(
            id="n1",
            processor="p@1",
            inputs=["not-a-valid-ref"],
            config={},
            output="silver/demo/baz@auto",
        )


def test_invalid_output_ref_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        RecipeNode(
            id="n1",
            processor="p@1",
            inputs=["bronze/demo/raw@main"],
            config={},
            output="no-layer-prefix@main",
        )


def test_invalid_processor_ref_raises() -> None:
    with pytest.raises(ValidationError):
        RecipeNode(
            id="n1",
            processor="missing-version-marker",
            inputs=["bronze/demo/raw@main"],
            config={},
            output="silver/demo/baz@auto",
        )


def test_load_recipe_from_yaml_text() -> None:
    yaml_text = """
name: demo
nodes:
  - id: n1
    processor: markdown-normalize@0.1
    inputs:
      - bronze/demo/raw@main
    config: {}
    output: silver/demo/clean@auto
"""
    r = load_recipe(yaml_text)
    assert r.name == "demo"
    assert r.nodes[0].id == "n1"


def test_load_recipe_from_dict() -> None:
    data = {
        "name": "demo",
        "nodes": [
            {
                "id": "n1",
                "processor": "markdown-normalize@0.1",
                "inputs": ["bronze/demo/raw@main"],
                "config": {},
                "output": "silver/demo/clean@auto",
            }
        ],
    }
    r = load_recipe(data)
    assert r.name == "demo"
