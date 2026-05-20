---
change_id: web-jobs-list-page-20260520
review_of: coding/coding_report_v1.md
reviewer: claude-stage4-reviewer
version: 1
authored_at: 2026-05-20T15:30:00Z
verdict: REVISION REQUIRED
---

# Code Review v1 — Stage 4 编码评审

## 机械化检查清单

| ID | 检查项 | 结论 | 原因 |
|---|---|---|---|
| A | 路径决策 D-1 folder routing 形态合理性 | PASS | `routes/jobs/index.tsx` + `routes/jobs/$job_id.tsx` 形态正确；`routeTree.gen.ts` 生成 `JobsIndexRoute` (path `/jobs/`) 与 `JobsJob_idRoute` (path `/jobs/$job_id`)；`FileRoutesByTo` 中 `/jobs` 即 `JobsIndexRoute`，`<Link to="/jobs">` 可兼容引用 |
| A2 | 迁移完整性（无 dangling flat 文件） | PASS | `routes/` 顶层无 `jobs.tsx`/`jobs.test.tsx` stale 文件；`routes/jobs/` 目录含 4 个文件 |
| B | 路由顺序：`@router.get("")` 在 `@router.get("/{job_id}")` 之前 | PASS | `routers/jobs.py` 第 65 行 `@router.get("")` 先于第 100 行 `@router.get("/{job_id}")`；FastAPI 顺序正确 |
| C | 白名单常量位置与 400 detail | PASS | `_ALLOWED_STATUS` 和 `_ALLOWED_TYPE` 定义在文件顶部（第 22-23 行）；400 detail 含具体允许值（`sorted(_ALLOWED_STATUS/TYPE)`） |
| D | `service.list_jobs` 实现：filters list 累积、count/stmt 分开构建、`int(total)` | PASS | `filters = []` 累积 → `count_stmt` 独立 where 循环（无 LIMIT 干扰）→ `stmt` 独立循环 → `int(total)` 显式转型；pattern 合规 |
| E | admin 限制：`_admin: AuthenticatedUser = Depends(require_admin)` | PASS | 与同文件 `enqueue_ingest_job` 的 `admin: AuthenticatedUser = Depends(require_admin)` 模式一致 |
| F | `useJobs` queryKey 稳定性与 null 退化 | PASS | queryKey 为 `["jobs", status ?? "", type ?? "", limit, offset]` 全基础值；`queryFn` 中 `r === null` 时抛错 |
| G1 | `jobs/index.tsx` 过滤控件完整性 | PASS | status select / type select / page size select 均实现；StatusBadge / formatRelativeTime / formatDuration / summarizePayload 均有；"无 jobs" / "加载中" / "加载失败" 文本均存在；Refresh 按钮调 `invalidateQueries({ queryKey: ["jobs"] })` |
| **G2** | **React Rules of Hooks 合规性** | **FAIL** | `useJobs` 在第 72 行调用，位于第 41 行 `if (!me) return` 和第 53 行 `if (me.role !== "admin") return` 两个 early return **之后**；违反 React Rules of Hooks（hooks 不得在条件分支后调用）；`useMe` 首次 render 返回 `{ data: undefined }` → `me` 为 undefined → early return，**不调用 `useJobs`**；下次 render me 解析后调用 useJobs → hooks 调用数量变化 → runtime 抛 "Rendered more hooks than during the previous render" |
| H | `__root.tsx` admin-only link | PASS | 第 33 行 `me.role === "admin"` 条件包裹；`<Link to="/jobs" search={{ status: "", type: "", limit: 50, offset: 0 }}>`；默认 search 合理（offset=0/limit=50 与 searchSchema default 一致） |
| I | spec.md AC-5 修订充分性 | PASS | spec v3 AC-5 grep 已匹配 `jobs/index.tsx` + `createFileRoute("/jobs/")`；AC-8 命令含 `DATAPLAT_COOKIE_SECURE=false` |
| I2 | NTH-1（AC-8 命令 `|| true` 保护） | PASS | spec AC-8 完整命令已含 `|| true`（`grep -cE ... || true`） |
| J | 跨 change 修正合理性（web-write-flows AC-2 路径） | PASS | `_self_check.sh` 第 844-845 行 AC-2 已改为 `jobs/$job_id.tsx`；单行修正，无需独立 change |
| P | `git diff --stat` 路径一致性 | PASS | coding_report 文件清单与工作树文件一致（已逐一核查）；`routeTree.gen.ts` 已重新生成 |
| Q | 静态验证：typecheck / ruff | PASS（信任报告）| coding_report 声明 0 errors；ESLint 未引入（hooks 问题无法被自动捕获） |
| R | AC kind lint | PASS | spec AC-7 / AC-8 均标记 behavioral；non-exempt change 满足 ≥ 2 条 behavioral |
| S | self_check AC block 覆盖 | PASS | `run_web_jobs_list_page` 含 10 AC；dispatcher 与 full 链均包含；AC-9 见下 SHOULD FIX |

---

## 问题列表

### MUST FIX

#### MUST-1：React Rules of Hooks 违反 — `useJobs` 在条件 return 之后调用

**文件**：`apps/web/src/routes/jobs/index.tsx`，第 41 行 / 第 53 行 / 第 72 行

**问题**：

```tsx
// 第 41 行：conditional early return
if (!me) { return <Card>...</Card>; }
// 第 53 行：conditional early return
if (me.role !== "admin") { return <Card>...</Card>; }

// 第 72 行：useJobs 在两个 early return 之后调用 ← VIOLATION
const jobsQuery = useJobs(filters);
```

