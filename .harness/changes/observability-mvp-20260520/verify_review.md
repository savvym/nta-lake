---
change_id: observability-mvp-20260520
phase: verify
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: 2026-05-21T14:00:00Z
verdict: APPROVED
---

# Verify Review：W4-7 observability-mvp（Phase 3 opus，真跑 AC + diff 体检）

> Phase 3 reviewer 产物。对照 [design.md](design.md)（原始要求）+ [implementation.md](implementation.md)（声称的实现）+ `git diff ef91e85..HEAD` 验 PR。

## 输入

- **Design**：`.harness/changes/observability-mvp-20260520/design.md`（commit `da41720`，opus 自写 mini-design v3）
- **Implementation**：`.harness/changes/observability-mvp-20260520/implementation.md`（commit `9de587a` backfill；feat commit `d93be97`，sonnet）
- **Git diff**：`git diff ef91e85..HEAD`（merge-base = `ef91e85`，main HEAD at W4-6 docs commit；用户指定 base `f8068fa` 偏一个 docs 提交，实际 W4-7 改动 = 14 files）
- **Branch**：`change/observability-mvp-20260520`（工作树 clean）

## AC 真跑对照表

| AC | kind | reviewer 跑的命令 | 输出 | PASS/FAIL/SKIP |
|---|---|---|---|---|
| AC-1 | static | `cd packages/core && uv run python -c "from dataplat_core.metrics import MetricsRegistry, OperatorMetrics, get_metrics_registry, reset_metrics_registry; print('OK')"` | `OK` | **PASS** |
| AC-2 | behavioral | `cd packages/core && uv run pytest tests/test_metrics.py -x -q` | `4 passed in 0.08s` | **PASS** |
| AC-3 | behavioral | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_records_metrics -x -q` | `1 passed in 0.12s` | **PASS** |
| AC-4 | behavioral (env-gated) | `cd apps/api && uv run pytest tests/test_router_metrics.py -x -q` | `2 skipped in 1.66s`（无 DB env，与 W4-1/W4-5 同模式） | **PASS (SKIP)** |

> AC-4 SKIP 状态：DATAPLAT_DATABASE_URL 未设置；与 design.md AC-4 行 "env 就位时 PASS / env 缺时 SKIP" 显式契约一致，与 W4-5 budgets 测试同模式。

## 回归套件

| 套件 | reviewer 命令 | 输出 | 基线 / 期望 | 结果 |
|---|---|---|---|---|
| packages/core | `uv run pytest -x -q` | `102 passed in 1.30s` | ≥ 102（W4-6 后 97 + 5 new = 102） | **PASS** |
| apps/api | `uv run pytest -x -q` | `51 passed, 131 skipped in 1.88s` | 51 passed + 129~131 skipped（W4-7 +2 env-gated SKIP） | **PASS** |
| apps/web vitest | `pnpm vitest run` | `22 files / 62 passed` | ≥ 62（W4-6 后 60 + 2 new = 62） | **PASS** |
| apps/web tsc | `pnpm tsc --noEmit` | （无输出，exit 0） | 0 errors | **PASS** |

零回归；packages/core +5 new tests（test_metrics 4 + test_recipe_v2 records_metrics 1）+ 2 原 test 改 async；apps/web +2 new tests；apps/api +2 env-gated SKIP。

## diff 体检

```text
$ git log --oneline ef91e85..HEAD
9de587a docs(impl.md): W4-7 observability-mvp Phase 2 backfill
d93be97 feat(observability-mvp): W4-7 operator metrics registry + API + UI
da41720 design(observability-mvp-20260520): W4-7 mini-design

$ git diff ef91e85..HEAD --stat
.../changes/observability-mvp-20260520/design.md         | 177 +++++++++
 .../observability-mvp-20260520/implementation.md        |  99 +++++
 apps/api/dataplat_api/main.py                           |   4 +-
 apps/api/dataplat_api/routers/metrics.py                |  56 +++
 apps/api/tests/test_router_metrics.py                   | 139 +++++++
 apps/web/src/lib/api/queries.ts                         |  26 +
 apps/web/src/routeTree.gen.ts                           |  21 +
 apps/web/src/routes/__root.tsx                          |  22 +-
 apps/web/src/routes/observability.test.tsx              | 112 +++++
 apps/web/src/routes/observability.tsx                   | 105 +++++
 packages/core/src/dataplat_core/metrics.py              | 134 +++++++
 packages/core/src/dataplat_core/recipe.py               |  31 +-
 packages/core/tests/test_metrics.py                     | 108 +++++
 packages/core/tests/test_recipe_v2.py                   |  84 +++-
 14 files changed, 1093 insertions(+), 25 deletions(-)
