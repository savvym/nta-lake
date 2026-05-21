"""Recipe v2 行为测试 (W2-5，AC-1..AC-4)。

- AC-1: load_recipe_v2 接受合规 v2 yaml str
- AC-2: load_recipe_v2 拒绝 v1 yaml（缺 version / version != 2）
- AC-3: run_recipe_v2 端到端：stub loader + [filter, chunker, snapshot_tag] chain
- AC-4: run_recipe_v2 空 operators 列表：rows 即 loader 原样输出

stub 说明：_StubRecipeV2Loader 在本文件 inline 定义并注册到 LoaderRegistry，
避免污染生产注册表；try/except ValueError 容错多次 import 场景（与 W2-1 同模式）。
"""

from __future__ import annotations

import pytest
from dataplat_core.loaders.registry import LoaderRegistry
from dataplat_core.protocols.loader import LoadResult, SilverRow

# ---------------------------------------------------------------------------
# Stub Loader（test 内 inline 定义 + 注册）
# ---------------------------------------------------------------------------


class _StubRecipeV2Loader:
    """测试用 stub Loader：返一个固定 SilverRow（text 150 chars）。"""

    name = "test-loader-recipe-v2"
    version = "1.0"
    input_subtype = "txt"
    output_schema_id = "silver-text-v1"

    def load(self, blob_sha: str, config: dict, ctx: object) -> LoadResult:
        """返回含 150 字符 text 的单行 LoadResult。"""
        text = "x" * 150  # 150 chars，确保 filter(min_chars=50) 通过 + chunker(max_chars=100) 拆为 2 块
        row = SilverRow(
            text=text,
            source_ref={"blob_sha": blob_sha, "loader": "test-loader-recipe-v2"},
        )
        return LoadResult(rows=[row], total_count=1, notes="stub")


try:
    LoaderRegistry.register("test-loader-recipe-v2", _StubRecipeV2Loader)
except ValueError:
    pass  # 模块重复 import 场景（与 W2-1..W2-4 自注册同模式）


# ---------------------------------------------------------------------------
# 辅助：最简 RunContext stub
# ---------------------------------------------------------------------------

from types import SimpleNamespace


def _make_ctx() -> object:
    """返一个满足 RunContext Protocol duck-typing 的 SimpleNamespace。"""
    return SimpleNamespace(logger=None, metrics=None, secrets=None, cancel_event=None, llm=None)


# ---------------------------------------------------------------------------
# AC-1: load_recipe_v2 解析合规 v2 yaml str
# ---------------------------------------------------------------------------


def test_load_recipe_v2_valid() -> None:
    """AC-1: load_recipe_v2 接受合规 v2 yaml str（含 1 loader + 3 operators），返 RecipeV2 对象。

    断言：name / version / loader.name / operators 字段正确。
    """
    from dataplat_core.recipe import RecipeV2, load_recipe_v2

    yaml_str = """\
name: test-recipe-valid
version: 2
loader:
  name: test-loader-recipe-v2
  config:
    some_key: some_val
  input:
    blob_sha: "abc123"
operators:
  - name: filter
    config:
      min_chars: 50
  - name: chunker
    config:
      max_chars: 100
  - name: snapshot_tag
    config:
      snapshot_name: test-snap
"""
    recipe = load_recipe_v2(yaml_str)

    assert isinstance(recipe, RecipeV2)
    assert recipe.name == "test-recipe-valid"
    assert recipe.version == 2
    assert recipe.loader.name == "test-loader-recipe-v2"
    assert len(recipe.operators) == 3
    assert recipe.operators[0].name == "filter"
    assert recipe.operators[1].name == "chunker"
    assert recipe.operators[2].name == "snapshot_tag"


# ---------------------------------------------------------------------------
# AC-2: load_recipe_v2 拒绝 v1 yaml（缺 version / version != 2）
# ---------------------------------------------------------------------------


def test_load_recipe_v2_rejects_v1() -> None:
    """AC-2: load_recipe_v2 拒绝缺 version 或 version != 2 的 yaml；抛 ValueError 含 "v1 deprecated"。

    两个 case：
      a) v1 yaml 无 version 字段（原始 v1 格式：name + nodes）
      b) v1 yaml 显式 version: 1
    """
    from dataplat_core.recipe import load_recipe_v2

    # case a：缺 version 字段
    yaml_no_version = "name: x\nnodes: []\n"
    with pytest.raises(ValueError, match="v1 deprecated"):
        load_recipe_v2(yaml_no_version)

    # case b：version: 1（显式 v1）
    yaml_version_1 = """\
name: old-recipe
version: 1
nodes: []
"""
    with pytest.raises(ValueError, match="v1 deprecated"):
        load_recipe_v2(yaml_version_1)


# ---------------------------------------------------------------------------
# AC-3: run_recipe_v2 端到端：stub loader + [filter, chunker, snapshot_tag]
# ---------------------------------------------------------------------------


