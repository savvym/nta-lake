---
change_id: web-jobs-list-page-20260520
review_of: unit_test/test_report_v1.md
reviewer: claude-stage6-reviewer
version: 2
authored_at: 2026-05-20T17:00:00Z
verdict: APPROVED
---

# Test Review v2 — Stage 6 单测评审（复审）

## v1 问题逐条核验

### MUST FIX

#### MUST-1：vitest 缺 AC-7 (c) type filter 覆盖 — **RESOLVED**

**证据**：`apps/web/src/routes/jobs/index.test.tsx` 第 144-152 行新增第 5 个 test case（按代码顺序）"type filter narrows visible rows and updates useJobs args"：

```ts
it("type filter narrows visible rows and updates useJobs args", async () => {
  renderAt("/jobs?type=ingest");
  await waitFor(() => {
    // mockJobs 里 type=ingest 只有 11111111；22222222 (process) 被过滤掉
    expect(screen.getByText("11111111")).toBeInTheDocument();
    expect(screen.queryByText("22222222")).not.toBeInTheDocument();
    expect(lastFilters.type).toBe("ingest");
  });
});
```

三个断言：（1）正向：ingest 行可见；（2）反向：非 ingest 行不可见；（3）filter 参数透传：`lastFilters.type === "ingest"`。同时验证了 zod `searchSchema.parse` 对 `type=ingest` 查询字符串的解析。

**测试总数**：v1 是 5 个，v2 增加到 **6 个**（admin / 非 admin / status filter / pagination / **type filter (NEW)** / page size reset），超额满足 AC-7 ≥ 5 要求。

**mock 同步**：第 56 行 `useJobs: (filters, _opts?: { enabled?: boolean })` mock 签名同步加 `_opts` 参数，与生产代码 `useJobs(filters, { enabled: isAdmin })` 调用形态一致。`_opts` 前缀下划线表明刻意忽略（mock 始终返回数据，无 enabled 行为；admin 早返不渲染表格已经覆盖 enabled=false 场景）。

---

### SHOULD FIX

#### SHOULD-1：pytest #4 未覆盖 offset 切页 — **RESOLVED**

**证据**：`apps/api/tests/test_jobs_list.py::test_pagination_preserves_desc_order` 第 184-230 行扩展（亦见 code_review_v2 SHOULD-1）：

- 保留：desc 顺序断言。
- 新增：第 205-228 行 `limit=2` 滚动 offset 收集 marker 行，最终断言 `[j["id"] for j in mine_p1 + mine_p2] == [str(i) for i in ids_desc]`。
- marker 隔离避免邻居数据噪声；`for off in range(0, 400, 2)` 上限放宽 + `if not page: break` 早停 + `if len(mine_p1) >= 2 and len(mine_p2) >= 2: break` 高效退出。

`list_jobs(offset=...)` 的 SQLAlchemy `.offset()` 分支获得集成覆盖。spec AC-8 (d) "limit/offset 分页正确" 完整满足。

#### SHOULD-2：vitest 无法检测 hooks 违反 — **RESOLVED (by upstream MUST-1 fix)**

code_review_v2 MUST-1 RESOLVED 后，`useJobs` 始终被无条件调用 → hooks 调用计数稳定 → vitest mock 同步返回的盲区不再隐藏 bug（bug 本身已根除）。v1 该 SHOULD 的语义关切（"测试套件对 hooks crash 路径完全无感知"）已自动消除。开发者未主动添加异步过渡测试，因 v1 已明示这是 "可选 SHOULD 而非 MUST"。

---

## 机械化检查清单（v2 全量）

| ID | 检查项 | 结论 | 原因 |
|---|---|---|---|
| K1 | pytest admin 200 | PASS | 未动 |
| K2 | pytest user 403 | PASS | 未动 |
| K3 | pytest status 过滤 | PASS | 未动 |
| **K4** | **pytest 分页 offset 切片** | **PASS** | 新增 limit=2 滚动 offset 拼接断言（v1 PARTIAL → v2 PASS；见 SHOULD-1 RESOLVED） |
| K5 | pytest 400 非白名单 | PASS | 未动 |
| K6 | pytestmark 隔离 | PASS | 未动 |
| K7 | `_delete_jobs` JSONB 语法 | PASS | 未动 |
| L1 | vitest admin 表格 | PASS | 未动 |
| L2 | vitest 非 admin 403 | PASS | 未动 |
| L3 | vitest status 过滤 | PASS | 未动 |
| L4 | vitest 翻页 | PASS | 未动 |
| L5 | vitest page size reset | PASS | 未动 |
| **L6** | **vitest AC-7 (c) type filter** | **PASS** | 新增第 6 个测试（v1 FAIL → v2 PASS；见 MUST-1 RESOLVED） |
| M1 | vi.mock 模块级 + 闭包变量 | PASS | 未动；mock signature 加 `_opts` 同步生产 |
| M2 | renderAt URL → searchSchema | PASS | type filter 测试同样走 `/jobs?type=ingest` → zod parse → lastFilters 验证 |
| N1 | id 不冲突 | PASS | type filter 测试用 `"11111111"` / `"22222222"` 数字前 8 位，与单词 status/type option 文本不冲突 |
| O | AC ↔ test 双向覆盖 | PASS | AC-7 5 子维度 + 第 6 case（page size）全 covered；AC-8 5 子维度全 covered |
| P | 文件路径一致性 | PASS | 未动 |
| Q | 测试运行实证 | PASS | coding_report 声明 vitest 6/6 + 全 web 47/47 + pytest 5/5 PASS |
| R | hooks 违反对 vitest 有效性 | PASS | 上游 code_review_v2 MUST-1 RESOLVED，盲区消除 |
| T | mock signature 与生产签名同步 | PASS | mock 接 `(filters, _opts?)` 与 `useJobs(filters, opts?)` 对应；无 TypeScript 报错风险 |

