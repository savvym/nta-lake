---
change_id: web-jobs-list-page-20260520
review_of: coding/coding_report_v1.md
reviewer: claude-stage4-reviewer
version: 2
authored_at: 2026-05-20T17:00:00Z
verdict: APPROVED
---

# Code Review v2 — Stage 4 编码评审（复审）

## v1 问题逐条核验

### MUST FIX

#### MUST-1：React Rules of Hooks 违反 — **RESOLVED**

**证据**：`apps/web/src/routes/jobs/index.tsx` 第 31-77 行已重构。

- 第 35-48 行：`useMe` / `Route.useSearch` / `Route.useNavigate` / `useQueryClient` / `useJobs` 5 个 hook **全部在 early return 之前**调用。
- 第 39 行：`const isAdmin = me?.role === "admin"` 派生变量（不调用 hook）。
- 第 40-48 行：`useJobs(filters, { enabled: isAdmin })` 通过 `enabled` 控制非 admin 不发请求，避免 403 噪声。
- 第 54 行与第 66 行：early return 全部在所有 hooks 调用**之后**。
- `apps/web/src/lib/api/queries.ts` 第 239-268 行：`useJobs` 签名扩展为 `(filters, opts?: { enabled?: boolean })`；`enabled: opts?.enabled ?? true` 默认向后兼容。

Hooks 调用次数在每次 render 恒定 = 5；无论 `me` 是否解析、是否 admin，调用序列不变。React Rules of Hooks 违反已根除。

第 32-34 行新增中文注释回顾该 bug 与修复理由，是良好的防回归留痕。

---

### SHOULD FIX

#### SHOULD-1：self_check AC-9 缺失 mypy — **RESOLVED**

**证据**：`scripts/_self_check.sh` 第 1656-1657 行 AC-9 已追加 mypy：

```bash
... && (uv run mypy apps/api/dataplat_api packages/core/src 2>&1 | tee /tmp/dataplat-jobs-mypy.log >/dev/null) \
    && grep -q "Success: no issues found" /tmp/dataplat-jobs-mypy.log
```

包级 target（`dataplat_api` + `packages/core/src`）与项目既有 AC-12/AC-16 风格一致，规避文件级触发 `dataplat_core import-untyped` 噪声的已知问题。coding_report 声明 `Success: no issues found in 93 source files`。AC-9 描述也已同步更新（"拆 alternation：3 个独立断言；mypy 走包级…"）。

与 spec 的对齐：spec AC-9 写 `mypy apps/api/dataplat_api packages/core/src worker/src`，self_check 实现只到 `packages/core/src`（少 `worker/src`）。考虑到 worker/src 在其他 AC-block 中已有独立 mypy 覆盖、且本 change 不动 worker 文件，此偏差不阻塞验收，归入 NICE TO HAVE N-1 备注。

#### SHOULD-2：pytest #4 未测 offset 切页 — **RESOLVED**

**证据**：`apps/api/tests/test_jobs_list.py::test_pagination_preserves_desc_order` 第 184-230 行已扩展：

- 第 194-203 行：保留 v1 的 desc 顺序断言（limit=200 + `mine_all[1].id == str(ids_desc[1])`）。
- 第 205-228 行：新增 offset 切片循环 — 用 `limit=2` 滚动 offset，通过 marker 过滤逐页收集 marker 行；最终断言 `mine_p1 + mine_p2` 的 4 个 id **完全等于** seed desc 顺序 `ids_desc`。
- 第 208 行 `for off in range(0, 400, 2)` 上限放宽容忍邻居数据噪声；第 214-215 行 `if not page: break` 早停；第 222 行 `if len(mine_p1) >= 2 and len(mine_p2) >= 2: break` 高效退出。

此扩展同时验证：（a）`offset` 真做窗口切片（拼接结果等于全量 desc 顺序）；（b）切片中 marker 行没有跳行 / 重复。SQLAlchemy `.offset()` 分支获得集成覆盖。

---

## 机械化检查清单（v2 全量）