async def test_run_recipe_v2_end_to_end() -> None:
    """AC-3: run_recipe_v2 端到端验证（改为 async 支持 await，W4-7）。

    Operator chain：filter(min_chars=50) → chunker(max_chars=100) → snapshot_tag(snapshot_name="test-snap")

    stub loader 返 1 row，text = 150 chars：
      - filter(min_chars=50)：150 >= 50 → 通过，1 row
      - chunker(max_chars=100)：150 chars / 100 = 2 chunks → 2 rows
      - snapshot_tag：给每行打标，仍 2 rows

    期望：
      - total_input == 1（loader 产出）
      - total_output == 2（chain 后）
      - 每行 lineage_ops 含 3 个 op 记录（filter / chunker / snapshot_tag）
    """
    from dataplat_core.metrics import reset_metrics_registry
    from dataplat_core.recipe import RecipeLoaderSpec, RecipeOperatorSpec, RecipeV2, run_recipe_v2

    reset_metrics_registry()

    recipe = RecipeV2(
        name="test-e2e",
        version=2,
        loader=RecipeLoaderSpec(
            name="test-loader-recipe-v2",
            config={},
            input={"blob_sha": "deadbeef" * 8},
        ),
        operators=[
            RecipeOperatorSpec(name="filter", config={"min_chars": 50}),
            RecipeOperatorSpec(name="chunker", config={"max_chars": 100}),
            RecipeOperatorSpec(name="snapshot_tag", config={"snapshot_name": "test-snap"}),
        ],
    )

    ctx = _make_ctx()
    result = await run_recipe_v2(recipe, ctx)  # type: ignore[arg-type]

    # 总量断言
    assert result.total_input == 1, f"total_input 期望 1，实得 {result.total_input}"
    assert result.total_output == 2, f"total_output 期望 2，实得 {result.total_output}"
    assert len(result.rows) == 2

    # 每行 lineage_ops 含 3 个 op
    for row in result.rows:
        op_names = [entry["op"] for entry in row.lineage_ops]
        assert "filter" in op_names, f"lineage_ops 缺 filter：{op_names}"
        assert "chunker" in op_names, f"lineage_ops 缺 chunker：{op_names}"
        assert "snapshot_tag" in op_names, f"lineage_ops 缺 snapshot_tag：{op_names}"
        assert len(row.lineage_ops) == 3, f"lineage_ops 期望 3 项，实得 {len(row.lineage_ops)}: {row.lineage_ops}"

    # loader_notes 透传
    assert result.loader_notes == "stub"


# ---------------------------------------------------------------------------
# AC-4: run_recipe_v2 空 operators 列表
# ---------------------------------------------------------------------------


async def test_run_recipe_v2_empty_operators() -> None:
    """AC-4: run_recipe_v2 空 operators → rows 即 loader 原样输出；total_input == total_output；lineage_ops 不被追加。"""
    from dataplat_core.metrics import reset_metrics_registry
    from dataplat_core.recipe import RecipeLoaderSpec, RecipeV2, run_recipe_v2

    reset_metrics_registry()

    recipe = RecipeV2(
        name="test-empty-ops",
        version=2,
        loader=RecipeLoaderSpec(
            name="test-loader-recipe-v2",
            config={},
            input={"blob_sha": "cafebabe" * 8},
        ),
        operators=[],  # 空 operator 列表
    )

    ctx = _make_ctx()
    result = await run_recipe_v2(recipe, ctx)  # type: ignore[arg-type]

    assert result.total_input == 1
    assert result.total_output == 1
    assert result.total_input == result.total_output
    assert len(result.rows) == 1

    # stub loader 返的 row 没有 lineage_ops，空 operators 不追加任何记录
    assert result.rows[0].lineage_ops == [], f"期望 lineage_ops 为空，实得 {result.rows[0].lineage_ops}"


# ---------------------------------------------------------------------------
# AC-5（W4-7）: run_recipe_v2 埋点测试
# ---------------------------------------------------------------------------


async def test_run_recipe_v2_records_metrics() -> None:
    """AC-3(W4-7): run_recipe_v2 跑 [filter, chunker] → snapshot 含 2 operator entry + rows_in/out 正确。

    stub loader 返 1 row（text=150 chars）：
      - filter(min_chars=50)：rows_in=1, rows_out=1（150 >= 50 通过）
      - chunker(max_chars=100)：rows_in=1, rows_out=2（150 chars → 2 chunks）
    """
    from dataplat_core.metrics import get_metrics_registry, reset_metrics_registry
    from dataplat_core.recipe import RecipeLoaderSpec, RecipeOperatorSpec, RecipeV2, run_recipe_v2

    reset_metrics_registry()

    recipe = RecipeV2(
        name="test-metrics",
        version=2,
        loader=RecipeLoaderSpec(
            name="test-loader-recipe-v2",
            config={},
            input={"blob_sha": "aabbccdd" * 8},
        ),
        operators=[
            RecipeOperatorSpec(name="filter", config={"min_chars": 50}),
            RecipeOperatorSpec(name="chunker", config={"max_chars": 100}),
        ],
    )

    ctx = _make_ctx()
    result = await run_recipe_v2(recipe, ctx)  # type: ignore[arg-type]

    # 基本执行结果
    assert result.total_input == 1
    assert result.total_output == 2

    # metrics snapshot 检查
    registry = get_metrics_registry()
    snaps = registry.snapshot()
    assert len(snaps) == 2, f"期望 2 个 operator metrics entry，实得 {len(snaps)}"

    # 按字母序：chunker < filter
    names = [s.operator_name for s in snaps]
    assert names == ["chunker", "filter"], f"期望 ['chunker', 'filter']，实得 {names}"

    # filter：rows_in=1, rows_out=1（150 chars 通过 min_chars=50）
    filter_snap = next(s for s in snaps if s.operator_name == "filter")
    assert filter_snap.runs == 1
    assert filter_snap.rows_in == 1
    assert filter_snap.rows_out == 1
    assert filter_snap.errors == 0

    # chunker：rows_in=1, rows_out=2（150 chars / max_chars=100 → 2 chunks）
    chunker_snap = next(s for s in snaps if s.operator_name == "chunker")
    assert chunker_snap.runs == 1
    assert chunker_snap.rows_in == 1
    assert chunker_snap.rows_out == 2
    assert chunker_snap.errors == 0
