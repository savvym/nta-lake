---
change_id: web-snapshot-export-ui-20260520
phase: implementation
status: done
authored_at: 2026-05-21T10:55:00Z
author: sonnet-phase2-implementer
model_used: claude-sonnet-4-6
branch: change/web-snapshot-export-ui-20260520
base_commit: 0e4bf66
head_commit: f4d4cdac47e3d1e75e44848c12adc5e44cc70366
pr_url: n/a
---

# Implementation

## 改动文件清单

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `apps/api/dataplat_api/schemas/snapshot_export.py` | new | SnapshotExportFormat + SnapshotExportTriggerBody schema |
| `apps/api/dataplat_api/routers/snapshots.py` | edit | 提取 _resolve_silver_jsonl_blob_sha helper + 新增 POST exports endpoint |
| `apps/api/tests/test_snapshot_export.py` | new | 3 env-gated 集成测试（happy / jsonl-422 / 404） |
| `apps/web/src/lib/api/queries.ts` | edit | 新增 useSnapshotExport useMutation hook |
| `apps/web/src/routes/repos/$owner.$name/snapshots/$hash/export.tsx` | new | 导出 UI 路由（folder form 多级嵌套） |
| `apps/web/src/routes/repos/$owner.$name/snapshots/$hash/export.test.tsx` | new | 2 vitest tests（AC-4） |
| `apps/web/src/routeTree.gen.ts` | edit | 注册新路由 ReposOwnerNameSnapshotsHashExportRoute |
| `apps/web/src/routes/repos/$owner.$name.tsx` | edit | .jsonl entry 旁加 "导出" 链接 |

## 验证结果

### AC 自检

| AC | 结果 | 证据 |
|---|---|---|
| AC-1 (static grep) | PASS | `grep -q '@router.post.*"/{owner}/{name}/snapshots/{hash}/exports"' snapshots.py && echo AC-1 OK` |
| AC-2 (env-gated happy) | SKIP | env not set；测试文件语法正确；3 skipped in 3.23s |
| AC-3 (env-gated 422/404) | SKIP | env not set；测试文件语法正确 |
| AC-4 (vitest UI) | PASS | 2 tests pass |

### pytest apps/api

```
48 passed, 125 skipped in 1.85s
```

### vitest apps/web

```
Test Files  21 passed (21)
      Tests  60 passed (60)
```

### typecheck apps/web

```
pnpm tsc --noEmit → 0 errors
```

## 偏离 design.md

| # | 偏离点 | 原因 |
|---|---|---|
| DEV-1 | 父路由导出 Link 使用原生 `<a href>` 拼 URL 而非 TanStack Router `<Link search=...>` | TanStack Router typed-search 要求同时携带父路由 search 字段（tab/path）；直接使用 href 功能等效 |
| DEV-2 | `_resolve_silver_jsonl_blob_sha` helper 从 W4-1 rows endpoint inline 提取为模块级 | 与 design §决策 6 预期一致；行为不变；W4-1 现有测试全通过 |

## 跨 change / 上游回归

- 全 web vitest：60/60 PASS（21 files）
- apps/api：48 passed + 125 skipped（全量无回归）
- typecheck：0 errors

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验。
