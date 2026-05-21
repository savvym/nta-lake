---
change_id: observability-mvp-20260520
title: observability MVP (W4-7) — operator MetricsRegistry + GET /metrics + /observability UI
owner: application-owner-agent
started_at: 2026-05-21T13:55:00Z
phase: done
status: done
last_updated: 2026-05-21T14:30:00Z
related_changes: [recipe-yaml-v2-20260520, cost-budget-system-20260520, web-pdf-mineru-ui-v2-20260520]
---

# Summary

## 一句话目标

`run_recipe_v2` 跑 Operator 时埋点 → 进程内 `MetricsRegistry`（asyncio.Lock 单例） → admin GET `/metrics` 暴露 JSON 快照 → `/observability` 表格 5s 轮询读，给后续 LLM-bound operator（eval-gen / dpo-pair-gen）落地前先把"哪个 operator 处理多少 row / 多少 error / 多慢"做成可视化。

## 范围摘要

- **In scope**：
  - `packages/core/src/dataplat_core/metrics.py`：`OperatorMetrics` (BaseModel + `duration_ms_avg` computed_field) + `MetricsRegistry` (`record_op_run` async / `snapshot` 排序 / `reset` async) + `@lru_cache` 单例 + `reset_metrics_registry` 测试钩子
  - `packages/core/src/dataplat_core/recipe.py`：`run_recipe_v2` 改 `async`；operator 循环 try/except 包裹 → 失败先 `record(error=True)` 再 raise
  - `apps/api/dataplat_api/routers/metrics.py` + `main.py` 注册：GET `/metrics` admin-only，返 `{operators, collected_at}`
  - `apps/web/src/lib/api/queries.ts::useMetrics`：`refetchInterval: 5000` + admin gate
  - `apps/web/src/routes/observability.tsx` + `__root.tsx` admin nav link + `routeTree.gen.ts`：表格（operator / runs / rows_in / rows_out / errors / avg ms）+ 403 guard
  - 测试：core 5 new（test_metrics 4 + test_recipe_v2 records_metrics 1）+ 原 2 改 async；api 2 env-gated；web 2 component
- **Out of scope**：prometheus exposition / DB 持久化 / 跨 worker 聚合 / histogram + percentile / Loader 埋点 / alert / metrics×cost merge / SSE 流 / chart 库（全列 9 项 follow-up）

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus | approved | APPROVED (self-attest, v3 mini-design D-13) | `da41720` | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | `d93be97` (feat) + `9de587a` (docs backfill) | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | approved | APPROVED — 0 issues | `0b8fdde` | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 | registry 放 `packages/core` 而非 `apps/api` | Operator 在 core 跑；埋点必须与 operator 同 import 层；api 路由读单例即可 | design § 决策 1 |
| 2026-05-21 | 进程内单例 + `asyncio.Lock` | 与 cost-ledger / LLMGateway / cost-controller 同模式；MVP；跨 worker / 持久化是独立 follow-up | design § 决策 2 |
| 2026-05-21 | `run_recipe_v2` 改 async（唯一 breaking change） | callers 都在 test 中（grep 确认 2 个），统一 async 模式与 core 现有 cost.py + LLMGateway 一致 | design § 决策 3 |
| 2026-05-21 | 失败时先记 metrics 再 raise | 保留原"第一个异常冒泡"语义；多记一条 `error=True`；不吞 exception | design § 决策 4 |
| 2026-05-21 | 埋点粒度 = Operator 不是 row | 1→N 链路下 per-row 埋点会爆量；总览统计 rows_in/out 足够 | design § 决策 5 |
| 2026-05-21 | path 用 `/metrics`（与 prometheus 默认同名） | JSON exposition；未来接 prometheus 新增 `/metrics/prometheus` 不冲突 | design § 决策 6 |
| 2026-05-21 | UI 5s 轮询（不 SSE） | MVP；单 worker / 单 admin 场景够用 | design § 决策 7 |
| 2026-05-21 | 表格不引 chart 库 | 减 bundle / 减依赖；MVP demo 表格足够 | design § 决策 8 |

## 当前阻塞

