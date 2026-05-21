---
change_id: cost-budget-system-20260520
phase: design
status: approved
authored_at: 2026-05-21T11:10:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：LLM cost budget (W4-5，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

LLM 调用前用 per-repo monthly budget 预检 + 超额抛 402；每次 call 记 tokens / usd 到进程内 ledger，UI / 测试可读。

## 背景

`LLMGateway` 当前已：cache（RedisLLMCache）+ 指数退避 retry + 拿到 provider tokens（anthropic / fake 都填 `LLMResponse.input_tokens / output_tokens`）。但缺三件事：

1. **价格表**：tokens → USD 还没换算；
2. **per-repo 预算**：admin 给某个 repo 设月度上限就无法生效；
3. **超额 fail-fast**：用 image_caption_stub 拼大量图、或 LLM operator 跑大 batch 时没刹车。

W2-3 落了 `image_caption_stub` 占位算子（仍是文本拼接，**不真调 LLM**），W4-5 roadmap 写的"VLM"是 follow-up `operator-image-caption-llm-*` 的事，与 cost budget 系统正交。本 change 把 cost 抽象做对，让未来 `image_caption_llm` / `operator-eval-gen` / `operator-dpo-pair-gen`（W4-8/9）直接复用。

切入点选 **`LLMGateway` 装饰层**：所有调用必经此一点；不侵入 provider，也不要求每个 operator 自己上报 cost；天然单测。

## 范围

In scope：

- `packages/core/src/dataplat_core/cost.py`（新，~80 行）：
  - `class CostRate(BaseModel)`：`model_id: str`、`input_per_1k_usd: float`、`output_per_1k_usd: float`，`extra="forbid"`
  - `class CostLedgerEntry(BaseModel)`：`model_id`、`input_tokens`、`output_tokens`、`usd`、`scope: str`（caller 标识；默认 `"default"`）
  - `class CostLedger`：进程内累计器；`record(entry)` / `total_usd(scope=None) -> float` / `reset(scope=None) -> None`；线程安全用 `asyncio.Lock`（已在 asyncio 路径中）
  - `def compute_cost(rate: CostRate, input_tokens, output_tokens) -> float`：纯函数
  - 默认价格表常量 `DEFAULT_RATES: dict[str, CostRate]`，hard-coded 含 `claude-opus-4-7` / `claude-sonnet-4-6` / `claude-haiku-4-5-20251001` / `fake-model`（fake = 0/0）+ 一个 fallback `_DEFAULT_RATE`（input 0.003 / output 0.015 美元/1k tok，与 sonnet 当前价位一致）
  - `class BudgetExceeded(Exception)`：携带 `scope` / `current_usd` / `limit_usd` 三字段
- `apps/api/dataplat_api/llm/cost.py`（新，~60 行）：
  - `class CostController`：组合 `CostLedger` + `dict[scope, limit_usd]`；接口：
    - `set_budget(scope, limit_usd)`、`get_budget(scope) -> float | None`、`clear_budget(scope)`
    - `async def check(scope, projected_usd)`：projected + current > limit → raise `BudgetExceeded`；否则 noop
    - `async def record(scope, entry)`：调 ledger.record
    - `total_usd(scope) -> float`、`reset(scope)`
  - 进程内单例：`get_cost_controller() -> CostController`（`@lru_cache(maxsize=1)`，与 `get_llm_gateway` 同模式）
- `apps/api/dataplat_api/llm/gateway.py`（改，+~25 行）：`LLMGateway.__init__` 加 `cost: CostController | None = None`、`rates: dict[str, CostRate] | None = None`、`scope: str = "default"`；`call()` 流程改为：
  1. cache.get → 命中直接返（不计费；cache hit 是免费的）
  2. **预检**：若 `cost` 非 None，估算 `projected = compute_cost(rate, req.max_tokens, req.max_tokens)` 作上界（input/output 都按 max_tokens 计；保守保护）→ `await cost.check(scope, projected)` → 超额 raise `BudgetExceeded`
  3. provider.call(...)（保留现有 retry 逻辑）
  4. **后置 record**：用 resp 真实 tokens 算 `usd = compute_cost(rate, resp.input_tokens, resp.output_tokens)` → `await cost.record(scope, entry)`
  5. cache.set + return
- `apps/api/dataplat_api/llm/factory.py`（改，+~10 行）：`get_llm_gateway()` 把 controller / rates 注入 `LLMGateway`
- `apps/api/dataplat_api/routers/budgets.py`（新，~80 行）：
  - `POST /repos/{owner}/{name}/llm-budget`：body `{ limit_usd: float, reset_window: "monthly" }`（reset_window 仅 monthly，预留字段；当前不真做月度滚动重置，进程重启即清）→ 200 `{ scope, limit_usd, current_usd }`
  - `GET /repos/{owner}/{name}/llm-budget`：返 `{ scope, limit_usd: float | null, current_usd: float, breakdown: list[{model_id, input_tokens, output_tokens, usd}] }`
  - `DELETE /repos/{owner}/{name}/llm-budget`：清预算 + ledger reset；200 `{ scope, cleared: true }`
  - scope 编码：`repo:{repo_id}`（uuid str）；从 `_resolve_repo` 拿 repo 后用 `repo.id`
  - 视为 admin-only：`Depends(require_admin_user)`；非 admin → 403
- `apps/api/dataplat_api/main.py`（小改）：注册 `budgets.router`
- 测试：
  - `packages/core/tests/test_cost.py`（新，4 tests）：
    - `compute_cost` 纯函数：1k input + 1k output ≠ 0；fake-model rate = 0 → 0
    - `CostLedger.record + total_usd` 累计正确
    - `CostLedger.reset` 清空 scope；其他 scope 不受影响
    - `BudgetExceeded` 携带 scope / current / limit
  - `apps/api/tests/test_llm_cost.py`（新，3 tests）：
    - LLMGateway 用 FakeLLMProvider + CostController + DEFAULT_RATES 跑 3 次 → ledger.total_usd > 0（fake = 0 → 改用一个 rate 非 0 的 `model_id`，例如 stub `"test-model"`）
    - 预算 0.0001 USD + 跑 N 次直到累计 > 限额 → 下一次 raise `BudgetExceeded`，scope / current / limit 字段正确
    - 预算 None → 永远不 raise（无预算 = 无限制）
  - `apps/api/tests/test_router_budgets.py`（新，3 tests，env-gated 与 W4-1 同模式）：
    - POST budget 设 + GET 拿到（admin）
    - 非 admin → 403
    - DELETE 清

Out of scope：

- **不**做月度滚动重置：MVP；按"进程内 ledger + 进程重启即清"实现；真月度持久化留 follow-up `cost-budget-persist-monthly-*`
- **不**入 DB 表（budgets / ledger）：MVP 进程内 dict；持久化 / 跨 worker 共享留 follow-up `cost-budget-persist-*`（DB schema + alembic migration）
- **不**做 per-row cost stats（roadmap 提到，但 row.stats 写入需 Operator 侧改）：留 follow-up `silver-row-cost-stats-*`
- **不**做 cost dashboard UI：留 follow-up `web-cost-dashboard-*`
- **不**做 cache hit 也计费（不计；cache hit 视为零成本）
- **不**接 dataset-card.yaml / manifest.yaml（D-1）
- **不**改 packages/core 价格之外的内容；价格表 hard-coded 在 cost.py
- **不**做 alembic migration

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | cost.py + CostController 存在 + 导出 BudgetExceeded | `python -c "from dataplat_core.cost import CostLedger, BudgetExceeded, compute_cost, DEFAULT_RATES; from dataplat_api.llm.cost import CostController, get_cost_controller; print('OK')"` | 输出 OK |
| AC-2 | behavioral | core 纯函数 + ledger 行为 | `cd packages/core && uv run pytest tests/test_cost.py -x -q` | 4 passed |
| AC-3 | behavioral | LLMGateway 集成：限额 0.0001 USD + 跑到累计 > 限额 → 下一次 BudgetExceeded（含 scope / current / limit 字段） | `cd apps/api && uv run pytest tests/test_llm_cost.py::test_gateway_raises_budget_exceeded -x -q` | 1 passed |
| AC-4 | behavioral | router admin 流：POST 设 0.5 → GET 拿到 limit_usd=0.5 + current_usd=0；非 admin POST → 403 | `cd apps/api && uv run pytest tests/test_router_budgets.py -x -q` | 3 passed (env 就位) / skipped (env 缺) |

## 决策

1. **per-repo scope = `repo:{repo_id}`**：scope 串到 ledger / controller，便于未来扩展到其他粒度（如 `user:{id}` / `pipeline:{id}`）；现在只用 repo scope。
2. **进程内 ledger + 进程重启即清**：MVP；DB / Redis 持久化是独立改动量（含序列化 + cross-worker 一致性）；留 follow-up。当前 apps/api 是单 worker uvicorn 部署，进程内 OK。
3. **cache hit 不计费 + 不预检**：cache hit 不调 provider，无外部成本；用户预算逻辑应当是"控制 provider 调用 cost"而非"控制 LLM 调用次数"。
4. **预检用 max_tokens 作上界**：保守保护（避免"刚好到限额就放过去 + 实际 output 超了"）；牺牲 5-10% 假阴性精度换严格刹车。
5. **DEFAULT_RATES 含 `fake-model` 行 + 价格 = 0**：保持 CI 默认 FakeLLMProvider 跑测试不被预算阻断；切到 anthropic 时按真价格计费。
6. **价格表 hard-coded 在 `packages/core/cost.py`**：避免引入 env 配置 / YAML 加载；价格变更走 PR 修常量；动态价格表留 follow-up `cost-rates-dynamic-*`。
7. **scope 不接受 user 输入**：scope 由 router 用 `repo.id` 算出；防止恶意 user 改 scope 绕过预算。
8. **CostController 注入 LLMGateway 而非 monkey-patch**：构造函数参数；factory 装；测试可独立构造 LLMGateway(controller=...) 不依赖单例。
9. **router 在 admin 路径下**：写预算属敏感操作；require_admin_user dependency 与 W3-1..W3-3 admin 端点一致。
10. **breakdown 按 model_id 聚合**：UI / 未来 dashboard 能看"哪个模型花了多少"；ledger 实现 `breakdown(scope) -> list[dict]`。
11. **预算 0 vs None 语义不同**：None = 无限制；0.0 = 已经超额（任何调用 raise）；显式区分语义。
12. **`require_admin_user`**：若 apps/api/auth 尚无此 helper，则就近用 W3-1..3 同模式 dependency；spec 后 sonnet 实测；缺失则 inline 一个简单 dependency 检查 `user.is_admin`。

## 风险

| 风险 | 缓解 |
|---|---|
| `get_cost_controller` 单例与测试隔离 | 测试用 `reset_cost_controller()` helper 清掉单例（与 `reset_llm_gateway` 同模式）；test fixture 中显式 reset |
| 预检 + record 的并发竞态（两 caller 同时预检都过、record 后超额） | asyncio.Lock 包 check + record；CostController.check 与 record 都 await lock；性能损失可接受（LLM call 本就 ~100ms+） |
| anthropic provider tokens 字段缺失（旧 SDK 版本） | `getattr(..., 0)` 已兜底；cost = 0 → ledger 加 0；不阻 |
| 用户在 routers/budgets.py 设负数 limit | pydantic schema `ge=0`；422 |
| `require_admin_user` dependency 名 / 路径不存在 | spec 写明"若缺则 fallback 内联"；sonnet 决定 |
| DEFAULT_RATES 漏某 model_id → fallback rate | _DEFAULT_RATE 兜底；ledger 仍正常记 |
| 单进程 ledger 在 multi-worker uvicorn 下不共享 | 当前部署单 worker；follow-up persist 解决 |
| follow-up `image-caption-llm-*` 落地后真发 LLM 请求 | 本 change 在 Gateway 层卡住；新 operator 无需改 cost 代码 |
| 进程内 ledger 在长跑后内存增长 | ledger entries 是 dict 累计，N 个 scope * M 个 model_id；当前业务规模 < 1k 条；超 follow-up GC |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/llm.py`（LLMRequest / LLMResponse）
  - `apps/api/dataplat_api/llm/cache.py`（cache hit 路径不计费）
  - `apps/api/dataplat_api/llm/providers/fake.py`（测试用）
  - `apps/api/dataplat_api/auth/`（require_admin_user / get_current_user）
- 应当不动：
  - `packages/core/src/dataplat_core/operators/*`（cost 注入对 operator 透明）
  - W1-* / W2-* / W3-* / W4-1..W4-4 已 merge 产物
  - alembic versions（本 change 不加表）
- 引用的其他 change：W2-3（image_caption_stub，不真调 LLM）、`operator-image-caption-llm-*`（follow-up，本 change 是其前置）

## 关联 follow-up

- `cost-budget-persist-*`：ledger / budget 入 DB + alembic + cross-worker
- `cost-budget-persist-monthly-*`：reset_window 真月度滚动
- `silver-row-cost-stats-*`：Operator 把 row.stats.cost_usd 写入 silver row
- `web-cost-dashboard-*`：UI 看 breakdown / 历史 / per-repo
- `cost-rates-dynamic-*`：价格表配置化（YAML / DB）
- `operator-image-caption-llm-*`：W2-3 占位算子的真 VLM 版本（消费本 change 的 budget 系统）
