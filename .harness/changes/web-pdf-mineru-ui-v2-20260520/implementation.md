---
change_id: web-pdf-mineru-ui-v2-20260520
phase: implementation
status: done
authored_at: 2026-05-20T22:15:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: main
base_commit: 0e4bf66
head_commit: <待 commit 后回填>
pr_url: n/a (直接 main)
---

# Implementation

## 改动文件清单

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `apps/api/dataplat_api/schemas/snapshot_rows.py` | new | SilverRowRead + SnapshotRowsResponse Pydantic schema | T-1 |
| `apps/api/dataplat_api/routers/snapshots.py` | edit | 新增 GET `/{owner}/{name}/snapshots/{hash}/rows` 端点 | T-1 |
| `apps/api/tests/test_snapshot_rows.py` | new | AC-1/AC-2/AC-3 集成测试（3 tests all pass） | T-1 |
| `apps/web/src/lib/api/queries.ts` | edit | 新增 SilverRowRead/SnapshotRowsResponse 接口 + useSnapshotRows hook | T-2 |
| `apps/web/src/routes/repos/$owner.$name/pdf-mineru.tsx` | new | PDF→Silver Row UI v2 路由组件（folder 形式） | T-2 |
| `apps/web/src/routes/repos/$owner.$name/pdf-mineru.test.tsx` | new | AC-4 前端组件测试（2 tests all pass） | T-2 |
| `apps/web/src/routeTree.gen.ts` | edit | 更新 import 路径指向 folder 形式路由文件 | T-2 |
| `apps/web/src/routes/repos/$owner.$name.tsx` | edit | 添加 `<Outlet />` 以支持 pdf-mineru 子路由渲染 | T-2 |

## 任务完成情况

| Task | 状态 | 备注 |
|---|---|---|
| T-1 后端 schema | done | SilverRowRead/SnapshotRowsResponse 均 `extra="forbid"` |
| T-1 后端端点 | done | GET `/repos/{owner}/{name}/snapshots/{hash}/rows`，offset/limit/blob_sha 查询参数 |
| T-1 后端测试 | done | 3/3 PASS：happy path 分页 / 404 / 422 两种情形 |
| T-2 前端 hook | done | useSnapshotRows + 接口定义在 queries.ts |
| T-2 前端路由 | done | folder 形式 `repos/$owner.$name/pdf-mineru.tsx`，validateSearch + zod schema |
| T-2 前端测试 | done | 2/2 PASS：表格渲染 3 行 / 点详情展开 JSON |

## 测试通过证据

### 后端（AC-1/2/3）

```text
$ cd apps/api && uv run --extra dev pytest tests/test_snapshot_rows.py -x -q -v
tests/test_snapshot_rows.py::test_rows_happy_paginated PASSED
tests/test_snapshot_rows.py::test_rows_snapshot_not_found PASSED
tests/test_snapshot_rows.py::test_rows_jsonl_resolution_errors PASSED
======================== 3 passed, 2 warnings in 3.83s =========================
```

### 前端（AC-4）

```text
$ cd apps/web && pnpm test
 ✓ src/routes/repos/$owner.$name/pdf-mineru.test.tsx (2 tests) 197ms
   ✓ /repos/$owner/$name/pdf-mineru > renders 3 rows table from useSnapshotRows
   ✓ /repos/$owner/$name/pdf-mineru > clicking detail button expands row JSON
 Test Files  17 passed (17)
      Tests  49 passed (49)
```

### 跨 change 回归

- 全 web vitest：17/17 files PASS，49/49 tests PASS（含新增 2 AC-4 tests）
- snapshot_rows + snapshots_api：5/5 PASS
- 全 pytest（含 pre-existing 失败）：128 passed，42 failed（pre-existing，非本 change 引入；见偏离说明）

## 偏离 design.md

| # | 偏离点 | 原因 |
|---|---|---|
| D-1 | 路由文件使用 folder 形式 `routes/repos/$owner.$name/pdf-mineru.tsx` 而非 design.md 示例的 flat-dot 形式 | TanStack Router vite 插件在 flat-dot 形式下将其自动嵌套为 ReposOwnerNameRoute 的子路由，且父组件没有 `<Outlet />`，导致测试不可见。design.md 明确说明了此回退方案："如果 sonnet 跑测试报 route ambiguous → 改用 routes/repos/$owner.$name/pdf-mineru.tsx 文件夹形式"。|
| D-2 | 在 `routes/repos/$owner.$name.tsx` 末尾添加 `<Outlet />` | folder 形式强制 TanStack Router 将 pdf-mineru 嵌套在父路由下；父组件必须渲染 `<Outlet />` 才能显示子组件内容。此改动不影响现有页面功能（Outlet 仅在子路由匹配时有内容）。 |
| D-3 | `store.get(sha)` 使用 `async for chunk in store.get(sha)` 而非 design.md 中的 `data = await store.get(sha)` | MinioBlobStore.get() 实现为 AsyncGenerator，不可直接 await；协议注释"W3-4..W3-7 protocol drift"已知。|

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验。
