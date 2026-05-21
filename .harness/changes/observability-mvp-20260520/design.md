---
change_id: observability-mvp-20260520
phase: design
status: approved
authored_at: 2026-05-21T13:55:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：observability MVP (W4-7，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

run_recipe_v2 跑 operator 时埋点 → 进程内 metrics registry → GET /metrics 暴露 → `/observability` UI 表格读。

## 背景

W2-5 落了 `run_recipe_v2`：进程内同步执行 `Loader → Operator 链`，最终返 `RecipeRunResult(rows, total_input, total_output, loader_notes)`。但每个 Operator 的"处理 row 数 / 失败率 / 耗时"是**黑箱**——recipe 跑完只能拿到链路终值，不知道：

1. `pii_strip` 处理了多少 row、丢了多少（1→0 过滤语义可见性=0）
2. `chunker` 把 1→N 时 N 实际是多少
3. 哪个 operator 慢（dpo-pair-gen / image_caption_llm 等 LLM-bound operator 落地后会更需要）
4. 哪个 operator 抛了多少 exception（当前 run_recipe_v2 没 try，第一个异常直接冒泡；observability 引入后第一步先**记 metrics** 再 raise，不改变错误语义）

W4-7 roadmap：metrics 埋点 + 简单 dashboard。前置 W2-5（recipe 执行器）+ W4-5（cost ledger 也是进程内累计器，本 change 复用 asyncio.Lock 同模式）已就位。

切入点：
- `packages/core/metrics.py` 提供 in-process `MetricsRegistry`（counter + histogram；`record_op_run(operator_name, rows_in, rows_out, duration_ms, error)`；`snapshot() -> list[OperatorMetrics]`）
- 在 `run_recipe_v2` 的 operator 循环里埋点（不改原有错误语义；失败时记 error_count 后 re-raise）
- `apps/api/dataplat_api/routers/metrics.py` 暴露 GET `/metrics`（admin only，复用 require_admin dependency）
- `apps/web/src/routes/observability.tsx` 简单表格读 `/metrics`，每 5s 轮询

价值定位：W4-8（eval-gen）/ W4-9（dpo-pair-gen）落地后立即受益——无需各 operator 自己埋点，registry 在 Operator 链层"装饰"自动覆盖。

## 范围

In scope：

- `packages/core/src/dataplat_core/metrics.py`（新，~110 行）：
  - `class OperatorMetrics(BaseModel)`：`operator_name: str`、`runs: int`、`rows_in: int`、`rows_out: int`、`errors: int`、`duration_ms_total: float`、`duration_ms_avg: float`（计算属性），`extra="forbid"`
  - `class MetricsRegistry`：进程内累计器；
    - `record_op_run(operator_name, rows_in, rows_out, duration_ms, error: bool=False) -> None`（async；asyncio.Lock 保并发，与 [[cost-ledger-asyncio-lock]] 同模式）
    - `snapshot() -> list[OperatorMetrics]`（不加锁；返按 operator_name 排序的快照）
    - `reset() -> None`（async；测试隔离用）
  - 进程内单例：`get_metrics_registry() -> MetricsRegistry`（`@lru_cache(maxsize=1)`，与 [[cost-controller-singleton]] / `get_llm_gateway` 同模式）
  - `reset_metrics_registry() -> None`：清单例（测试用）
- `packages/core/src/dataplat_core/recipe.py`（改，+~25 行）：`run_recipe_v2` 改造：
  - import `get_metrics_registry`、`time.perf_counter`
  - operator 循环里：
    ```python
    rows_in_count = len(rows)
    t0 = perf_counter()
    try:
        for row in rows:
            new_rows.extend(op.run(row, op_spec.config, ctx))
    except Exception:
        duration_ms = (perf_counter() - t0) * 1000
        await registry.record_op_run(op_spec.name, rows_in_count, 0, duration_ms, error=True)
        raise
    duration_ms = (perf_counter() - t0) * 1000
    await registry.record_op_run(op_spec.name, rows_in_count, len(new_rows), duration_ms)
    rows = new_rows
    ```
  - **`run_recipe_v2` 改为 async** 以支持 `await registry.record_op_run`：
    - 函数签名：`async def run_recipe_v2(...)`
    - 现有 2 个 caller 都在 test 中：`test_recipe_v2.py::test_run_recipe_v2_end_to_end` / `test_run_recipe_v2_empty_operators`；改为 `@pytest.mark.asyncio` + `await run_recipe_v2(...)`
    - **关键约束**：测试中要 `reset_metrics_registry()` + `pytest.mark.asyncio`；保持其余断言不变
- `apps/api/dataplat_api/routers/metrics.py`（新，~50 行）：
  - `GET /metrics`：`Depends(require_admin)` → `registry.snapshot()` → 返 `{ operators: list[OperatorMetrics], collected_at: datetime.utcnow().isoformat() }`
  - 非 admin → 403（与 W3-1..W3-3 admin 路径同模式）
  - 不复用 `prometheus_client` 等库（增依赖；MVP json 足够；prometheus exposition 留 follow-up）
- `apps/api/dataplat_api/main.py`（小改，+2 行）：注册 `metrics.router`
- `apps/web/src/lib/api/queries.ts`（改，+~15 行）：新增 `useMetrics()`（`useQuery`，`refetchInterval: 5000`）
- `apps/web/src/routes/observability.tsx`（新，~60 行）：
  - createFileRoute("/observability")
  - 表格列：operator / runs / rows_in / rows_out / errors / avg duration (ms)
  - 顶部 collected_at + "每 5s 自动刷新" 文案
  - 401/403 时显示 "需要 admin 权限"（W4-1 同模式）
- `apps/web/src/routes/__root.tsx`（小改）：admin 用户额外显示 "Observability" Link 指向 `/observability`（与 Jobs Link 同位）
- `apps/web/src/routeTree.gen.ts`（小改）：注册 ObservabilityRoute（手编辑前先跑 dev server 自动生成，沿用 W4-3/W4-4 模式）
- 测试：
  - `packages/core/tests/test_metrics.py`（新，4 tests）：
    - `record_op_run` happy path：记 N 条 → snapshot 含 N runs + 正确 rows_in/out 累计
    - `record_op_run` error=True：errors 自增 1；rows_out 不计
    - `snapshot` 排序：多 operator 按 name 字母序
    - `reset` 清空 registry
  - `packages/core/tests/test_recipe_v2.py`（改，+1 test）：
    - `test_run_recipe_v2_records_metrics`：跑 [filter, chunker] → snapshot 含 2 个 entry + 各自 rows_in/out 正确
    - 原 2 个 test 改为 async（保留行为断言）
  - `apps/api/tests/test_router_metrics.py`（新，2 tests，env-gated 与 W4-1 同模式）：
    - admin GET → 200 + JSON 字段齐
    - 非 admin GET → 403
  - `apps/web/src/routes/observability.test.tsx`（新，2 tests，vi.mock pattern）：
    - 渲染表格 + mock 数据 3 个 operator → 3 行
    - 403 → 显示 "需要 admin 权限"

Out of scope：

- **不**接 prometheus / opentelemetry：MVP；引入 prometheus_client 是新依赖 + exposition format 多一层 mental load；留 follow-up `metrics-prometheus-export-*`
- **不**做指标持久化（DB / Redis）：进程重启即清；留 follow-up `metrics-persist-*`
- **不**做跨 worker 聚合：当前单 worker uvicorn 部署 OK；多 worker / k8s 部署留 follow-up `metrics-cross-worker-*`
- **不**做 histogram / percentile：MVP 只算 avg；P50/P99 留 follow-up `metrics-percentile-*`
- **不**埋点 Loader / Adapter：W4-7 roadmap 文字只提 Operator；Loader 埋点留 follow-up `metrics-loader-instrument-*`（Loader 链 W2-5 内调 1 次，价值较 Operator 链低）
- **不**做指标 panic 报警：留 follow-up `metrics-alert-*`
- **不**做 cost 与 metrics 双向联动（如显示每 operator 的 cost_usd）：W4-5 ledger 是 `(scope, model_id)` 维度，与 operator_name 正交；联动留 follow-up `metrics-cost-merge-*`
- **不**改 W4-5 cost 系统（cost 跟 metrics 各自独立 registry，符合"两个独立切面"）
- **不**改 packages/core / W1..W4-6 任何 merged 产物，除 `recipe.py::run_recipe_v2` 改 async（必要副作用）
- **不**做 alembic migration（无 DB schema）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | metrics.py 存在 + 导出 MetricsRegistry / OperatorMetrics / get_metrics_registry / reset_metrics_registry | `python -c "from dataplat_core.metrics import MetricsRegistry, OperatorMetrics, get_metrics_registry, reset_metrics_registry; print('OK')"` | 输出 OK |
| AC-2 | behavioral | core 测试：record + snapshot + reset 行为正确（4 tests） | `cd packages/core && uv run pytest tests/test_metrics.py -x -q` | 4 passed |
| AC-3 | behavioral | run_recipe_v2 埋点：跑 [filter, chunker] → snapshot 含 2 个 operator entry + rows_in/out 计数正确 | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_records_metrics -x -q` | 1 passed |
| AC-4 | behavioral | router admin 流：admin GET /metrics 200 含 `operators` + `collected_at`；非 admin 403 | `cd apps/api && uv run pytest tests/test_router_metrics.py -x -q` | 2 passed (env 就位) / skipped (env 缺) |

> 注：AC-4 在 docker 缺位 (无 DB) 时 SKIP；与 W4-1 / W4-5 同模式。验证报告中需明示哪种状态。

## 决策

1. **registry 在 packages/core 而非 apps/api**：Operator 在 packages/core 跑；埋点应跟 operator 同进程同 import 层。apps/api 路由读 registry 即可（同进程单例）。
2. **进程内单例 + asyncio.Lock**：与 [[cost-ledger-asyncio-lock]] 完全同模式；MVP；跨 worker / 持久化是独立改动。
3. **run_recipe_v2 改 async**：唯一被迫的 breaking change（callers 都在 test 中）；async 是必要的，因为 `record_op_run` 内 `asyncio.Lock`。**替代方案**：同步 `threading.Lock` → 可避免改 async；但 packages/core 现有 cost.py 与 LLMGateway 都已 asyncio.Lock，统一 async 模式更一致；callers 都在 test 中（grep 确认），改动量小。
4. **失败时先记 metrics 再 raise**：保留原有错误冒泡语义不变；只多记一条 `error=True` entry；不吞 exception。
5. **埋点粒度=Operator 不是单 row**：1→N 链路下，per-row 埋点会爆量；按 operator 总览统计 rows_in / rows_out 即可。
6. **`/metrics` 路径选了 RESTful 名而非 prometheus 默认**：prometheus 用 `/metrics` 期望特定 exposition format（`# HELP ...` text）；我们这是 JSON，但 path 名一致——admin 直接 curl 看 JSON；若未来接 prometheus，新增 `/metrics/prometheus` follow-up 即可，不冲突。
7. **`refetchInterval: 5000` 而非 server-sent events / websocket**：MVP；5s 轮询对单 worker / 单 user 场景够用；SSE / WS 是 follow-up `metrics-live-stream-*`。
8. **观察页面无 chart 库**：纯表格；引入 chart 库（recharts / chart.js）= 新依赖 + bundle 体积；MVP 表格够 demo；留 follow-up `web-observability-charts-*`。
9. **admin only**：metrics 含运行时间 / 错误率，敏感度中等；与 jobs / budgets 同访问级别。
10. **OperatorMetrics 不包含 last_run_at**：snapshot 时间放顶层 `collected_at`；per-operator last_run 增锁竞争或额外字段，价值低。
11. **不在 `run_recipe_v2` 包 `try/except` 整个 operator 循环**：现有 `for op_spec in recipe.operators` 是顶层；只对内层 `for row in rows` 包 try（精确捕获哪个 operator 异常），保持现有"第一个 exception 冒泡"行为。
12. **测试改 async 显式 import `pytest_asyncio` 或用 `@pytest.mark.asyncio`**：packages/core 现有 `pyproject.toml` 应已含 `pytest-asyncio`（W4-5 cost 测试已用）；若缺补 dev dep。

## 风险

| 风险 | 缓解 |
|---|---|
| run_recipe_v2 改 async 破坏现有 caller | grep 确认仅 2 个 test caller；改 async；其余 W1..W4-6 不调；apps/api/runner/orchestrator 用的是 v1 Recipe，不动 |
| asyncio.Lock 序列化 operator 调用 | record_op_run 内只更新 dict（~微秒），锁开销远小于 operator 本身（loader/llm ms 级）；与 [[cost-ledger-asyncio-lock]] 同 |
| 进程重启后 metrics 清零 | MVP 接受；UI 顶部显示 "进程启动以来" + collected_at；follow-up persist |
| 多 worker uvicorn 下指标分裂 | 当前部署单 worker；deploy 增多 worker 时 metrics 各自独立；follow-up cross-worker |
| `get_metrics_registry` 单例测试干扰 | `reset_metrics_registry()` helper（与 reset_cost_controller / reset_llm_gateway 同模式）；test fixture 显式 reset |
| operator 抛 KeyError / ValueError 后 raise 改变了原有 traceback 行 | except 不改 exception 类型也不 chain；用 `raise` re-raise 保 traceback；与原行为一致 |
| TanStack route gen 文件冲突 | 同 W4-3/W4-4 模式：sonnet 先跑 web devserver 让其自动生成，再手工 review；冲突时复制 W4-4 已有 entry 旁加新 entry |
| __root.tsx 加 admin nav link 影响现有路由测试 | W4-1 W4-2 W4-3 W4-4 测试都未断言 nav 内容（只断言 children Outlet）；本 change 增 Link 不影响 |
| Loader 长跑时 metrics 不更新（用户看不到 in-progress） | MVP 接受；run_recipe_v2 是同步顺序执行，operator 跑完才 record；UI 5s 轮询会看到 "完成后" 状态；流式埋点留 follow-up |
| pytest-asyncio 与现有 conftest 冲突 | packages/core 已用 asyncio（W4-5）；conftest 不需改 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/operator.py`（Operator Protocol，不动）
  - `packages/core/src/dataplat_core/recipe.py::RecipeRunResult`（schema 不变）
  - `apps/api/dataplat_api/auth/deps.py::require_admin`（W3-1..3 复用）
  - `apps/web/src/lib/api/client.ts::fetchJson`（GET helper 复用）
- 应当不动：
  - `packages/core/src/dataplat_core/cost.py`（cost 与 metrics 各自独立 registry）
  - `apps/api/dataplat_api/llm/gateway.py`（cost 切面，metrics 不动它）
  - W1..W4-6 已 merge 产物（除 run_recipe_v2 改 async 外）
- 引用的其他 change：W2-5（recipe-yaml-v2 / run_recipe_v2）、W4-5（cost-budget-system，参考 ledger + Lock + 单例模式）

## 关联 follow-up

- `metrics-prometheus-export-*`：prometheus exposition format（/metrics/prometheus）
- `metrics-persist-*`：DB / Redis 持久化（重启不丢）
- `metrics-cross-worker-*`：多 worker 下 metrics 聚合（共享内存 / Redis）
- `metrics-percentile-*`：histogram + P50/P99
- `metrics-loader-instrument-*`：Loader 链埋点（adapter / loader 调用次数 / 时长）
- `metrics-alert-*`：异常率 / 慢 operator 阈值报警
- `metrics-cost-merge-*`：observability 表加 cost_usd 列（与 W4-5 ledger 关联）
- `metrics-live-stream-*`：SSE / WebSocket 替代 5s 轮询
- `web-observability-charts-*`：表格 → recharts 时间序列
