---
change_id: web-row-preview-20260520
phase: implementation
status: done
authored_at: 2026-05-20T22:41:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/web-row-preview-20260520
base_commit: 0cad6a2
head_commit: 70702fc76bad4372392b6df8ae7ca0e5a78bd93d
pr_url: n/a
---

# Implementation：通用 silver/gold row 预览 + 虚拟化 (W4-2)

## 摘要

新增 `/snapshots/$owner/$name/$hash/rows` folder-form 子路由，引入 `@tanstack/react-virtual@^3` 行虚拟化（固定 600px 高度容器 + estimateSize=48），复用 W4-1 `useSnapshotRows` hook 与 endpoint，支持行级展开看完整 JSON + URL search param 驱动分页。父路由 `$owner.$name.$hash.tsx` 加了 `<Outlet />` 并在 `.jsonl` / `.jsonl.gz` 文件行旁加了 "Preview rows" Link。

## 改动文件清单

| 路径 | 类型 | 一句话说明 | 增删行 |
|---|---|---|---|
| `apps/web/package.json` | edit | 加 @tanstack/react-virtual@^3 | +1 |
| `pnpm-lock.yaml` | edit | lock 更新 | +17 |
| `apps/web/src/routeTree.gen.ts` | edit | 注册新子路由 + 更新 interfaces | +44/-3 |
| `apps/web/src/routes/snapshots/$owner.$name.$hash.tsx` | edit | 加 Outlet + Preview rows Link | +16/-1 |
| `apps/web/src/routes/snapshots/$owner.$name.$hash/rows.tsx` | new | folder-form 子路由主文件 | +219 |
| `apps/web/src/routes/snapshots/$owner.$name.$hash/rows.test.tsx` | new | 3 个 vitest 用例 | +232 |

## 测试通过证据

### AC 静态验证

```text
AC-1 OK   # test -f rows.tsx && grep createFileRoute
AC-2 OK   # grep '<Outlet' $owner.$name.$hash.tsx
```

### vitest 单元测试

```text
$ cd apps/web && pnpm vitest run src/routes/snapshots/\$owner.\$name.\$hash/rows.test.tsx
 ✓ src/routes/snapshots/$owner.$name.$hash/rows.test.tsx (3 tests) 201ms
 Tests  3 passed (3)
```

### 全套 vitest

```text
$ cd apps/web && pnpm vitest run
 Test Files  18 passed (18)
       Tests  52 passed (52)
```

### TypeScript 类型检查

```text
$ cd apps/web && pnpm tsc --noEmit
（无输出 = clean）
```

## 偏离 design.md（DEV-N）

| # | 偏离点 | 原因 |
|---|---|---|
| DEV-1 | rows.test.tsx 中 vi.mock useSnapshot 返回有效 snapshot 数据（非 null） | 父路由 early-return 会阻断 Outlet 渲染，测试必须让父路由渲染完整 |
| DEV-2 | routeTree.gen.ts 手动更新（非 vite plugin 自动生成） | 本地无 dev server 环境；手动注册与 plugin 生成格式完全一致 |

## 跨 change / 上游回归

- 全 web vitest：52/52 PASS（18 files）— W4-1 测试全部仍 PASS
- typecheck: clean（零错误）

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 AC-1..AC-4。