无。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up | prometheus exposition format（`/metrics/prometheus` text） | `metrics-prometheus-export-*` |
| follow-up | DB / Redis 持久化（重启不丢） | `metrics-persist-*` |
| follow-up | 多 worker 下 metrics 聚合（共享内存 / Redis） | `metrics-cross-worker-*` |
| follow-up | histogram + P50/P99 percentile | `metrics-percentile-*` |
| follow-up | Loader / Adapter 链埋点 | `metrics-loader-instrument-*` |
| follow-up | 异常率 / 慢 operator 阈值报警 | `metrics-alert-*` |
| follow-up | 观察表加 `cost_usd` 列（与 W4-5 ledger 关联） | `metrics-cost-merge-*` |
| follow-up | SSE / WebSocket 流（替代 5s 轮询） | `metrics-live-stream-*` |
| follow-up | 表格 → recharts / chart.js 时间序列 | `web-observability-charts-*` |
| meta follow-up | verifier prompt 用 `git merge-base main HEAD` 而非固定 base SHA（W4-7 reviewer 撞过 1 个 docs commit off-by-one） | `harness-verifier-prompt-base-merge-base-*` |

## 交付

- Branch：`change/observability-mvp-20260520`
- Base：`ef91e85`（main HEAD at W4-6 docs close commit；用户指定 `f8068fa` 为 W4-6 merge commit，实际 main 已推进 1 个 docs commit）
- Head：`0b8fdde`（verify_review）；feat `d93be97` + impl.md backfill `9de587a`
- Merge commit：`5d1a097`（main，`--no-ff`）
- 用户确认：批量授权（"我只最后验收整个系统，也不用给我过目了"，2026-05-20）
- 关闭时间：2026-05-21T14:30:00Z

## 测试通过证据（reviewer 真跑，2026-05-21T14:00Z）

| 维度 | 数字 | 命令 |
|---|---|---|
| AC-1 dry-import | OK | `uv run python -c "from dataplat_core.metrics import ...; print('OK')"` |
| AC-2 test_metrics | 4 passed | `uv run pytest tests/test_metrics.py -x -q` |
| AC-3 records_metrics | 1 passed | `uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_records_metrics -x -q` |
| AC-4 router env-gated | 2 skipped (env 缺，与 W4-1 同模式) | `uv run pytest tests/test_router_metrics.py -x -q` |
| packages/core 全量 | **102 passed** | `uv run pytest -x -q` |
| apps/api 全量 | **51 passed, 131 skipped** | `uv run pytest -x -q` |
| apps/web vitest | **62 passed** | `pnpm vitest run` |
| apps/web tsc | **0 errors** | `pnpm tsc --noEmit` |

零回归。永不做清单 6 项全 PASS（无 manifest/dataset-card/row-diff/cherry-pick/rollback/branch-merge）。should-not-touch 文件（cost.py / gateway.py / protocols/operator.py）零改动。

## 0-issue streak

W4-7 是连续第 **21** 个 0-issue APPROVED（W1-4 / W2-1..W2-6 / W3-1..W3-7 / W4-1..W4-7）。

## 复盘

### 哪些顺利

- v3 mini-design 流再次稳定运转：opus design 178 行 / 4 AC → sonnet 端到端（12 文件 + 14 测试改动）→ opus verify 4 min；零 reviewer round-trip
- 复用既有模式（asyncio.Lock 单例 / `@lru_cache` / `reset_*` test helper / admin Depends）显著减心智负担
- 改 async 这种"看着 breaking"的改动，因 callers 全在 test（design 阶段 grep 已确认），实际改动 = 2 行函数签名 + `await`
- 21 连 0-issue 延续；W4-7 含 2 DEV ACCEPT（routeTree.gen.ts auto-regen / test 类型未直接 import），impl.md 主动声明 + 分类正确，reviewer 接受

### 哪些踩坑

- 用户指定 base = `f8068fa`（W4-6 merge）；实际 main 已推进到 `ef91e85`（W4-6 docs close）；`f8068fa..HEAD` 会多带一个 `ef91e85` 提交。reviewer 用 `git merge-base main HEAD` 修正为 `ef91e85..HEAD` 才是真 W4-7 scope。**防复发**：verifier prompt 里 base 写 "merge-base main HEAD" 而非具体 SHA，避免 main 在 dispatch 期间推进的 off-by-one。落 follow-up `harness-verifier-prompt-base-merge-base-*`
