"""Recipe v2：v2 schema（1 Loader + N Operators）+ 解析器 + 执行器。

按 .harness/design.md § W2-5：Recipe v2 是 Silver 层算子链的核心编排抽象。
  - v1（apps/api/dataplat_api/schemas/pipeline.py）是 DAG-based pipeline，不动。
  - v2（本文件）是线性 loader + operator 链，专为训练数据 silver 层优化。

导出：
    RecipeLoaderSpec    — Loader 配置 spec（含 input: dict）
    RecipeOperatorSpec  — Operator 配置 spec
    RecipeV2            — 完整 v2 Recipe schema
    RecipeRunResult     — 执行结果（rows + 统计 + loader notes）
    load_recipe_v2      — yaml str / dict → RecipeV2 解析器
    run_recipe_v2       — RecipeV2 + RunContext → RecipeRunResult 执行器（async，W4-7 埋点）
"""

from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from dataplat_core.loaders.registry import LoaderRegistry
from dataplat_core.metrics import get_metrics_registry
from dataplat_core.operators import OperatorRegistry
from dataplat_core.protocols.loader import LoadResult, SilverRow
from dataplat_core.protocols.runcontext import RunContext

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class RecipeLoaderSpec(BaseModel):
    """Loader 配置描述。

    - `name`：LoaderRegistry 中已注册的 Loader 名称。
    - `config`：透传给 Loader.load() 的配置 dict。
    - `input`：输入参数 dict；`blob_sha` key 必须存在（executor 读取时 KeyError 兜底）。
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    config: dict[str, Any] = {}
    input: dict[str, Any]


class RecipeOperatorSpec(BaseModel):
    """Operator 配置描述。

    - `name`：OperatorRegistry 中已注册的 Operator 名称。
    - `config`：透传给 Operator.run() 的配置 dict。
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    config: dict[str, Any] = {}


class RecipeV2(BaseModel):
    """Recipe v2 完整 schema：1 Loader + N Operators 线性链。

    - `name`：Recipe 名称，非空字符串。
    - `version`：必须为字面量 2（显式 versioning，拒绝 v1 yaml）。
    - `loader`：Loader 配置 spec。
    - `operators`：Operator 配置列表（默认空，即仅跑 Loader）。
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    version: Literal[2]
    loader: RecipeLoaderSpec
    operators: list[RecipeOperatorSpec] = []


# ---------------------------------------------------------------------------
# RecipeRunResult
# ---------------------------------------------------------------------------


class RecipeRunResult(BaseModel):
    """run_recipe_v2 的执行结果汇总。

    - `rows`：Operator 链执行后的 Silver row 列表。
    - `total_input`：Loader 产出的初始 row 数（operator 链执行前）。
    - `total_output`：Operator 链执行后的最终 row 数。
    - `loader_notes`：Loader 返回的附加说明（如有）。
    """

    model_config = ConfigDict(extra="forbid")

    rows: list[SilverRow]
    total_input: int
    total_output: int
    loader_notes: str | None = None


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def load_recipe_v2(data: str | dict[str, Any]) -> RecipeV2:
    """将 yaml 字符串或已解析的 dict 解析为 RecipeV2 对象。

    Args:
        data: yaml str 或顶层 dict。str 会先经 yaml.safe_load 转换。

    Returns:
        验证通过的 RecipeV2 实例。

    Raises:
        ValueError: 顶层不是 mapping；或 version 字段缺失 / != 2（v1 yaml 被拒）。
        pydantic.ValidationError: RecipeV2 schema 校验失败（extra key / 类型错误等）。
    """
    if isinstance(data, str):
        parsed: Any = yaml.safe_load(data)
        if not isinstance(parsed, dict):
            raise ValueError("recipe yaml 顶层必须是 mapping (dict)")
        data = parsed

    # 检查 version 字段：缺失或不等于 2 时给出友好错误信息
    version = data.get("version")
    if version != 2:
        raise ValueError("recipe v1 deprecated; please use v2 (version: 2)")

    return RecipeV2.model_validate(data)


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------


async def run_recipe_v2(recipe: RecipeV2, ctx: RunContext) -> RecipeRunResult:
    """在进程内异步执行 RecipeV2：Loader → Operator 链 → RecipeRunResult。

    执行步骤（严格按 design.md §run_recipe_v2）：
      1. 从 LoaderRegistry 查找 Loader 类。
      2. 实例化 Loader。
      3. 从 recipe.loader.input 取 blob_sha（缺失 → KeyError，expected v1 行为）。
      4. 调用 loader.load(blob_sha, config, ctx)，得 LoadResult。
      5. 展开 rows 列表，记录 total_input。
      6. 逐个 Operator：从 OperatorRegistry 查找 → 实例化 → 对每行调用 run()，
         并向 MetricsRegistry 记录 rows_in / rows_out / duration_ms / error。
      7. 返 RecipeRunResult。

    改为 async（W4-7）：支持 await registry.record_op_run（asyncio.Lock）。

    Args:
        recipe: 已通过 load_recipe_v2 验证的 RecipeV2 实例。
        ctx:    运行时上下文（RunContext Protocol 实现）。

    Returns:
        RecipeRunResult，包含最终 rows + 统计信息。

    Raises:
        KeyError: Loader / Operator 未注册；或 blob_sha 缺失；或 Operator config 缺必填 key。
    """
    registry = get_metrics_registry()

    # 步骤 1：查找 Loader 类
    loader_cls = LoaderRegistry.get(recipe.loader.name)

    # 步骤 2：实例化 Loader
    loader = loader_cls()

    # 步骤 3：取 blob_sha（缺失 → KeyError）
    blob_sha: str = recipe.loader.input["blob_sha"]

    # 步骤 4：调用 Loader.load
    load_result: LoadResult = loader.load(blob_sha, recipe.loader.config, ctx)

    # 步骤 5：展开 rows，记录 total_input
    rows: list[SilverRow] = list(load_result.rows)
    total_input = len(rows)

    # 步骤 6：逐个执行 Operator（埋点：error=True 先记再 raise）
    for op_spec in recipe.operators:
        op_cls = OperatorRegistry.get(op_spec.name)
        op = op_cls()
        new_rows: list[SilverRow] = []
        rows_in_count = len(rows)
        t0 = perf_counter()
        try:
            for row in rows:
                result = op.run(row, op_spec.config, ctx)
                if asyncio.iscoroutine(result):
                    result = await result
                new_rows.extend(result)
        except Exception:
            duration_ms = (perf_counter() - t0) * 1000
            await registry.record_op_run(op_spec.name, rows_in_count, 0, duration_ms, error=True)
            raise
        duration_ms = (perf_counter() - t0) * 1000
        await registry.record_op_run(op_spec.name, rows_in_count, len(new_rows), duration_ms)
        rows = new_rows

    # 步骤 7：返回结果
    return RecipeRunResult(
        rows=rows,
        total_input=total_input,
        total_output=len(rows),
        loader_notes=load_result.notes,
    )
