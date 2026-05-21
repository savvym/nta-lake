---
change_id: cost-budget-system-20260520
phase: merged
status: closed
verdict: APPROVED
closed_at: 2026-05-21T13:15:00Z
merge_commit: 9c73af66753d61a91317986f6c829bc90c333e67
branch: change/cost-budget-system-20260520
base_commit: 95f55e7
head_commit: 1b8f776
---

# Summary：W4-5 LLM cost budget + 402 + per-scope ledger

## 一句话结果

`LLMGateway` 装饰层加 cost 预检 + 后置 record：cache miss → 用 req.max_tokens 估上界 → `CostController.check(scope, projected)` 超额抛 `BudgetExceeded` → provider call → 用 resp 真实 tokens 算 USD → `record(scope, entry)`。新 admin 路由 `POST/GET/DELETE /repos/{owner}/{name}/llm-budget` 让管理员设/查/清 per-repo 月度预算。0 issue APPROVED 一气呵成 merge。

## 关键决策

1. **per-repo scope = `repo:{repo_id}`**：scope 串到 ledger / controller；future 可扩 `user:{id}` / `pipeline:{id}` 粒度。
2. **进程内 ledger + 进程重启即清**：MVP；DB / Redis 持久化 + cross-worker 一致性留 follow-up `cost-budget-persist-*`。
3. **cache hit 不计费 + 不预检**：cache hit 无外部 provider 成本，预算逻辑控的是"provider 调用 cost"。
4. **预检用 max_tokens 作上界**：保守保护避免"刚好到限额放过去而 output 超了"，牺牲 5-10% 假阴性精度换严格刹车。
5. **DEFAULT_RATES 含 `fake-model`（rate=0）+ `test-model`（rate=0.003/0.015）**：fake-model 保证 CI FakeLLMProvider 不被预算阻断；test-model 让单元测试有非零计费断言。
6. **价格表 hard-coded 在 `packages/core/cost.py`**：避免引入 env / YAML；动态价格表留 `cost-rates-dynamic-*` follow-up。
7. **`_DEFAULT_RATE` fallback**：未知 model_id 用 sonnet 价位（0.003/0.015 USD per 1k tok），ledger 仍能正常累计。
8. **scope 由 router 用 `repo.id` 算**：不接受 user 输入，防恶意改 scope 绕预算。
9. **CostController 通过构造函数注入 LLMGateway**：非 monkey-patch；测试可独立构造不依赖单例。
10. **admin only 路由**：`require_admin` dependency，非 admin → 403（W3-1..W3-3 同模式）。
11. **breakdown 按 model_id 聚合**：UI / 未来 dashboard 能看"哪个模型花了多少"。
12. **预算 0 vs None 语义不同**：None = 无限制；0.0 = 已超额（任何正 projected 都 raise）。
13. **DEV-3 lock 选择**：`check` 与 `record` 各自加 `asyncio.Lock` 但不持锁跨 provider call（~100ms）；竞态窗口在 design §风险表已承认。

## 测试结果

| 范围 | 结果 |
|---|---|
| AC-1 import smoke | PASS（core + api 双双 OK） |
| AC-2 core test_cost | 5 passed in 0.08s（design 写 4 + DEV-1 bonus 1） |
| AC-3 gateway env-free | 3 passed in 0.36s（含 test_gateway_raises_budget_exceeded） |
| AC-4 router env-gated | 3 skipped（与 W4-1/W4-4 同模式；env 就位即 PASS） |
| packages/core 全量 | 97 passed in 1.32s（baseline 92 + 5） |
| apps/api 全量 | 51 passed + 128 skipped in 1.85s（零回归） |

## 改动文件

10 files / +1493 −22：

- `packages/core/src/dataplat_core/cost.py`（new，180 行）
- `apps/api/dataplat_api/llm/cost.py`（new，107 行）
- `apps/api/dataplat_api/llm/gateway.py`（+62 −0）：cost/rates/scope 注入 + pre-check + post-record
- `apps/api/dataplat_api/llm/factory.py`（+13 −0）
- `apps/api/dataplat_api/schemas/budget.py`（new，48 行）
- `apps/api/dataplat_api/routers/budgets.py`（new，119 行）
- `apps/api/dataplat_api/main.py`（+2 行）
- `packages/core/tests/test_cost.py`（new，140 行，5 tests）
- `apps/api/tests/test_llm_cost.py`（new，133 行，3 env-free tests）
- `apps/api/tests/test_router_budgets.py`（new，248 行，3 env-gated tests）

**零新依赖**（asyncio / pydantic 既有）。

## 跨 change / D-1 检查

- packages/core 仅新增 `cost.py` + tests，零 edit
- W1..W4-4 已 merge 产物零回归
- W4-4 main.py 新增 budgets_router 与已有 snapshots_router 并存无冲突
- D-1 永不做清单零命中（无 manifest.yaml / 无 dataset-card.yaml / 无 row-diff / 无 cherry-pick / 无 rollback / 无 alembic migration / 无 DB schema 改）

## Verdict / Merge

- Phase 3 reviewer (opus)：**APPROVED**（0 issue / 0 MUST FIX / 0 SHOULD FIX）
- 3 个声明偏离全部 ACCEPT（DEV-1 bonus test / DEV-2 test-model 入 DEFAULT_RATES / DEV-3 check+record 各自加锁）
- Merge commit：`9c73af66753d61a91317986f6c829bc90c333e67`
- 关联 follow-up（design 已列）：`cost-budget-persist-*` / `cost-budget-persist-monthly-*` / `silver-row-cost-stats-*` / `web-cost-dashboard-*` / `cost-rates-dynamic-*` / `operator-image-caption-llm-*`

## 下一步

启动 W4-6 `integration-test-framework-*`（playwright e2e；W3 done + W4-1..4 UI 已 merged，前置充足）。
