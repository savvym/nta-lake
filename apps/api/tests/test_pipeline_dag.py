"""DAG 拓扑排序 + 环检测（spec pipeline-orchestrator-mvp-20260518 T-7a，AC-2）。

5 用例：linear / branching-merge / cycle raise / unknown deps / build_node_deps。
"""

from __future__ import annotations

import pytest
from dataplat_api.runner.dag import build_node_deps, topo_sort
from dataplat_api.schemas.pipeline import Recipe, RecipeNode


def test_topo_sort_linear() -> None:
    out = topo_sort(
        [
            {"id": "a", "deps": []},
            {"id": "b", "deps": ["a"]},
            {"id": "c", "deps": ["b"]},
        ]
    )
    assert out == ["a", "b", "c"]


def test_topo_sort_branching_merge() -> None:
    out = topo_sort(
        [
            {"id": "a", "deps": []},
            {"id": "b", "deps": ["a"]},
            {"id": "c", "deps": ["a"]},
            {"id": "d", "deps": ["b", "c"]},
        ]
    )
    # 'a' 必须在最前；'d' 必须在最后；b/c 顺序按输入稳定
    assert out[0] == "a"
    assert out[-1] == "d"
    assert set(out[1:3]) == {"b", "c"}


def test_topo_sort_cycle_raises() -> None:
    with pytest.raises(ValueError, match="cycle"):
        topo_sort(
            [
                {"id": "a", "deps": ["b"]},
                {"id": "b", "deps": ["a"]},
            ]
        )


def test_topo_sort_unknown_deps_raises() -> None:
    with pytest.raises(ValueError, match="未知 deps"):
        topo_sort(
            [
                {"id": "a", "deps": ["ghost"]},
            ]
        )


def test_topo_sort_duplicate_id_raises() -> None:
    with pytest.raises(ValueError, match="重复"):
        topo_sort(
            [
                {"id": "a", "deps": []},
                {"id": "a", "deps": []},
            ]
        )


def test_build_node_deps_extracts_node_refs() -> None:
    recipe = Recipe(
        name="demo",
        nodes=[
            RecipeNode(
                id="a",
                processor="markdown-normalize@0.1",
                inputs=["bronze/demo/raw@main"],
                config={},
                output="silver/demo/out@auto",
            ),
            RecipeNode(
                id="b",
                processor="markdown-normalize@0.1",
                inputs=["@a"],
                config={},
                output="silver/demo/out2@auto",
            ),
        ],
    )
    deps = build_node_deps(recipe)
    assert deps == [
        {"id": "a", "deps": []},
        {"id": "b", "deps": ["a"]},
    ]
