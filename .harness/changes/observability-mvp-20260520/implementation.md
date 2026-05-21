---
change_id: observability-mvp-20260520
phase: implementation
status: done
authored_at: 2026-05-21T12:00:00Z
author: sonnet-phase2-implementer
model_used: claude-sonnet-4-6
branch: change/observability-mvp-20260520
base_commit: f8068fa
head_commit: d93be97415ce2f0940e4297a7d2947f5ef759c4d
pr_url: n/a (no gh PAT pr:write)
---

# Implementation：observability MVP (W4-7)

## 改动文件清单

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `packages/core/src/dataplat_core/metrics.py` | new | MetricsRegistry + OperatorMetrics + singleton helpers |
| `packages/core/src/dataplat_core/recipe.py` | edit | run_recipe_v2 改 async + operator 循环埋点 |
| `packages/core/tests/test_metrics.py` | new | 4 tests：happy/error/sort/reset |
| `packages/core/tests/test_recipe_v2.py` | edit | 2 existing tests → async+await；+1 metrics test |
| `apps/api/dataplat_api/routers/metrics.py` | new | GET /metrics (admin-only) |
| `apps/api/dataplat_api/main.py` | edit | register metrics_router |
| `apps/api/tests/test_router_metrics.py` | new | 2 tests (env-gated：admin 200 / non-admin 403) |
| `apps/web/src/lib/api/queries.ts` | edit | useMetrics() hook + types |
| `apps/web/src/routes/observability.tsx` | new | 观察页面：表格 + admin guard |
| `apps/web/src/routes/__root.tsx` | edit | admin nav 加 Observability link |
| `apps/web/src/routeTree.gen.ts` | edit | ObservabilityRoute 注册 |
| `apps/web/src/routes/observability.test.tsx` | new | 2 tests (3 rows / 403 message) |

## 任务完成情况

| Task | 状态 | 说明 |
|---|---|---|
| metrics.py MetricsRegistry | done | asyncio.Lock + lru_cache 单例，与 cost-ledger 同模式 |
| recipe.py async + 埋点 | done | error=True record-then-raise；perf_counter 计时 |
| test_metrics.py 4 tests | done | happy / error / sort / reset |
| test_recipe_v2.py 改 async + 新 test | done | 原 2 test await + reset_metrics + 1 新 metrics test |
| routers/metrics.py GET /metrics | done | admin-only；返 operators + collected_at |
| main.py register | done | metrics_router 注册 |
| test_router_metrics.py | done | 2 tests env-gated |
| queries.ts useMetrics() | done | refetchInterval: 5000 + enabled by admin |
| observability.tsx | done | 表格 + 403 guard |
| __root.tsx nav link | done | Observability 在 Jobs 旁 |
| routeTree.gen.ts | done | 手编辑后 vitest run 触发 TanStack 自动重新生成确认一致 |
| observability.test.tsx | done | 2 tests (3 rows + 403) |

## 测试通过证据

### AC-1: static import
```
$ uv run --package dataplat-core python -c "from dataplat_core.metrics import MetricsRegistry, OperatorMetrics, get_metrics_registry, reset_metrics_registry; print('OK')"
OK
```

### AC-2: packages/core tests（102 passed，基线 97 + 5 new）
```
$ uv run --package dataplat-core pytest packages/core/tests/ -x -q
102 passed in 1.29s
```

### AC-3: test_run_recipe_v2_records_metrics
```
$ uv run --package dataplat-core pytest packages/core/tests/test_recipe_v2.py::test_run_recipe_v2_records_metrics -x -q
1 passed in 0.28s
```

### AC-4: apps/api tests（51 passed, 131 skipped；2 new tests env-gated SKIP）
```
$ uv run --package dataplat-api pytest apps/api/tests/ -x -q
51 passed, 131 skipped in 1.86s
```
AC-4 SKIP 状态：无 DB 环境（DATAPLAT_DATABASE_URL 未设置）；与 W4-5 budgets 测试同模式。

### vitest（62 passed，基线 60 + 2 new）
```
$ cd apps/web && pnpm vitest run
Test Files  22 passed (22)
Tests  62 passed (62)
```

### tsc（0 errors）
```
$ cd apps/web && pnpm tsc --noEmit
（无输出）
```

## 偏离 design.md

| # | 偏离点 | 分类 | 说明 |
|---|---|---|---|
| DEV-1 | routeTree.gen.ts 手编辑后被 TanStack 自动重新生成，import 顺序调整 | 必要副作用 | TanStack Router vitest 插件在 collect 阶段重新生成；内容等价，ObservabilityRoute 全部正确注册 |
| DEV-2 | test_metrics.py 未直接 import MetricsRegistry / OperatorMetrics | design 漏点 | AC-1 smoke 测试独立用 python -c；test 内用 get_metrics_registry 足够；ruff F401 auto-fix 删除多余 import |

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 PR。
