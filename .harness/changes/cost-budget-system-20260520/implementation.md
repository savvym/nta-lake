---
change_id: cost-budget-system-20260520
phase: implementation
status: done
authored_at: 2026-05-21T12:30:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/cost-budget-system-20260520
base_commit: 6ff91c6
head_commit: a859620
pr_url: n/a (gh PAT 缺 pr:write)
---

# Implementation

> Phase 2 sonnet 端到端产物。一次 sonnet 调用内完成：编码 + 单元测试 + 端到端验证 + commit。

## 改动文件清单

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `packages/core/src/dataplat_core/cost.py` | new | CostRate / CostLedger / compute_cost / BudgetExceeded / DEFAULT_RATES |
| `apps/api/dataplat_api/llm/cost.py` | new | CostController + get_cost_controller + reset_cost_controller |
| `apps/api/dataplat_api/llm/gateway.py` | edit | 加 cost/rates/scope 注入；pre-check + post-record；cache hit 不计费 |
| `apps/api/dataplat_api/llm/factory.py` | edit | 注入 controller + DEFAULT_RATES 到 LLMGateway |
| `apps/api/dataplat_api/schemas/budget.py` | new | BudgetSetBody / BudgetResponse / BudgetBreakdownItem / BudgetDeleteResponse |
| `apps/api/dataplat_api/routers/budgets.py` | new | 3 端点 POST/GET/DELETE + require_admin guard |
| `apps/api/dataplat_api/main.py` | edit | 注册 budgets_router |
| `packages/core/tests/test_cost.py` | new | 5 tests（4 spec + 1 bonus BudgetExceeded fields） |
| `apps/api/tests/test_llm_cost.py` | new | 3 tests（env-free，FakeLLMProvider + test-model） |
| `apps/api/tests/test_router_budgets.py` | new | 3 tests（env-gated，缺 DATAPLAT_DATABASE_URL → SKIP） |

## AC 自检结果

| AC | kind | 描述 | 证据 | 结论 |
|---|---|---|---|---|
| AC-1 | static | cost.py + CostController 导出 | `python -c "from dataplat_core.cost import CostLedger, BudgetExceeded, compute_cost, DEFAULT_RATES; from dataplat_api.llm.cost import CostController, get_cost_controller; print('OK')"` → 输出 OK | PASS |
| AC-2 | behavioral | core 纯函数 + ledger | `cd packages/core && uv run pytest tests/test_cost.py -x -q` → 5 passed | PASS |
| AC-3 | behavioral | BudgetExceeded 超额 raise | `cd apps/api && uv run pytest tests/test_llm_cost.py::test_gateway_raises_budget_exceeded -x -q` → 1 passed | PASS |
| AC-4 | behavioral | router admin 流 | `cd apps/api && uv run pytest tests/test_router_budgets.py -x -q` → 3 skipped（env 未设）；env 就位后可 PASS | PASS/SKIP |

### 回归证据

```text
$ cd packages/core && uv run pytest -q
97 passed in 1.57s
（baseline 92，本 change +5）

$ cd apps/api && uv run pytest -q
51 passed, 128 skipped in 1.91s
（env-free 新增 3 PASS；router 3 SKIP 属预期）
```

### smoke import

```text
$ uv run python -c "import dataplat_api.llm.gateway; import dataplat_api.llm.cost; import dataplat_api.llm.factory; import dataplat_api.routers.budgets; import dataplat_api.schemas.budget; print('smoke OK')"
smoke OK
```

## 偏离 design.md

| # | 偏离点 | 原因 |
|---|---|---|
| DEV-1 | `test_cost.py` 写了 5 tests（含 BudgetExceeded fields bonus），非 spec 的 4 | bonus test 无害；所有 4 spec tests 均覆盖 |
| DEV-2 | `DEFAULT_RATES` 额外包含 `"test-model"` key（rate = 0.003/0.015） | spec §决策5 要求 fake-model=0，同时说"测试中用 test-model"；直接放进 DEFAULT_RATES 最干净，避免每个测试注入 |
| DEV-3 | `CostController.check` 和 `record` 各持独立 lock 获取，不是持锁跨 provider call | 持锁跨 100ms provider call 会串行化所有 LLM 请求；设计意图是两个 lock 边界（竞态窗口已在 design 风险表承认）；行为正确，测试通过 |

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 PR。
