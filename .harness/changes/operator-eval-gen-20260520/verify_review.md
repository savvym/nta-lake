---
change_id: operator-eval-gen-20260520
phase: verify
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: 2026-05-21T15:40:00Z
verdict: APPROVED
---

# Verify Review：operator-eval-gen (W4-8)

> Phase 3 opus reviewer 产物。对照 design.md + implementation.md + `git diff $(git merge-base main HEAD)..HEAD` 真跑验 PR。

## 输入

- **Design**：`.harness/changes/operator-eval-gen-20260520/design.md`（commit `a512853`）
- **Implementation**：`.harness/changes/operator-eval-gen-20260520/implementation.md`（commit `4f3b59c`）
- **Git base**：`$(git merge-base main HEAD)` = `a8390b4`（W4-7 merge commit `5d1a097` 的祖先 main HEAD）
- **Branch**：`change/operator-eval-gen-20260520`
- **Head commits**:
  - `a512853` design(operator-eval-gen-20260520): W4-8 mini-design
  - `cd7fc47` feat(operator-eval-gen): W4-8 EvalGenOperator + async recipe support
  - `4f3b59c` docs(impl.md): W4-8 implementation.md backfill
  - `a481d21` fix(W4-8): remove unused imports (asyncio in eval_gen.py, pytest in test_operator_eval_gen.py)

## AC 对照表

每条 AC 真跑 reviewer 自己执行的命令：

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL |
|---|---|---|---|---|
| AC-1 | static | `cd packages/core && uv run python -c "from dataplat_core.operators.registry import OperatorRegistry; from dataplat_core.operators.eval_gen import EvalGenOperator; assert OperatorRegistry.get('eval_gen') is EvalGenOperator; print('OK')"` | `OK` | **PASS** |
| AC-2 | behavioral | `cd packages/core && uv run pytest tests/test_operator_eval_gen.py -x -q` | `5 passed in 0.12s` | **PASS** |
| AC-3 | behavioral | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_supports_async_operator -x -q` | `1 passed in 0.12s` | **PASS** |
| AC-4 | behavioral | `cd packages/core && uv run pytest -x -q` | `108 passed in 1.34s`（≥ 108 ✅；102 基线 + 6 new = 5 eval_gen + 1 recipe_v2 async） | **PASS** |

## 机械化检查日志

```text
$ cd packages/core && uv run python -c "from dataplat_core.operators.registry import OperatorRegistry; \
    from dataplat_core.operators.eval_gen import EvalGenOperator; \
    assert OperatorRegistry.get('eval_gen') is EvalGenOperator; print('OK')"
OK

$ cd packages/core && uv run pytest tests/test_operator_eval_gen.py -x -q
.....                                                                    [100%]
5 passed in 0.12s

$ cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_supports_async_operator -x -q
.                                                                        [100%]
1 passed in 0.12s

$ cd packages/core && uv run pytest -x -q
........................................................................ [ 66%]
....................................                                     [100%]
108 passed in 1.34s

$ cd apps/api && uv run pytest -x -q
ssssssssssssssssssssssssssssssss..ssss.sssssssssssssssssssssssssssss.... [ 39%]
.s.......sssssssss.......................s....ssssss.......ssssssss..sss [ 79%]
ssssssssssssssssssssssssssssssssssssss                                   [100%]
51 passed, 131 skipped in 1.85s

$ git log --oneline $(git merge-base main HEAD)..HEAD
a481d21 fix(W4-8): remove unused imports (asyncio in eval_gen.py, pytest in test_operator_eval_gen.py)
4f3b59c docs(impl.md): W4-8 implementation.md backfill
cd7fc47 feat(operator-eval-gen): W4-8 EvalGenOperator + async recipe support
a512853 design(operator-eval-gen-20260520): W4-8 mini-design

