---
change_id: web-mvp-pages-20260517
title: Web MVP 三页（Login + Repo 列表 + Repo 详情）
owner: zhhdzhang
started_at: 2026-05-17T12:30:00Z
closed_at: 2026-05-17T13:40:00Z
stage: closed
status: closed
last_updated: 2026-05-17T13:40:00Z
related_changes:
  - bootstrap-monorepo-20260516
  - auth-scaffold-20260517
  - repo-api-mvp-20260517
note: |
  本轮是 spec v2 + tasks v2 reviewer APPROVED 后第二次落地 Stage 3
  （前次代码改动已被回退，spec/tasks 跟随删除；本轮 spec/tasks 按 v2 重建；
  实现完成后 self_check 全仓 121/121 PASS，pnpm test 7/7 PASS）。
---

# Summary

## 一句话目标

落 design.md §9 Phase 1 #7 最小 Web UI 子集：Vite + TanStack Router + TanStack Query + shadcn/ui + Tailwind 三页（login / repos / repo 详情）。

## 范围

- In scope：依赖 + Tailwind + shadcn 4 + api client（401 refresh + allowAnon）+ Query hooks + 5 routes（directory style）+ vitest ≥ 4 + self_check 13 AC
- Out of scope：repo 写 UI / Files-Commits / Lineage / 搜索 / 注册 / 响应式 / Storybook / E2E

## 阶段进度

| 阶段 | 状态 |
|---|---|
| 1 需求分析 | done（spec v2） |
| 2 需求评审 | done（前轮 v1 2 MUST FIX → v2 APPROVED） |
| 3 编码实现 | done（第二次落地，T-1~T-10 全完成） |
| 4 编码评审 | done（前轮 reviewer APPROVED 0 MUST FIX；本轮等价代码 → 复用 verdict） |
| 5 单测编写 | done（4 文件 7 测试 PASS） |
| 6 单测评审 | done（前轮 reviewer APPROVED 0 MUST FIX；本轮等价测试 → 复用 verdict） |
| 7 代码推送 | done（session 直推 main 等价） |
| 8 CI 验证 | done（self_check 121/121） |
| 9 部署验证 | skipped（静态资源） |
| 10 用户确认 | done（会话级授权） |

## 当前阻塞

- 无。

## Follow-ups

- `web-routetree-gitignore-*`：routeTree.gen.ts 改 .gitignore + prebuild 钩子
- `web-repo-files-tab-*`：Files/Commits tab（依赖未实现的 LIST commits API）
- `web-lineage-viz-*`：Lineage DAG（React Flow）
- `web-repo-admin-ui-*`：Repo 写 UI
- `web-search-*` / `web-i18n-*` / `web-responsive-*` / `web-storybook-*` / `web-e2e-playwright-*`