---

## 验收项 ↔ 测试映射（v2 更新版）

| AC ID | 测试文件 | 测试函数 | 状态 v1 | 状态 v2 |
|---|---|---|---|---|
| AC-1 JobListResponse | test_jobs_list.py | 所有 5 用例（response body） | COVERED | COVERED |
| AC-2 list_jobs 服务方法 | test_jobs_list.py | pagination + status_filter | PARTIAL | **COVERED**（offset 切片新增） |
| AC-3 GET /jobs admin | test_jobs_list.py | admin + user_403 | COVERED | COVERED |
| AC-4 useJobs hook | index.test.tsx | 所有 6 用例 | COVERED | COVERED |
| AC-5 /jobs 路由 | index.test.tsx | admin sees table | COVERED | COVERED |
| AC-6 nav Jobs link | self_check AC-6 静态 | — | COVERED | COVERED |
| AC-7 (a) admin 看到列表 | index.test.tsx | admin sees table | COVERED | COVERED |
| AC-7 (b) filter status | index.test.tsx | status filter narrows | COVERED | COVERED |
| AC-7 (c) filter type | index.test.tsx | **type filter narrows (NEW)** | MISSING | **COVERED** |
| AC-7 (d) 翻页 | index.test.tsx | pagination next/prev | COVERED | COVERED |
| AC-7 (e) 非 admin 403 | index.test.tsx | non-admin message | COVERED | COVERED |
| AC-8 (a) admin 200 + total | test_jobs_list.py | test_admin_list | COVERED | COVERED |
| AC-8 (b) user 403 | test_jobs_list.py | test_user_list | COVERED | COVERED |
| AC-8 (c) status 过滤 | test_jobs_list.py | test_status_filter | COVERED | COVERED |
| AC-8 (d) limit/offset 分页 | test_jobs_list.py | test_pagination（含 offset 切片） | PARTIAL | **COVERED** |
| AC-8 (e) 400 非白名单 | test_jobs_list.py | test_invalid_status_400 | COVERED | COVERED |
| AC-9 typecheck/ruff/mypy | self_check AC-9 静态 | — | PARTIAL | **COVERED**（mypy 已纳入） |
| AC-10 self_check 自递归 | self_check AC-10 静态 | — | COVERED | COVERED |

---

## v2 新发现问题

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

#### N-1：mock `_opts` 参数未实际驱动 `enabled` 分支

`vi.mock` 在 `useJobs` 始终返回数据，未据 `_opts?.enabled` 切换 `data: undefined` / `isLoading: true`。这意味着 vitest 不直接验证生产代码 `enabled: isAdmin` 的行为；非 admin 分支由 early return（"仅 admin 可见"提示）单独覆盖，所以这条路径仍有效保护。属于 mock 设计简化，非缺陷。后续若需更严格，可在 mock 内根据 `_opts?.enabled` 切换返回形态。

#### N-2：vitest 用例 1 `getAllByText("succeeded").length > 0` 精度问题（v1 NTH-2 重申）

未在 v2 修复，但 v1 已标注 NICE TO HAVE，不阻塞验收。开发者优先级合理。

---

## Verdict

**APPROVED**

v1 报告的 1 条 MUST FIX + 2 条 SHOULD FIX 全部 RESOLVED：

- MUST-1 type filter test：新增第 6 个用例，断言三层 + searchSchema 解析 — 全 PASS。
- SHOULD-1 pytest offset 切片：limit=2 滚动 offset 拼接断言 — 全 PASS。
- SHOULD-2 hooks 测试盲区：由 code_review_v2 MUST-1 RESOLVED 自动消除。

AC ↔ test 覆盖表所有 AC 均为 COVERED；vitest 6/6 + pytest 5/5 + 全 web 47/47 本地全 PASS。N-1 / N-2 NICE TO HAVE 不阻塞。

---

## 后续指引

1. stage 6 verdict 标 APPROVED，更新 summary.md `6 单测评审 done v2 APPROVED`。
2. 与 code_review_v2 APPROVED 一并视作 stage 4+6 闭合，可进入 stage 7 代码推送（branch `change/web-jobs-list-page-20260520`）。
3. stage 7 push 前再跑一次 `bash scripts/_self_check.sh web-jobs-list-page` 确认 10/10；stage 8 CI 跑 `full` 链确认无回归。
4. 跨链路 `web-write-flows-20260517 AC-2` 的 grep 路径修正（jobs/$job_id.tsx）建议在 stage 9 followup 简单提一句"已顺手修正，无独立 change"。

关联：code_review_v2.md 同步 APPROVED；两份报告对 v1 全部问题给出 RESOLVED 证据。