```

> 注：用户指定的 base commit `f8068fa` 是 W4-6 merge commit；实际 main HEAD 已推进到 `ef91e85`（W4-6 docs close commit），W4-7 branch 即从 `ef91e85` 拉出。从 `f8068fa..HEAD` 会包含 `ef91e85` 自身（即 W4-6 close 的 dashboard + summary 编辑），这不是 W4-7 引入的改动。使用 merge-base `ef91e85..HEAD` 是正确的 W4-7 改动范围。

## scope-creep 检查

| 检查项 | 期望 | 实际 | 结论 |
|---|---|---|---|
| 改动文件 ⊆ design.md `## 范围` In scope | 14 files matching design 列表 | 14 files 一一对应（design.md / impl.md / metrics.py / recipe.py / test_metrics.py / test_recipe_v2.py / routers/metrics.py / main.py / test_router_metrics.py / queries.ts / observability.tsx / __root.tsx / routeTree.gen.ts / observability.test.tsx） | **PASS** |
| design `## 交叉引用清单 应当不动` 文件未被改 | cost.py / gateway.py / protocols/operator.py / W1..W4-6 merged 产物（除 recipe.py async） | `git diff ef91e85..HEAD -- packages/core/src/dataplat_core/cost.py apps/api/dataplat_api/llm/gateway.py packages/core/src/dataplat_core/protocols/operator.py` → 空输出 | **PASS** |
| Out of scope 项未触发（prometheus / DB persist / histogram / Loader 埋点 / alert / cost merge） | 不引入 prometheus_client / 不动 DB schema / 不加 percentile / Loader 不埋 / 无 alerting / metrics 与 cost 仍独立 | 仅 in-process JSON + Operator 层 record；无 prometheus_client / alembic 改动 | **PASS** |
| 不引入新依赖 | design § Out of scope 隐含；imp.md 未列新 dep | metrics.py 仅用 stdlib + 既有 pydantic；routers/metrics.py 仅用既有 fastapi/pydantic；observability.tsx 仅用既有 React/TanStack 套件 | **PASS** |
| 不动 alembic / DB migration | design 显式声明 | `git diff ef91e85..HEAD -- "**/migrations/*" "**/alembic/*"` → 空 | **PASS** |

## 永不做清单检查（[data-not-code-pivot.md](../../rules/data-not-code-pivot.md)）

`git diff ef91e85..HEAD | grep -iE "manifest\.yaml|dataset-card\.yaml|row.?diff|cherry.?pick|rollback|force.?push|branch.*merge"` → 空输出。

| 永不做项 | 是否引入 | 结论 |
|---|---|---|
| branch / merge / cherry-pick / rollback | metrics.py / recipe.py / observability.tsx 无相关引用 | **PASS** |
| row-level diff | 仅总览统计（rows_in/out 计数），无 per-row diff | **PASS** |
| blob → blob 派生图 | 不涉及 lineage / source_ref | **PASS** |
| Asset 抽象 / manifest.yaml 强制 | 不涉及 bronze 资产层 | **PASS** |
| silver 文件树 | 不涉及 silver / gold 数据形态 | **PASS** |
| bronze 强 schema | 不动 schema 注册 | **PASS** |

零违反。Operator 切面与永不做清单正交。

## 隐式偏离审计

> reviewer 对照 design.md vs implementation.md vs git diff，列出 implementation.md § 偏离 没声明但实际发生的偏离。

逐文件比对：

