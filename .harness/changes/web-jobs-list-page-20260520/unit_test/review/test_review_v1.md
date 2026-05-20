---
change_id: web-jobs-list-page-20260520
review_of: unit_test/test_report_v1.md
reviewer: claude-stage6-reviewer
version: 1
authored_at: 2026-05-20T15:30:00Z
verdict: REVISION REQUIRED
---

# Test Review v1 — Stage 6 单测评审

## 机械化检查清单

| ID | 检查项 | 结论 | 原因 |
|---|---|---|---|
| K1 | pytest 5 用例：admin 200 | PASS | `test_admin_list_returns_items_and_total`：200 + items ≥ 4 + total ≥ 4 + desc 顺序 |
| K2 | pytest 5 用例：user 403 | PASS | `test_user_list_returns_403`：normal_user → 403 |
| K3 | pytest 5 用例：status 过滤 | PASS | `test_status_filter_narrows_results`：?status=queued → marker 行只剩 1 条 |
| K4 | pytest 5 用例：分页 desc | PARTIAL | `test_pagination_preserves_desc_order`：仅验证 desc 顺序（limit=200 全量），**未验证 offset 切页**；spec AC-8 (d) 明确要求 "limit/offset 分页正确"（见 SHOULD FIX S-1） |
| K5 | pytest 5 用例：400 非白名单 | PASS | `test_invalid_status_returns_400`：?status=bogus → 400 + "非白名单" |
| K6 | pytestmark 隔离实际生效 | PASS | `pytestmark = pytest.mark.skipif(not _db_url(), ...)` 模块级 skipif；无 DB 时全部跳过而非失败 |
| K7 | `_delete_jobs` JSONB key 抽取语法正确 | PASS | `payload->>'_marker' = :m` 是 PostgreSQL JSONB 文本提取操作符；SQLAlchemy `text()` + bind param `:m` 无 `::jsonb` 冲突；语法正确 |
| L1 | vitest 5 用例：admin 表格 | PASS | "admin sees jobs table with status badges"：id 前 8 位 + status badge 均断言 |
| L2 | vitest 5 用例：非 admin 403 提示 | PASS | "non-admin sees 403-equivalent message"：`/仅 admin 可见/` |
| L3 | vitest 5 用例：status 过滤 | PASS | "status filter narrows visible rows"：renderAt `/jobs?status=running`，验证 lastFilters.status + row 可见性 |
| L4 | vitest 5 用例：翻页 | PASS | "pagination next/prev affects useJobs offset"：fireEvent.click 下一页/上一页，验证 lastFilters.offset |
| L5 | vitest 5 用例：page size reset | PASS | "changing page size resets offset to 0"：fireEvent.change，验证 limit + offset=0 |
| **L6** | **AC-7 (c) type filter 覆盖** | **FAIL** | spec AC-7 (c) 要求 "filter type 触发 query"；5 个 vitest 用例中无任何一个测试 type filter select 的变化；`lastFilters.type` 从未被 vitest 断言（见 MUST FIX M-1） |
| M1 | vi.mock 模块级 + 闭包变量 | PASS | `vi.mock("../../lib/api/queries", ...)` 顶层调用；`currentMe` / `lastFilters` 闭包变量；`beforeEach` 重置 |
| M2 | `renderAt` URL 参数验证 searchSchema | PASS | `renderAt("/jobs?status=running")` → TanStack router + `validateSearch` → zod `searchSchema.parse` → `lastFilters.status === "running"` 验证 |
| N1 | id 不冲突：status badge 文本与 filter option 同名问题 | PASS | 用例 1 用 `getAllByText("succeeded").length > 0` 而非 `getByText`；mock job id 前 8 位为数字（`"11111111"` / `"22222222"`），与 status/type 单词不冲突 |
| O | AC ↔ test 双向覆盖表（test_report §"验收项 ↔ 测试映射"） | PARTIAL | AC-7 (c) type filter 无 test 对应（见 M-1）；AC-8 (d) 分页 offset 覆盖不足（见 S-1）；其余 AC 有对应 |
| P | 文件路径一致性 | PASS | `test_jobs_list.py` 在 `apps/api/tests/`；`index.test.tsx` 在 `apps/web/src/routes/jobs/`；`$job_id.test.tsx` mock 路径已修正为 `../../lib/api/queries` |
| Q | 测试运行实证 | PASS（信任报告）| coding_report 声明 5/5 + 5/5 + 46/46 PASS；无法访问 docker/DB 真跑 pytest，vitest 不依赖基础设施 |
| R | React hooks 违反对 vitest 有效性的影响 | FAIL | 由于 vi.mock 同步返回 `currentMe`（无异步过渡），vitest 在非 admin 测试中始终走 early return 不调用 useJobs，在 admin 测试中始终走 useJobs，**两者在同一渲染内无切换**，故 hooks 调用数不变，vitest 测试通过。但这意味着 vitest 无法检测到 code_review_v1 MUST-1 描述的运行时 hooks 违反 bug（见 SHOULD FIX S-2）|

