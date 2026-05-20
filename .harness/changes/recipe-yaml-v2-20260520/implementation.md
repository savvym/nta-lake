---
change_id: recipe-yaml-v2-20260520
phase: implementation
status: done
authored_at: 2026-05-20T02:00:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/recipe-yaml-v2-20260520
base_commit: 4f3ce26
head_commit: 6dcaf86
pr_url: n/a (gh PAT 缺 pr:write)
---

# Implementation

> Phase 2 sonnet 端到端产物。一次 sonnet 调用内完成：编码 + 单元测试 + 端到端验证 + commit。

## 改动文件清单

执行 `git diff --name-only main...HEAD`：

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `packages/core/src/dataplat_core/recipe.py` | new | Recipe v2 schema + load_recipe_v2 解析器 + run_recipe_v2 执行器 | W2-5 |
| `packages/core/tests/test_recipe_v2.py` | new | AC-1..AC-4 行为测试 + stub loader 内联注册 | W2-5 |
| `.harness/changes/recipe-yaml-v2-20260520/implementation.md` | edit | 本文件（Phase 2 产物）| W2-5 |

## 任务完成情况

| Task | 状态 | commit | 备注 |
|---|---|---|---|
| recipe.py schema（RecipeLoaderSpec / RecipeOperatorSpec / RecipeV2 / RecipeRunResult） | done | 6dcaf86 | model_config extra="forbid"；Literal[2] version |
| load_recipe_v2 解析器 | done | 6dcaf86 | str → yaml.safe_load；version != 2 → ValueError("v1 deprecated...") |
| run_recipe_v2 执行器 | done | 6dcaf86 | 严格按 design.md §run_recipe_v2 步骤 1-7 |
| test_recipe_v2.py（AC-1..AC-4） | done | 6dcaf86 | 4/4 PASS |

## 测试通过证据

### AC-1 (test_load_recipe_v2_valid)

```text
$ cd packages/core && uv run pytest tests/test_recipe_v2.py::test_load_recipe_v2_valid -x -q
1 passed in 0.06s
```

### AC-2 (test_load_recipe_v2_rejects_v1)

```text
$ cd packages/core && uv run pytest tests/test_recipe_v2.py::test_load_recipe_v2_rejects_v1 -x -q
1 passed in 0.06s
```

### AC-3 (test_run_recipe_v2_end_to_end)

```text
$ cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_end_to_end -x -q
1 passed in 0.08s
```

### AC-4 (test_run_recipe_v2_empty_operators)

```text
$ cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_empty_operators -x -q
1 passed in 0.06s
```

### 全量 pytest（自检 AC block）

```text
$ cd packages/core && uv run pytest tests/ -q
58 passed in 0.26s
```

（基线 54 + 本 change 新增 4 = 58；无回归）

### Pyright（recipe.py + test_recipe_v2.py）

```text
$ cd packages/core && uv run pyright src/dataplat_core/recipe.py tests/test_recipe_v2.py
0 errors, 0 warnings, 0 informations
```

全量 pyright 5 errors 均为 pre-existing（test_auth_protocol / test_lineage / test_repository / test_tree 中的故意 invalid literal 测试），与本 change 无关。

## 偏离 design.md（如有）

无偏离。严格按 design.md In scope 落地。

## 跨 change / 上游回归

- 全量 pytest packages/core：58/58 PASS（W1-2..W2-4 全部无回归）
- pyright recipe.py + test_recipe_v2.py：0/0/0

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 AC-1..AC-4。
