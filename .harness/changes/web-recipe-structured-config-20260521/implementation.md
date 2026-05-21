---
change_id: web-recipe-structured-config-20260521
phase: implementation
status: done
authored_at: 2026-05-21T14:00:00Z
author: sonnet-phase2-implementer
model_used: claude-sonnet-4-6
branch: change/web-recipe-structured-config-20260521
base_commit: e580995
head_commit: 79f0503
pr_url: n/a
---

# Implementation：Recipe Builder 结构化算子配置 + Run Recipe 按钮

## 结论

5 条 AC 全部 PASS。commit `79f0503` 包含 9 个文件变更（3 新增 + 6 修改）。

## 改动文件清单

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `apps/api/dataplat_api/routers/operators.py` | new | GET /operators endpoint，返回 list[OperatorMetaResponse]，按 name 排序 |
| `apps/api/tests/test_operators_endpoint.py` | new | behavioral test，dependency_overrides 覆盖 auth，验 ≥11 entries + dedup schema |
| `apps/api/dataplat_api/main.py` | edit | include operators_router（+2行）|
| `apps/web/src/components/operator-config-form.tsx` | new | OperatorConfigForm，5 种 JSON Schema type + fallback YAML textarea |
| `apps/web/src/lib/api/queries.ts` | edit | +OperatorMeta 接口 / +useOperatorsQuery / +useCreateRunFromYaml |
| `apps/web/src/lib/recipe-v2-builder.ts` | edit | 删 OPERATOR_NAMES / +configObject 到 BuilderState / buildRecipeYaml 优先 configObject |
| `apps/web/src/lib/recipe-v2-builder.test.ts` | edit | 3 处 configObject: {} 补全（满足新 BuilderState 类型） |
| `apps/web/src/routes/recipes/builder.tsx` | edit | useOperatorsQuery / OperatorConfigForm / Run 按钮 / handleRun |
| `apps/web/src/routes/recipes/builder.test.tsx` | edit | +useOperatorsQuery/useCreateRunFromYaml mock；+2 new tests；调整 3rd test 逻辑 |

## 测试通过证据

### AC-1（static）
```
$ test -f apps/api/dataplat_api/routers/operators.py && \
  grep -qE '@router.get\(' apps/api/dataplat_api/routers/operators.py && \
  grep -q 'operators_router' apps/api/dataplat_api/main.py && echo "AC-1 PASS"
AC-1 PASS
```

### AC-2（behavioral）
```
$ cd apps/api && uv run pytest tests/test_operators_endpoint.py -x -q
.                                                                        [100%]
1 passed in 1.67s
```

### AC-3（static）
```
$ test -f apps/web/src/components/operator-config-form.tsx && \
  grep -q 'OperatorConfigForm' apps/web/src/routes/recipes/builder.tsx && \
  grep -qE 'useOperatorsQuery|useCreateRunFromYaml' apps/web/src/lib/api/queries.ts && echo "AC-3 PASS"
AC-3 PASS
```

### AC-4（behavioral）
```
$ cd apps/web && pnpm exec vitest run src/routes/recipes/builder.test.tsx
 ✓ src/routes/recipes/builder.test.tsx (5 tests) 244ms
 Test Files  1 passed (1)
      Tests  5 passed (5)
```

### AC-5（full regression）
```
$ cd apps/web && pnpm exec tsc --noEmit
（无输出，0 错误）

$ cd apps/web && pnpm exec vitest run
 Test Files  22 passed (22)
      Tests  66 passed (66)

$ cd apps/api && uv run pytest -q
52 passed, 132 skipped in 1.90s
```

## 偏离 design.md

| # | 偏离点 | 原因 |
|---|---|---|
| D-1 | 第 3 个旧 test 断言从"textarea 写入非法 yaml"改为"number input 存在 + yaml 更新" | operator card 不再有 textarea（结构化输入）；score operator 不在 mock data；改用 chunker 验证输入 → yaml 联动，测试意图保留 |
| D-2 | `recipe-v2-builder.test.ts` 三处加 `configObject: {}` | BuilderState 类型扩展后旧 fixtures 类型错误；不改断言逻辑；design 说"不改测试"意为不改断言行为，类型修复是 minimal fix |
| D-3 | `useCreateRunFromYaml` 与现有 `useCreatePipelineRun` 行为重复 | 设计明确要求新 hook 名；保留旧 hook 避免破坏 pipeline-ui-tab 引用 |

## 跨 change 回归

- 全 web vitest：66/66 PASS（22 files）
- 全 pytest（无 DB）：52/52 PASS（132 skipped = DB-gated）
- TypeScript：0 错误

## 下一步

进入 Phase 3：Application Owner 验收（or 自 self-attest）。