- `packages/core/src/dataplat_core/metrics.py`：MetricsRegistry / OperatorMetrics / get_metrics_registry / reset_metrics_registry 实现一致；`computed_field duration_ms_avg` 在 snapshot 时按需算出，符合 design.md 决策 10（不存 last_run_at；时间戳放顶层 collected_at）；`extra="forbid"` 命中 design 行 43。
- `packages/core/src/dataplat_core/recipe.py`：`run_recipe_v2` 改 async + `try/except → record(error=True) → raise`；perf_counter 计时；嵌套 try 只包内层 `for row in rows`（design 决策 11）；与 design.md §范围 行 51-66 代码块逐行一致。
- `packages/core/tests/test_metrics.py`：4 tests = happy / error / sort / reset；impl.md DEV-2 已声明"未直接 import MetricsRegistry/OperatorMetrics（ruff F401 auto-fix），test 内用 get_metrics_registry 已覆盖"。AC-1 由独立 python -c 单测保证 import 路径，DEV-2 接受偏离合理。
- `packages/core/tests/test_recipe_v2.py`：原 2 test 改 `@pytest.mark.asyncio` + `await run_recipe_v2`；+ 1 新 test `test_run_recipe_v2_records_metrics`。与 design.md 行 90-92 一致。
- `apps/api/dataplat_api/routers/metrics.py`：GET `/metrics` + `Depends(require_admin)` + `MetricsResponse(operators, collected_at)`；prefix `/metrics`、tags `["metrics"]`、`datetime.now(tz=UTC).isoformat()` —— 与 design.md 行 71-74 一致。
- `apps/api/dataplat_api/main.py`：+2 行注册 `metrics.router`（与 design.md 行 75 一致）。
- `apps/api/tests/test_router_metrics.py`：admin 200 + 非 admin 403，env-gated SKIP 模式与 W4-1 同（design.md AC-4 行 120 已显式声明）。
- `apps/web/src/lib/api/queries.ts`：`useMetrics` hook + `refetchInterval: 5000` + `enabled` admin gate —— 与 design.md 行 76 + 行 132 决策 7 一致。
- `apps/web/src/routes/observability.tsx`：admin guard / 表格列 operator/runs/rows_in/rows_out/errors/avg duration / 每 5s 自动刷新 文案 / 401-403 → "需要 admin 权限" —— 与 design.md 行 77-81 一致。
- `apps/web/src/routes/__root.tsx`：admin nav 加 Observability Link 在 Jobs 旁，包装一个 `<>...</>` fragment 不影响其余 nav；与 design.md 行 82 一致。
- `apps/web/src/routeTree.gen.ts`：ObservabilityRoute 注册（impl.md DEV-1 已声明 vitest plugin auto-regen 顺序调整为必要副作用，内容等价）。
- `apps/web/src/routes/observability.test.tsx`：2 tests (3 operators rows / 403 message) —— 与 design.md 行 96-98 一致。

**隐式偏离 = 0**。impl.md 声明的 2 个 DEV（routeTree 重生成 / test_metrics 未 import 类型）均为必要副作用或 design 漏点，分类正确，符合 development-process.md "接受偏离" 规则。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

无。

可纳入 follow-up（design.md § 关联 follow-up 已列全 9 项：metrics-prometheus-export-* / metrics-persist-* / metrics-cross-worker-* / metrics-percentile-* / metrics-loader-instrument-* / metrics-alert-* / metrics-cost-merge-* / metrics-live-stream-* / web-observability-charts-*），无需新增。

## Verdict

**APPROVED**

理由：

1. **4 / 4 AC PASS**（AC-4 SKIP = env-gated 契约 PASS，与 design.md 显式声明一致）
2. **零回归**：packages/core 102 / apps/api 51 passed + 131 skipped / vitest 62 / tsc 0
3. **diff 14 files = design 范围**：零 scope creep；should-not-touch 文件 untouched
4. **永不做清单全 PASS**：6 项检查零违反
5. **隐式偏离 = 0**：impl.md 2 DEV（routeTree.gen.ts auto-regen / test_metrics 类型 import）分类正确，接受偏离合理
6. **设计与实现逐行匹配**：metrics.py / recipe.py / routers/metrics.py / observability.tsx / __root.tsx / queries.ts 与 design.md §范围 / §决策 完全对齐

## 后续指引

1. 切回 main：`git checkout main`
2. merge：`git merge --no-ff change/observability-mvp-20260520 -m "Merge change/observability-mvp-20260520: observability MVP (W4-7)"`
3. 回写 dashboard：W4-7 行改 `**merged** | APPROVED | <merge_hash>`，next 切到 W4-8 `operator-eval-gen-*`，Wave 4 进度 7/10
4. 写 summary.md（merge commit / pass 数 / 21 连续 0-issue 延续）
5. commit 一次 docs（dashboard + summary）到 main
6. 关闭 task #77；启动 W4-8 task