---

## 问题列表

### MUST FIX

#### MUST-1：vitest 无 AC-7 (c) type filter 覆盖 — spec 要求的 5 个子维度未全满足

**文件**：`apps/web/src/routes/jobs/index.test.tsx`

**问题**：

spec AC-7 明确列出 5 个必须覆盖的子维度：

> (a) admin 看到列表 (b) filter status 触发 query (c) filter type 触发 query (d) 翻页 (e) 非 admin 隐藏导航 / 403 提示

实现的 5 个 vitest 用例覆盖了 (a)(b)(d)(e) 和 "page size reset"，**缺少 (c) filter type 触发 query**。"page size reset" 是合理的附加测试，但不能替代 AC-7 (c) type 过滤覆盖。

验证命令：

```bash
grep -n "type\|lastFilters.type" apps/web/src/routes/jobs/index.test.tsx
# 输出中无 lastFilters.type 断言；无 renderAt("/jobs?type=...")
```

**修复方向**（仅指出方向，不改代码）：增加一个测试 `it("type filter narrows visible rows and updates useJobs args", ...)`，使用 `renderAt("/jobs?type=ingest")`，断言 `lastFilters.type === "ingest"` 且仅 ingest 行可见。可以将现有的 "page size reset" 测试保留为第 6 个测试（使总数 ≥ 6），以超额满足 AC-7 ≥ 5 要求。

---

### SHOULD FIX

#### SHOULD-1：`test_pagination_preserves_desc_order` 未覆盖 offset 切页语义

**文件**：`apps/api/tests/test_jobs_list.py`，第 184-204 行

**问题**：测试名和函数注释（"limit+offset 分页"）暗示此测试覆盖 spec AC-8 (d) "limit/offset 分页正确"，但实现仅以 `limit=200` 拉取全量，验证 `mine_all[1].id == ids_desc[1]`，验证的是 **desc 排序**，不是 **offset 窗口切片**行为。

真正的 offset 测试应：

```python
# 示例断言（不改代码，仅说明）
r1 = client.get("/jobs", params={"limit": 2, "offset": 0})
r2 = client.get("/jobs", params={"limit": 2, "offset": 2})
# r1.items[0].id == ids_desc[0], r2.items[0].id == ids_desc[2]
```

此缺失使 `list_jobs(offset=...)` 的 SQLAlchemy `.offset()` 分支在集成测试层无覆盖。

#### SHOULD-2：vitest 无法检测 MUST-1 React hooks 违反 — 测试设计盲区

**文件**：`apps/web/src/routes/jobs/index.test.tsx`

**问题**：`vi.mock` 同步返回 `currentMe`，所有 test case 在单次同步 render 中确定状态（无 `undefined → admin` 异步过渡），因此 React hooks 调用计数在单次 render 内不变，hooks 违反错误不触发。这是合理的 mock 策略，但导致测试套件对 code_review_v1 MUST-1 所描述的运行时 crash 路径完全无感知。

**建议**：在修复 MUST-1 (hooks 提前调用) 后，增加一个异步过渡场景测试，验证 `me` 从 `undefined` 过渡到 `admin` 时组件不崩溃（可用 `waitFor` + 延迟 mock resolve 模拟）。此测试可作为 SHOULD 而非 MUST，因为 MUST-1 修复本身消除了 bug。

---

### NICE TO HAVE

#### NTH-1：`_make_user` 在 fixture 外部调用（非 async generator 惯例）

**文件**：`apps/api/tests/test_jobs_list.py`，第 103-109 行