React 规则要求：hooks 必须在每次 render 以相同数量、相同顺序调用。`useMe` 首次 render 时返回 `{ data: undefined }`（`allowAnon: true`，查询未完成），组件走第 41 行 early return，**不调用 `useJobs`**。当 `useMe` 查询完成后，组件 re-render，`me` 存在、role 为 admin → 执行到第 72 行调用 `useJobs`。Hooks 调用次数从 N 变为 N+1，React 抛 runtime 错误："Rendered more hooks than during the previous render."

此问题在 vitest 测试中不出现，因为 mock 同步返回 `currentMe`（无异步过渡）。但在浏览器真实场景（`useMe` 有网络 round-trip）必然触发。

**修复方向**（不改代码，仅指出）：将所有 hooks 调用提至 early return 之前；或将 admin-only 逻辑从条件返回改为条件渲染（参考 `repos/index.tsx` 中 `useRepos()` 无条件调用的模式）。例如：

```tsx
// 正确模式：所有 hooks 无条件调用在最前
const { data: me } = useMe();
const search = Route.useSearch();
const navigate = Route.useNavigate();
const qc = useQueryClient();
const filters = { status: search.status || undefined, ... };
const jobsQuery = useJobs(filters);  // ← 无条件调用

// 之后用条件渲染而非 early return
if (!me) return <Card>未登录...</Card>;
if (me.role !== "admin") return <Card>仅 admin 可见...</Card>;
// ... 其余 UI
```

注意：`filters` 在 `me` 未知时仍能构建（`search` 来自 URL params，总是有值）；`useJobs` 在非 admin 情况下会发出 403 请求，但这可以通过 `enabled: me?.role === "admin"` 来抑制，或接受 403 抛错（非 admin 渲染分支不会展示数据）。

---

### SHOULD FIX

#### SHOULD-1：self_check AC-9 缺失 mypy 检查

**文件**：`scripts/_self_check.sh`，第 1656-1657 行

**问题**：spec AC-9 要求 `pnpm typecheck && ruff check && mypy`，self_check AC-9 实现只运行 `pnpm typecheck + ruff`，**无 mypy**：

```bash
# self_check AC-9（实际）
bash -c '(pnpm --filter web typecheck ...) && ! grep -qE "error TS" ... && \
  (cd apps/api && uv run ruff check dataplat_api ...) && ! grep -qE "..." ...'
```

mypy 缺失意味着 AC-9 门禁无法机械化确认 mypy PASS 状态。

**建议**：在 self_check AC-9 追加 `uv run mypy apps/api/dataplat_api packages/core/src worker/src` 及对应 exit code 检查；或在当前 `|| true` 的宽松形式下单独增加 AC-9b。

#### SHOULD-2：pytest 用例 4（`test_pagination_preserves_desc_order`）未测试 `offset` 行为

**文件**：`apps/api/tests/test_jobs_list.py`，第 184-204 行

**问题**：spec AC-8 (d) 要求 "limit/offset 分页正确"。但 `test_pagination_preserves_desc_order` 使用 `limit=200` 拉取全量后验证 desc 顺序，**未测试 `offset` 切页效果**（如 `offset=2` 跳过前 2 条）。函数名和文档字符串都暗示这是"分页"测试，实际只覆盖了顺序。

**建议**：增加一个额外断言：`r = client.get("/jobs", params={"limit": 2, "offset": 2, ...})`，验证返回的第 1 条 id 等于 `ids_desc[2]`。

---

### NICE TO HAVE

#### NTH-1：`_make_user` / `_seed_jobs` / `_delete_jobs` 每次创建新 engine 未 dispose

**文件**：`apps/api/tests/test_jobs_list.py`，第 34 行、第 65 行、第 90 行

在 asyncio_mode=auto + NullPool 配置下影响不大（每次操作完连接立即释放），但 engine 对象本身未调用 `await engine.dispose()`。其他测试文件（`test_jobs.py`）也采用同样模式，属项目级一致风格，不影响正确性。

#### NTH-2：`summarizePayload` 对 `payload==null` 的防御

**文件**：`apps/web/src/routes/jobs/index.tsx`，第 270 行

函数签名为 `payload: Record<string, unknown>` 但第 271 行有 `if (!payload) return ""`，暗示曾考虑过 null/undefined。类型层已排除 null（`JobRead.payload` 在 queries.ts 中定义为 `Record<string, unknown>`），此防御代码多余但无害。

---

## Verdict

**REVISION REQUIRED**

MUST-1（React Rules of Hooks 违反）是必须修复的运行时 bug，会在浏览器真实场景中触发 React 异常。其他问题（SHOULD-1 mypy 缺失、SHOULD-2 pagination offset 覆盖不足）不阻塞功能正确性，但影响门禁完整性和测试覆盖信度。

---

## 后续指引

1. **修复 MUST-1**：将 `useJobs(filters)` 提至 early return 之前（所有 hooks 无条件调用）；考虑加 `enabled: me?.role === "admin"` 避免非 admin 发出无谓 API 请求。
2. **处理 SHOULD-1**：self_check AC-9 追加 mypy 调用，使其与 spec 完全一致。
3. **处理 SHOULD-2**：在 `test_pagination_preserves_desc_order` 增加 offset 切页断言。
4. 修复完成后，重新运行 `bash scripts/_self_check.sh web-jobs-list-page` 确认 10/10 PASS；重新运行 vitest（含真实浏览器 dev server 手动验证）和 pytest 确认回归。
5. 输出 `code_review_v2.md` → 进入 stage 6 单测评审或同步 revision。

关联：stage 6 test_review_v1.md 中 MUST-1 覆盖了同一 hooks 问题对测试有效性的影响（vitest 因 mock 同步返回而无法捕获此 bug）。