| ID | 检查项 | 结论 | 原因 |
|---|---|---|---|
| A | folder routing 形态合理性 | PASS | 未动；与 v1 一致 |
| A2 | 迁移完整性 | PASS | 未动；`routes/` 顶层仍无 stale 文件 |
| B | 路由顺序 `@router.get("")` 在 `/{job_id}` 之前 | PASS | 未动；routers/jobs.py 第 65/100 行 |
| C | 白名单常量位置与 400 detail | PASS | 未动 |
| D | `service.list_jobs` 实现 | PASS | 未动 |
| E | admin 限制 | PASS | 未动 |
| F | `useJobs` queryKey 稳定性 | PASS | queryKey 字段未变；新增 `opts?` 参数不进 queryKey（合理：enabled 不应影响 cache key） |
| G1 | jobs/index.tsx UI 完整性 | PASS | 未动核心 UI；hook 调用顺序调整不影响渲染输出 |
| **G2** | **React Rules of Hooks 合规性** | **PASS** | 全部 hooks 拉到 early return 之前；`useJobs` 用 `enabled: isAdmin` 控制非 admin 不发请求（见 MUST-1 RESOLVED） |
| H | __root.tsx admin-only link | PASS | 未动 |
| I | spec AC-5 修订充分性 | PASS | 未动 |
| J | 跨 change web-write-flows AC-2 修正 | PASS | 未动 |
| P | git diff 路径一致性 | PASS | v2 改动集中于 index.tsx / queries.ts / _self_check.sh / test_jobs_list.py / index.test.tsx，与 coding_report 一致 |
| Q | typecheck / ruff / mypy | PASS | coding_report 与 self_check AC-9 现都跑 mypy，本地 `Success: no issues found` |
| R | AC kind lint | PASS | 未动 |
| S | self_check AC block | PASS | AC-9 mypy 补足；AC block 总数仍 10 条 |
| T | `useJobs` 向后兼容 | PASS | `opts?: { enabled?: boolean }` optional，`enabled: opts?.enabled ?? true`；既有调用方 `useEnqueueIngest` / `useJob` 不受影响 |

---

## v2 新发现问题

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

#### N-1：self_check AC-9 mypy target 缺 `worker/src`

**文件**：`scripts/_self_check.sh` 第 1657 行

spec AC-9 完整命令包含 `mypy apps/api/dataplat_api packages/core/src worker/src` 三个 target，self_check 实现只到前两个。`worker/src` 在 `bootstrap-monorepo` / `processor-framework` 等 AC block 中已有独立覆盖，本 change 不动 worker 文件，不阻塞验收，但 spec ↔ self_check 文本字面对齐度可在下一次 harness 微调时补全。

#### N-2：`useJobs` 在非 admin renders 内仍被 React Query 注册但不发请求

`useJobs(..., { enabled: false })` 时 React Query 仍会注册 query observer（保持 cache key 占位），未实际发请求。第一次 render（me=undefined）`isAdmin=false`，第二次 render（me=admin）`isAdmin=true` → enabled 切换 → React Query 自动 fetch。行为符合 TanStack Query 文档；无副作用。属设计说明，非问题。

---

## Verdict

**APPROVED**

v1 报告的 1 条 MUST FIX + 2 条 SHOULD FIX 全部 RESOLVED，证据充分；v2 复审无新发现 MUST/SHOULD 级问题。N-1 仅文本层对齐建议，不阻塞 stage 4 通过。

---

## 后续指引

1. stage 4 verdict 标 APPROVED，更新 summary.md `4 编码评审 done v2 APPROVED`。
2. 如 stage 6 test_review_v2 也 APPROVED，可进入 stage 7 代码推送。
3. N-1（self_check AC-9 mypy target 补 `worker/src`）建议挂在下一次 harness 维护型 change，不为此重做 v3。
4. coding_report_v1 中"列表无 live poll"已在非范围列出，follow-up `web-jobs-list-live-poll-*` 留待后续 change。

关联：stage 6 test_review_v2.md 中验证了 vitest 第 6 个用例 + mock signature 同步对应；两份报告一致 APPROVED。