`admin_user` fixture 在 `async def` + `AsyncGenerator` 中调用 `await _make_user(...)` 然后 yield，是有效 pattern。但 `_make_user` 内部每次创建新 engine 不 dispose，在 NullPool 下影响极小（连接立即释放），属于与项目既有测试一致的风格。建议后续统一为接受共享 session 的 helper，不影响本 change 正确性。

#### NTH-2：vitest 用例 1 中 `getAllByText` 断言不检查行内 badge 与 option 分离

**文件**：`apps/web/src/routes/jobs/index.test.tsx`，第 105-106 行

```ts
expect(screen.getAllByText("succeeded").length).toBeGreaterThan(0);
```

此断言同时匹配 filter `<option>succeeded</option>` 与行内 `<StatusBadge status="succeeded">`，不能单独证明 badge 渲染正确。可加 `data-testid` 或用 `within(row).getByText("succeeded")` 精确定位。属精度问题，不影响 pass/fail 判断。

---

## 验收项 ↔ 测试映射（修订版）

| AC ID | 测试文件 | 测试函数 | 状态 |
|---|---|---|---|
| AC-1 JobListResponse | test_jobs_list.py | 所有 5 用例（response body 含 items/total/limit/offset） | COVERED |
| AC-2 list_jobs 服务方法 | test_jobs_list.py | test_pagination_preserves_desc_order + test_status_filter | PARTIAL（desc 顺序覆盖；offset 无覆盖） |
| AC-3 GET /jobs admin | test_jobs_list.py | test_admin_list + test_user_list_returns_403 | COVERED |
| AC-4 useJobs hook | index.test.tsx | 所有 5 用例（lastFilters 捕获） | COVERED |
| AC-5 /jobs 路由 | index.test.tsx | "admin sees jobs table" | COVERED |
| AC-6 nav Jobs link | self_check AC-6（静态） | — | COVERED（静态） |
| AC-7 (a) admin 看到列表 | index.test.tsx | "admin sees jobs table" | COVERED |
| AC-7 (b) filter status | index.test.tsx | "status filter narrows" | COVERED |
| AC-7 (c) filter type | index.test.tsx | **无对应测试** | MISSING |
| AC-7 (d) 翻页 | index.test.tsx | "pagination next/prev" | COVERED |
| AC-7 (e) 非 admin 403 | index.test.tsx | "non-admin sees message" | COVERED |
| AC-8 (a) admin 200 + total | test_jobs_list.py | test_admin_list | COVERED |
| AC-8 (b) user 403 | test_jobs_list.py | test_user_list | COVERED |
| AC-8 (c) status 过滤 | test_jobs_list.py | test_status_filter | COVERED |
| AC-8 (d) limit/offset 分页 | test_jobs_list.py | test_pagination（仅 desc 顺序） | PARTIAL |
| AC-8 (e) 400 非白名单 | test_jobs_list.py | test_invalid_status_400 | COVERED |
| AC-9 typecheck/ruff/mypy | self_check AC-9（静态） | — | PARTIAL（mypy 未纳入 self_check） |
| AC-10 self_check 自递归 | self_check AC-10（静态） | — | COVERED |

---

## Verdict

**REVISION REQUIRED**

MUST-1（vitest 缺少 AC-7 (c) type filter 测试）是明确的规格遗漏：spec 显式要求 5 维度之 (c) 但无对应 test case。SHOULD-1（offset 切页无覆盖）和 SHOULD-2（hooks bug 的测试盲区）降低了测试套件的信度但不直接阻塞功能门禁。

---

## 后续指引

1. **修复 MUST-1**：在 `index.test.tsx` 增加 type filter 测试（`renderAt("/jobs?type=ingest")`）；同时建议将总测试数提至 ≥ 6 以在 MUST-1 修复后超额满足 AC-7 ≥ 5。
2. **关联 code_review_v1 MUST-1 修复**：修复 hooks violation 后，SHOULD-2 的测试盲区自然消除（或主动补充异步过渡 test case）。
3. **处理 SHOULD-1**：在 `test_pagination_preserves_desc_order` 追加 offset 切页断言（`limit=2, offset=2`）。
4. 修复后重新运行 `pnpm exec vitest run src/routes/jobs/index.test.tsx` 确认 ≥ 6/6 PASS；`uv run pytest tests/test_jobs_list.py` 确认 ≥ 5/5 PASS。
5. 输出 `test_review_v2.md` 后，若 code_review 也已 APPROVED，可进入 stage 7 代码推送。
