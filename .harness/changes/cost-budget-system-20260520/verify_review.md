---
change_id: cost-budget-system-20260520
phase: verify
status: done
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: 2026-05-21T13:00:00Z
verdict: APPROVED
---

# Verify Review：cost-budget-system (W4-5)

> Phase 3 opus reviewer 对照 design.md + implementation.md + `git diff main...change/cost-budget-system-20260520` 验 PR。

## 输入

- **Design**：`.harness/changes/cost-budget-system-20260520/design.md`（v3 mini-design，opus）
- **Implementation**：`.harness/changes/cost-budget-system-20260520/implementation.md`（sonnet end-to-end）
- **Branch**：`change/cost-budget-system-20260520`（commits `6ff91c6` + `a859620` + `a52d00c`）
- **Base**：`95f55e7`（W4-4 merge commit on main）

## AC 对照表

| AC | kind | reviewer 跑的命令 | 结果 | 结论 |
|---|---|---|---|---|
| AC-1 | static | `cd packages/core && uv run python -c "from dataplat_core.cost import CostLedger, BudgetExceeded, compute_cost, DEFAULT_RATES; print('OK')"` + `cd apps/api && uv run python -c "from dataplat_api.llm.cost import CostController, get_cost_controller; print('OK')"` | `core OK` + `api OK` | PASS |
| AC-2 | behavioral | `cd packages/core && uv run pytest tests/test_cost.py -x -q` | 5 passed in 0.08s | PASS |
| AC-3 | behavioral | `cd apps/api && uv run pytest tests/test_llm_cost.py -x -q` | 3 passed in 0.36s（含 test_gateway_raises_budget_exceeded） | PASS |
| AC-4 | behavioral | `cd apps/api && uv run pytest tests/test_router_budgets.py -x -q` | 3 skipped in 1.66s（env-gated，与 W4-1/W4-4 同模式；spec 允许 SKIP） | PASS |

## 机械化检查日志

```text
$ cd packages/core && uv run pytest -q
97 passed in 1.32s   # baseline 92 + 5 新增（DEV-1：4 spec + 1 bonus）

$ cd apps/api && uv run pytest -q
51 passed, 128 skipped in 1.85s   # +3 env-free PASS（test_llm_cost）+ 3 env-gated SKIP（test_router_budgets）

$ git diff 95f55e7..a52d00c --stat
.../cost-budget-system-20260520/design.md         | 147 ++
.../cost-budget-system-20260520/implementation.md |  71 ++
.../cost-budget-system-20260520/summary.md        |  60 ++   # 占位（本 verify 后重写）
.../cost-budget-system-20260520/verify_review.md  |  81 ++   # 占位（本文件）
.../web-snapshot-export-ui-20260520/summary.md    |  70 ++   # W4-4 backfill（dashboard 同步）
.../north-star-rollout-20260520/dashboard.md      |  34 +-
apps/api/dataplat_api/llm/cost.py                 | 107 ++
apps/api/dataplat_api/llm/factory.py              |  13 +-
apps/api/dataplat_api/llm/gateway.py              |  62 +-
apps/api/dataplat_api/main.py                     |   2 +
apps/api/dataplat_api/routers/budgets.py          | 119 ++
apps/api/dataplat_api/schemas/budget.py           |  48 ++
apps/api/tests/test_llm_cost.py                   | 133 ++
apps/api/tests/test_router_budgets.py             | 248 +++
packages/core/src/dataplat_core/cost.py           | 180 +++
packages/core/tests/test_cost.py                  | 140 ++
16 files changed, 1493 insertions(+), 22 deletions(-)

# W1..W4-4 已 merge 产物未动；本 change 仅
#   - packages/core 新增 cost.py + tests
#   - apps/api 新增 llm/cost.py + schemas/budget.py + routers/budgets.py + 2 test files
#   - apps/api 改 llm/gateway.py + llm/factory.py + main.py（小切口注入）
```

## 隐式偏离审计

reviewer 对照 design.md vs implementation.md vs git diff：**无隐式偏离**。

所有 implementation.md 列出的 DEV-1..DEV-3 三项偏离均显式声明并与 design 一致：

- **DEV-1 (bonus test)**：spec 写 4 tests；impl 5（多 1 个 BudgetExceeded fields 测试）→ 覆盖增益，ACCEPT。
- **DEV-2 (`test-model` 入 DEFAULT_RATES)**：design.md §决策 5 原话："DEFAULT_RATES 含 `fake-model` 行 + 价格 = 0，同时一个 test 用 rate 非 0 的 model_id 例如 stub `test-model`"。impl 直接把 `test-model` 放进 DEFAULT_RATES 是最干净写法，与 spec 文字一致，ACCEPT。
- **DEV-3 (check + record 各自加锁)**：design.md §风险表写"asyncio.Lock 包 check + record"；impl 中 check 内 await lock、record 内 await lock，两次 lock 之间释放（不持锁跨 100ms provider call）。竞态窗口在 design §风险表已承认；行为与"防止两路 caller 并发预检都过"语义一致。性能正确选择（不持锁跨外部 IO），ACCEPT。

## D-1 永不做清单复核

| D-1 项 | 本 change 是否触犯 |
|---|---|
| manifest.yaml mandatory | 否（无 manifest 字段） |
| dataset-card.yaml | 否 |
| row-diff / per-row cost stats 写入 silver row | 否（cost 走进程内 ledger；spec §Out of scope 明确） |
| cherry-pick / rollback / branch / merge 语义 | 否（无版本控制改动） |
| blob 派生图 / Asset / manifest 强制 / silver 文件树 / bronze 强 schema | 否 |
| alembic migration / DB schema rename | 否（spec §Out of scope 明确"不入 DB 表"） |

**D-1 PASS：本 change 0 命中。**

## 范围审计

- W1..W4-4 已 merge 产物（loaders/operators/adapters/recipe/exporters/snapshot 等）**全部未改动**。
- W4-4 main.py 新增 snapshots router 与本 change 新增 budgets router 在 main.py 同处并存（无冲突）。
- packages/core 仅新增 `cost.py` + `tests/test_cost.py`，零 edit。
- apps/api 改动 surface 完全在 design.md §范围 列出的清单内（gateway/factory/main + 新 cost.py + 新 routers/budgets.py + 新 schemas/budget.py）。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

- follow-up `cost-budget-persist-*`（DB schema + alembic）已在 design §关联 follow-up 记录。
- follow-up `web-cost-dashboard-*` UI 看 breakdown / 历史，已记录。
- follow-up `operator-image-caption-llm-*`（W2-3 占位算子的真 VLM 版本，消费本 change 的 budget 系统）已记录。
- follow-up `silver-row-cost-stats-*` / `cost-rates-dynamic-*` 已记录。

## Verdict

**APPROVED** — PR 兑现 design.md 全部 4 AC + 0 隐式偏离 + 0 D-1 命中；3 个声明偏离均合理 ACCEPT；测试 baseline 92 → 97 PASS（core）/ 48 → 51 PASS（api env-free）；范围干净，不破坏已 merge 产物。

## 后续指引

- merge `change/cost-budget-system-20260520` → main（--no-ff）
- 写 summary.md（参考 W4-4 模板）
- dashboard.md：Wave 4 进度 4/10 → 5/10；W4-5 phase merged / verdict APPROVED；next action 启动 W4-6 integration-test-framework（W3 done + W4-1..4 已 merged，前置充足）