$ git diff $(git merge-base main HEAD)..HEAD --stat
 .../changes/operator-eval-gen-20260520/design.md   | 172 +++++++++++++
 .../operator-eval-gen-20260520/implementation.md   |  92 +++++++
 .../core/src/dataplat_core/operators/__init__.py   |   6 +-
 .../core/src/dataplat_core/operators/eval_gen.py   | 265 +++++++++++++++++++++
 .../core/src/dataplat_core/protocols/operator.py   |   4 +
 packages/core/src/dataplat_core/recipe.py          |   6 +-
 packages/core/tests/test_image_to_text_suite.py    |   2 +-
 packages/core/tests/test_operator_eval_gen.py      | 245 +++++++++++++++++++
 packages/core/tests/test_recipe_v2.py              |  81 +++++++
 9 files changed, 870 insertions(+), 3 deletions(-)
```

## Scope-creep 检查

Design "应当不动"（design.md §交叉引用清单）逐项核查：

| 文件 | design 期望 | 实际 diff | 结论 |
|---|---|---|---|
| `apps/api/dataplat_api/llm/gateway.py`（W4-5 产物） | 不动 | `git diff` 0 行 | ✅ |
| `apps/api/dataplat_api/llm/cost.py`（W4-5 产物） | 不动 | `git diff` 0 行 | ✅ |
| `packages/core/src/dataplat_core/protocols/llm.py` | 不动（仅引用） | 0 行 | ✅ |
| `packages/core/src/dataplat_core/protocols/loader.py::SilverRow` | 不动（仅引用） | 0 行 | ✅ |
| `packages/core/src/dataplat_core/protocols/runcontext.py` | 不动（仅引用） | 0 行 | ✅ |
| `packages/core/src/dataplat_core/operators/registry.py` | 不动（仅引用模式） | 0 行 | ✅ |
| `packages/core/src/dataplat_core/operators/score.py` | 不动（结构参考） | 0 行 | ✅ |
| W1..W4-7 已 merged 产物 | 不动，除 protocols/operator.py +注释 / recipe.py +5 行 | 仅 protocols/operator.py +4 行注释；recipe.py +6 行（含 `import asyncio` + 5 行循环改造）；其他 W1..W4-7 文件全 0 行 | ✅ 与 design 一致 |
| apps/web | 不动 | 0 行 | ✅ |
| apps/api/dataplat_api | 不动（worker/orchestrator 留 follow-up） | 0 行 | ✅ |

**新增/编辑文件**全部在 design.md §范围 In scope 内：

- `eval_gen.py`（new）— 算子主体 ✅
- `protocols/operator.py` +4 行注释 — design 明示 ✅
- `recipe.py` +6 行（含 `import asyncio` + iscoroutine 分支）— design 明示 +5 行；实际多 1 行因 `import asyncio` 独占一行，仍在 design 描述范围内 ✅
- `operators/__init__.py` +5 / -1 — export + 注册，design 明示 ✅
- `tests/test_operator_eval_gen.py`（new，5 tests）— design 明示 ✅
- `tests/test_recipe_v2.py` +81 行（1 test）— design 明示 ✅
- `tests/test_image_to_text_suite.py` -1 / +1 — **DEV-1 偏离**（见下节）

## DEV-1 偏离评估

sonnet 在 implementation.md §偏离 design.md 中显式声明 DEV-1：

- **修改**：`test_image_to_text_suite.py` `len(names) == 9` → `len(names) >= 9`
- **原因**：新增第 10 个算子后该硬编码断言必然失败
- **类型**：必要副作用（design 漏点）
- **reviewer 评估**：
  - 完全契合 memory `[[feedback_brittle_count_assertions]]` 反脆弱约束（"dataplat Registry 测试禁用 len == N 总数断言；用 >= N"）
  - 与 dashboard Follow-up backlog `harness-registry-count-assert-style-*` 同方向（就地修而非新 change）
  - 改动 1 行；test 语义未弱化（仍含 `image_strip in names` / `image_caption_stub in names` 严断言）
  - **接受偏离**：必要副作用、就地修复脆弱断言、不引入隐式扩张

## 隐式偏离审计

对照 design.md / implementation.md / git diff 排查未声明偏离：

- `eval_gen.py` 末尾 `try/except ValueError` 注册（implementation.md §实现说明 6 已显式声明）— OK
- `recipe.py` 多 1 行 `import asyncio`（implementation.md §改动文件清单 已隐含 "+ operator 循环加 iscoroutine"）— OK（design 数 "5 行" 是估计，实际 6 行差 1 行属合理）
- 无未声明偏离 ✅

## 永不做清单检查（data-not-code-pivot.md）

grep `git diff` 排除关键词：

| 关键词 | 命中 | 结论 |
|---|---|---|
| `manifest.yaml` | 0 | ✅ |
| `dataset-card` / `dataset_card` | 0 | ✅ |
| `row-diff` / `row_diff` | 0 | ✅ |
| `cherry-pick` / `cherry_pick` | 0 | ✅ |
| `rollback` | 0 | ✅ |
| `branch.*merge` | 0 | ✅ |
| alembic / DB schema rename | 0（无 alembic 迁移） | ✅ |
| Asset / silver 文件树 | 0 | ✅ |
| bronze 强 schema | 0 | ✅ |

**永不做清单零违反** ✅

## 回归表

| 测试 suite | 命令 | 结果 | 期望 | 结论 |
|---|---|---|---|---|
| packages/core 全量 | `cd packages/core && uv run pytest -x -q` | **108 passed** | ≥ 108（102 基线 + 6 new） | ✅ 0 回归 |
| apps/api 全量 | `cd apps/api && uv run pytest -x -q` | **51 passed, 131 skipped** | 51+ passed / 131+ skipped | ✅ 0 回归 |
| apps/web | 未跑 | — | 不改不必跑（无 web 代码 diff） | ✅ scope OK |

`packages/core` 新增测试明细：

- `test_operator_eval_gen.py`：5 new
- `test_recipe_v2.py::test_run_recipe_v2_supports_async_operator`：1 new
- 总计 +6 → 102 + 6 = 108 ✅ 精确对齐

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

无。（follow-up backlog 见 design.md §关联 follow-up：n_per_row > 1 / retry on parse fail / prompt 模板从 file 加载 / worker 注入真 LLMGateway / web eval preview UI / DPO pair gen 等已规划）

## Verdict

**APPROVED**

理由：

1. 4 条 AC 真跑全 PASS（含 AC-4 ≥108：精确 108）
2. apps/api 0 回归（51 passed / 131 skipped 与 W4-7 基线一致）
3. Scope-creep 检查：W1..W4-7 已 merged 产物零修改（除 design 明示的 protocols/operator.py + recipe.py）
4. DEV-1 偏离（test_image_to_text_suite.py len==9 → >=9）符合 memory 反脆弱约束；接受为必要副作用
5. 隐式偏离审计：无未声明偏离
6. 永不做清单：零违反
7. 实现质量：first-LLM-bound operator + recipe.py async/sync union 桥接干净；FakeLLMClient 测试覆盖 happy / short_skip / parse_fail / fence / invalid_answer 5 个关键路径；short_skip 通过 call_count 断言"LLM 未被调用"，行为闭环

## 后续指引

1. 切回 main：`git checkout main`
2. merge：`git merge --no-ff change/operator-eval-gen-20260520 -m "Merge change/operator-eval-gen-20260520: operator eval gen (W4-8)"`
3. 回写 `.harness/orchestration/north-star-rollout-20260520/dashboard.md`：W4-8 行 `merged | APPROVED | <merge_hash>`；Wave 4 进度 8/10；next → W4-9 operator-dpo-pair-gen
4. 写 summary.md（含 merge commit / pass 数 / 0-issue streak 22）
5. commit dashboard + summary 到 main（一个 docs commit）
6. 下一个 change：W4-9 `operator-dpo-pair-gen-20260520`（depends on W4-8；同 LLM-in-operator 模式）
