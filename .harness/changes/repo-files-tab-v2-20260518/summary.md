---
change_id: repo-files-tab-v2-20260518
title: Repo 详情页 Files 独立 Tab + 文件预览页（独立路由 + 5MB + 4 格式）
owner: application-owner-agent
started_at: 2026-05-18T20:30:00Z
stage: request_analysis
status: waiting_review
last_updated: 2026-05-18T22:20:00Z
related_changes:
  - repo-files-tab-20260517
  - pipeline-ui-tab-20260518
  - web-mvp-pages-20260517
  - web-write-flows-20260517
  - commit-api-mvp-20260517
---

# Summary

> 这是本变更的 Single Source of Truth。任何阶段开始 / 通过 / 失败都必须同步更新这里。

## 一句话目标

把 Repo 详情页现有的 Files / Ingest / Pipelines 三个堆叠 section **改造为 Tab 切换**（Files 默认），并让 Files Tab 中的每个文件支持**点击进入独立预览页**（独立路由可分享 URL，按扩展名走 4 套渲染策略，5 MB 守门）。

## 范围摘要

- **In scope**：
  - AC-1：后端新增 `GET /repos/{o}/{n}/blobs/{sha}/meta` 返 `{sha256, size}`（与 GET /blobs/{sha} 同权限模型：`get_optional_user`；blob 不存在返 404）
  - AC-2：`apps/web/src/lib/api/queries.ts` 加 `useBlobMeta(owner, name, sha)` query + `BlobMetaResponse` TS 类型
  - AC-3：`apps/web/src/routes/repos/$owner.$name.tsx` 重构为 **Metadata 卡片 + Tabs**：Tab 由 URL `?tab=files|ingest|pipelines` 控制（默认 `files`；Tab 切换更新 search params，浏览器前进/后退可用）；非 admin 不渲染 Ingest / Pipelines Tab Trigger
  - AC-4：新路由 `apps/web/src/routes/blob.$owner.$name.$hash.tsx`（path 平铺，与既有 `commits.$owner.$name.$hash.tsx` 一致命名）；查询参数 `?path=...` 显示文件路径面包屑；按扩展名走 4 渲染策略（text / markdown rendered / image / binary fallback）+ 5 MB size guard；提供"返回 Files"链接
  - AC-5：Files Tab 的 entries 表 path 列变为 Link → `/blob/$owner/$name/$hash?path=<encoded path>`（保留既有"下载"链接不变）
  - AC-6：vitest 单测（**behavioral**）≥ 5 PASS，覆盖：(a) `useBlobMeta` 成功路径；(b) Tab URL state 切换；(c) BlobPage 文本预览渲染；(d) BlobPage 二进制 fallback 渲染；(e) BlobPage size > 5 MB 守门
  - AC-7：后端 pytest（**behavioral**）`test_blob_meta` ≥ 3 测试（200 + size 正确 / 404 / public repo 匿名可读）
  - AC-8：`scripts/_self_check.sh` 加 `run_repo_files_tab_v2` block；全仓 self_check 本 block 全 PASS；`apps/web && npm run build` 含 `built in` 且无 `error TS`（**behavioral**）

- **Out of scope**（明列以防范围爆炸）：
  - 嵌套目录 / tree 展开（仓库 commit-api-mvp 阶段决定 MVP 只支持单层 entry_type='blob'；嵌套树是另开 change `tree-nested-*` 的范畴）
  - 完整 Markdown 渲染（本 change 仅支持 headings / paragraph / unordered list / fenced code 4 类语法；inline emphasis / table / link / image inline 等 → follow-up `web-markdown-renderer-full-*`）
  - 引入第三方 markdown / 语法高亮库（保持零新依赖）
  - 文件内容编辑 / 删除（→ follow-up `web-blob-edit-*`，与既有写流程一致需经 commit）
  - 文件历史 / blame / diff 视图（→ Phase 2 lineage 可视化）
  - 分支切换器（main 已 hardcoded；ref 列表 / 切换 UI 是 follow-up `web-ref-switcher-*`）
  - SSE 推送大文件预览进度（5 MB 一次性 fetch 足够）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done | v2 | — | [spec.md](request_analysis/spec.md) v2 · [tasks.md](request_analysis/tasks.md) v2（闭 v1 review 5 MUST FIX + 3 SHOULD + 2 NICE） |
| 2 需求评审 | waiting_review | v2 待评 | v1 REVISION REQUIRED（已闭环） | v1：[spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md)；v2 待 reviewer 复检（仅检 MUST FIX 闭环，不全量重评） |
| 3 编码实现 | pending | — | — | coding/coding_report_v1.md |
| 4 编码评审 | pending | — | — | coding/review/code_review_v1.md |
| 5 单测编写 | pending | — | — | unit_test/test_report_v1.md |
| 6 单测评审 | pending | — | — | unit_test/review/test_review_v1.md |
| 7 代码推送 | pending | — | — | main 直接 commit（无 remote） |
| 8 CI 验证 | self-attest | — | — | 项目无 remote 长期未决（沿用既往）|
| 9 部署验证 | pending | — | — | deployment/deploy_verify_v1.md |
| 10 用户确认 | pending | — | — | 浏览器实测 |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-18 | Tab 状态用 URL `?tab=` 而非 React state | 可分享 URL；浏览器前进/后退；与 GitHub/HF 一致 | spec.md §架构 |
| 2026-05-18 | 文件预览用独立路由 `/blob/$owner/$name/$hash` 而非 Drawer/模态 | 用户问卷明示需要可分享 URL | spec.md §架构 |
| 2026-05-18 | 用 sha256 作为 URL path、path 作为 query string | sha256 是 CAS 一等公民；path 仅展示用（commit 内可重名→sha 不能） | spec.md §架构 |
| 2026-05-18 | 加后端 `/blobs/{sha}/meta` 端点而非前端流式累计 bytes | 一次轻量调用得 size；避免浪费 5MB 带宽 + 中断 fetch 体验差 | spec.md §架构 |
| 2026-05-18 | Markdown rendered 仅支持 4 类语法 + 内置 renderer（不引入 marked/react-markdown） | 零新依赖；本 change 完成 80% 用户价值；剩余语法 follow-up | spec.md §架构 |
| 2026-05-18 | 不动既有 commit 详情页的 entries 表 | 范围隔离；commit 页是历史快照视图，与 Files Tab 的"工作目录"视图职责不同 | spec.md §非范围 |

## 当前阻塞

- spec_v2 / tasks_v2 已提交（闭 v1 review 全部 MUST FIX + SHOULD FIX + NICE）；等待 stage 2 reviewer v2 复检（建议 sonnet，仅复检 MUST FIX 闭环）。

## Deferred 项（已 review 通过但未在本 change 内修）

> 评审/实施过程产生的非 MUST FIX 项，关闭本 change 时回填。

| 类型 | 描述 | 跟进位置 |
|---|---|---|

## 交付

> 关闭本变更时填写。

- Branch：main（无 remote）
- PR：N/A
- Merge commit：—
- 部署版本（如有）：—
- 用户确认：—
- 关闭时间：—

## 复盘（可选）

> 关闭时填写。
