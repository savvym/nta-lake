---
change_id: operator-eval-gen-20260520
phase: implementation
status: done
authored_at: 2026-05-21T15:10:00Z
author: sonnet-phase2-implementer
model_used: claude-sonnet-4-6
branch: change/operator-eval-gen-20260520
base_commit: 5d1a097
head_commit: cd7fc47
pr_url: n/a (no push requested)
---

# Implementation：operator-eval-gen (W4-8)

> Phase 2 sonnet 端到端产物。一次 sonnet 调用内完成：编码 + 单元测试 + 端到端验证 + commit。

## 改动文件清单

执行 `git diff --name-only main...HEAD`：

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `packages/core/src/dataplat_core/operators/eval_gen.py` | new | EvalGenOperator（async run；short skip / parse failure / lineage / stats） |
| `packages/core/src/dataplat_core/protocols/operator.py` | edit | Operator Protocol docstring +4 行 sync/async union 说明 |
| `packages/core/src/dataplat_core/recipe.py` | edit | `import asyncio` + operator 循环加 `iscoroutine` 分支支持 async operator |
| `packages/core/src/dataplat_core/operators/__init__.py` | edit | export EvalGenOperator + 注册（共 10 个内置算子） |
| `packages/core/tests/test_operator_eval_gen.py` | new | 5 tests（happy/short_skip/parse_fail/fence/invalid_answer） |
| `packages/core/tests/test_recipe_v2.py` | edit | +1 test：`test_run_recipe_v2_supports_async_operator` |
| `packages/core/tests/test_image_to_text_suite.py` | edit | `len==9` → `>=9`（反脆弱修正，DEV-1） |

## 测试通过证据

### AC-1：EvalGenOperator 注册存在

```
$ cd packages/core && uv run python -c "from dataplat_core.operators.registry import OperatorRegistry; from dataplat_core.operators.eval_gen import EvalGenOperator; assert OperatorRegistry.get('eval_gen') is EvalGenOperator; print('OK')"
OK
```

### AC-2：eval_gen 5 行为测试

```
$ cd packages/core && uv run pytest tests/test_operator_eval_gen.py -x -q
.....
5 passed in 0.14s
```

### AC-3：run_recipe_v2 支持 async operator

```
$ cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_supports_async_operator -x -q
.
1 passed in 0.15s
```

### AC-4：packages/core 全量基线无回归

```
$ cd packages/core && uv run pytest -x -q
........................................................................
....................................
108 passed in 1.34s
```

### apps/api 无回归

```
$ cd apps/api && uv run pytest -x -q
51 passed, 131 skipped in 1.86s
```

## 偏离 design.md

| # | 偏离点 | 原因 | 类型 |
|---|---|---|---|
| DEV-1 | `test_image_to_text_suite.py` `len(names)==9` 改为 `>=9` | 新增第 10 个算子后该硬编码断言必然失败；per harness memory "Registry 测试禁用 len==N 总数断言"，就地修为 `>=9`；非新 change 改原测试而是反脆弱修复 | 必要副作用（design 漏点：未提及上游脆弱断言需同步更新） |

## 实现说明

### 关键实现细节

1. **async def run**：`eval_gen.py` 直接 `await ctx.llm.call(req)`
2. **iscoroutine 分支**：`recipe.py` 加 5 行：`result = op.run(...); if asyncio.iscoroutine(result): result = await result; new_rows.extend(result)`
3. **markdown fence 剥离**：`_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)` 匹配 ` ```json ` 和 ` ``` ` 两种形态
4. **parse failure 降级**：`_parse_eval_item` 返 `None` 时写 `{"error": "parse_failed", "raw": resp.text[:200]}`；`eval_gen_parse_errors += 1`；不抛
5. **lang 读取**：从 `row.stats.get("lang") or getattr(row, "lang", None) or "unknown"`（SilverRow 无 lang 字段，兼容处理）
6. **注册**：`eval_gen.py` 末尾 `try: OperatorRegistry.register(...) except ValueError: pass`；`__init__.py` 循环注册也含 `eval_gen`（双重容错）

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 AC。
