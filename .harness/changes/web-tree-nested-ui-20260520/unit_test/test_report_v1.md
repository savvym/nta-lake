---
change_id: web-tree-nested-ui-20260520
version: 1
authored_at: 2026-05-19T18:50:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC ID | 测试文件 | 测试函数 |
|---|---|---|
| AC-4 (默认 root 渲染 + folder/blob 区分) | repos.files-section.test.tsx | "嵌套 commit：根级渲染 folder icon + blob 混合" |
| AC-4 (点 folder 触发 setPath) | repos.files-section.test.tsx | "点 folder：URL ?path 更新" |
| AC-4 (面包屑回退) | repos.files-section.test.tsx | "面包屑：path 非空时显示路径段 + 返回上一级；点段回退" |
| AC-4 (error UI + 返根目录按钮) | repos.files-section.test.tsx | "path 不存在：渲染错误 message + 返根目录按钮" |
| AC-5 (legacy 扁平兼容) | repos.files-section.test.tsx | "legacy 扁平 commit：渲染扁平 entry list，无 folder icon，下载链可用" |
| AC-2 (queryFn 串行 fetch + null-guard + segment 校验) | queries.tree-nested.test.tsx | 5 用例（happy / null-guard / segment 不存在 / blob 而非 tree / "//" 空段过滤） |
| AC-6 (≥ 4 新用例) | both files | 5 (files-section) + 5 (queries) = 10 新用例 |
| AC-7 (现有不回归) | repos.tabs.test.tsx 等 | 26 - 5 + 5 = 26 上轮基线全通；现 31/31 PASS |

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| apps/web/src/routes/repos.files-section.test.tsx | 集成（路由 + UI 渲染） | 5 |
| apps/web/src/lib/api/queries.tree-nested.test.tsx | 单元（hook queryFn 直接跑） | 5 |
| 其他现有文件 | 不变 | 21 (合计 26→31，新增 10 个用例覆盖本 change) |

## Mock 范围

- repos.files-section.test.tsx：mock 整个 `../lib/api/queries`（用 mockSubtreeState 闭包动态切换 data / isLoading / isError），让 UI 测试聚焦渲染逻辑而不被 fetch 链拖
- queries.tree-nested.test.tsx：仅 spy `fetchJson`（client.ts），让 useSubtreeByPath 的 queryFn **真跑**（spawn reviewer 报的 MUST FIX-2 修复点）；覆盖 null-guard / segment 校验 / 串行 fetch 算法

## 本地运行

```text
$ pnpm test -- --run
 Test Files  14 passed (14)
      Tests  31 passed (31)
   Duration  3.20s

$ pnpm typecheck
> tsc --noEmit -p tsconfig.json
 success（0 errors）
```

## 已知 flaky / 跳过

无；31 PASS 0 fail 0 skip。

## 偏离 spec / trade-off

- **MUST FIX-2 增补 queryFn 单测**：stage 6 reviewer v1 抓到 useSubtreeByPath 的 queryFn 被 module-level mock 完全隐藏，未覆盖。新建 queries.tree-nested.test.tsx 用 spy + renderHook + 真 QueryClient 让 queryFn 真跑；5 用例覆盖 null-guard / 不存在 segment / blob-not-tree / 空段过滤 / happy path
- **Test file extension .ts → .tsx**：JSX wrapper function 需要 .tsx 后缀；esbuild 否则 transform fail

## 下一步

stage 6 v2 reviewer 复检 MUST FIX-2 / MUST FIX-3 是否真修。
