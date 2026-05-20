---
change_id: web-operator-chain-builder-20260520
phase: implementation
status: done
authored_at: 2026-05-20T23:05:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/web-operator-chain-builder-20260520
base_commit: 0e4bf66
head_commit: c48031dcba8e92021a90d8ea34f870d05e3777eb
pr_url: n/a
---

# Implementation：Recipe v2 Chain Builder UI (W4-3)

## 摘要

新增 `/recipes/builder` 路由（`apps/web/src/routes/recipes/builder.tsx`），三栏布局：左栏 Palette（loader/operator 选择）、中栏 Chain（recipe 名称 + loader 卡片 + 可拖序 operator 列表）、右栏 YAML Preview（实时 yaml + 复制/下载/校验）。

yaml 序列化由 `buildRecipeYaml` pure 函数（`lib/recipe-v2-builder.ts`）负责，基于 `js-yaml`。拖拽排序用 `@dnd-kit/sortable`（非 react-flow，design 决策 1 记录的显式偏离）。

LOADER_NAMES / OPERATOR_NAMES 经 grep 验证后 hard-code，与 packages/core 实际注册名一致（DEV-1 修订：design 举例名与实际名不符）。

## 改动文件清单

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `apps/web/package.json` | edit | 加 @dnd-kit/core@^6 / @dnd-kit/sortable@^8 / @dnd-kit/utilities@^3 / js-yaml@^4 + @types/js-yaml@^4 devDep |
| `pnpm-lock.yaml` | edit | lock 更新（新增 5 个 packages） |
| `apps/web/src/routeTree.gen.ts` | edit | 注册新路由 RecipesBuilderRoute + 更新所有 interfaces/declare module/rootRouteChildren |
| `apps/web/src/routes/recipes/builder.tsx` | new | /recipes/builder 三栏 UI：Palette + Chain + YAML Preview，dnd-kit sortable |
| `apps/web/src/routes/recipes/builder.test.tsx` | new | 3 个 RTL vitest 用例 (AC-3 + AC-4 + 错误状态内联显示) |
| `apps/web/src/lib/recipe-v2-builder.ts` | new | buildRecipeYaml pure 函数 + LOADER_NAMES / OPERATOR_NAMES 常量（grep 验证实际注册名） |
| `apps/web/src/lib/recipe-v2-builder.test.ts` | new | 3 个 pure 函数 vitest 用例（AC-2 + empty yaml → {} + invalid yaml throw） |

## 测试通过证据

### AC 静态验证

```text
AC-1 OK   # test -f apps/web/src/routes/recipes/builder.tsx && grep createFileRoute("/recipes/builder")
```

### vitest AC-2..AC-4

```text
$ cd apps/web && pnpm vitest run src/lib/recipe-v2-builder.test.ts src/routes/recipes/builder.test.tsx
 ✓ src/lib/recipe-v2-builder.test.ts (3 tests) 9ms
 ✓ src/routes/recipes/builder.test.tsx (3 tests) 208ms
 Test Files  2 passed (2)
      Tests  6 passed (6)
```

### 全套 vitest

```text
$ cd apps/web && pnpm vitest run
 Test Files  20 passed (20)
       Tests  58 passed (58)
```

（W4-2 后 52 PASS，本 change 新增 3+3=6 测试 → 58 PASS）

### TypeScript 类型检查

```text
$ cd apps/web && pnpm tsc --noEmit
（无输出 = clean）
```

## 偏离 design.md（DEV-N）

| # | 偏离点 | 原因 |
|---|---|---|
| DEV-1 | LOADER_NAMES 实际为 `["html-md","docx","pptx","jsonl"]`，不含 `pdf_mineru` / `markdown`；OPERATOR_NAMES 无 `normalize_unicode` / `strip_html`，实际 9 个：`identity/filter/dedup/score/chunker/image_strip/image_caption_stub/snapshot_tag/snapshot_sample` | grep 确认 packages/core LoaderRegistry / OperatorRegistry 实际注册列表，与 design 举例名不符。AC-2 测试改用 `html-md` + `chunker` 替代举例名 |
| DEV-2 | 新增 `@dnd-kit/utilities@^3` 依赖（design.md 仅列 @dnd-kit/core + @dnd-kit/sortable） | `@dnd-kit/sortable` 依赖 `CSS.Transform.toString`，来自 `@dnd-kit/utilities`；该包是 @dnd-kit/sortable 的 peerDep，需显式安装 |
| DEV-3 | routeTree.gen.ts 手动更新（非 vite plugin 自动生成） | 本地无 dev server；手动注册与 W4-2 同模式，与 plugin 生成格式一致 |

## 跨 change / 上游回归

- 全 web vitest：58/58 PASS（20 files）— W4-1 / W4-2 测试全部仍 PASS
- typecheck: clean（零错误）

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 AC-1..AC-4。
