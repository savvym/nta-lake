---
change_id: web-tree-nested-ui-20260520
title: Web Files tab 树形导航（HF 风 + ?path + 面包屑）
owner: application-owner-agent
started_at: 2026-05-19T14:56:03Z
stage: request_analysis
status: waiting_review
last_updated: 2026-05-19T16:55:00Z
related_changes:
  - tree-nested-domain-20260520
  - repo-files-tab-20260517
  - repo-files-tab-v2-20260518
---

# Summary

## 一句话目标

Files tab 改 HF 风：默认显示根级 entries（混 folder + file），点 folder 进入该层，面包屑可点击回退，URL `?path=images/sub` 可书签；legacy 扁平 commit 自然降级为扁平表。

## 范围摘要

- **In scope**：queries.ts 加 `useSubtree` + `useSubtreeByPath`；路由 search 加 `path`；FilesSection 改造（面包屑 + folder icon + click navigation）；vitest ≥ 4 新用例；self_check 12 AC
- **Out of scope**：后端（tree-nested-domain 已就绪）/ `?recursive` 切换按钮 / 分页 / file preview / 虚拟滚动

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 阶段 commit | 产物 / 报告 |
|---|---|---|---|---|---|
| 1 需求分析 | done | v1 | — | TBD | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | waiting_revision | v1 | REVISION REQUIRED | — | [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) |
| 3 编码实现 | | | | | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | | | | | [code_review_v1.md](coding/review/code_review_v1.md) |
| 5 单测编写 | | | | | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | | | | | [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | | | | | _branch / push ref_ |
| 8 CI 验证 | | | | | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | | | | | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) |
| 10 用户确认 | | | | | _确认人 / 时间_ |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-19 | HF 风（默认本级 + ?path 面包屑） | 用户选定；类 git ls-tree 语义；URL 可书签 | spec.md §背景 |
| 2026-05-19 | 不分页（MVP） | 用户选定；81 行可滚动；大目录虚拟滚动留 follow-up | spec.md §非范围 |
| 2026-05-19 | stage 2/4/6 全 reviewer spawn 不偏离 | 沿 tree-nested-domain 模式 | tasks.md process_tasks |

## 当前阻塞

- stage 2 REVISION REQUIRED（4 MUST FIX + 6 SHOULD FIX）；需 generator 修 spec v2 + tasks v2 后重提评审

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| 非范围 | 大目录虚拟滚动 | `web-tree-virtual-scroll-*` |
| 非范围 | file preview / search inside dir | `web-tree-preview-*` |
| 非范围 | ?recursive=1 切换按钮 | `web-tree-recursive-toggle-*` |

## 交付

- Branch：`change/web-tree-nested-ui-20260520`（基于 main）
- PR：TBD（push 后直 merge，沿前例）
- Merge commit：TBD
- 部署版本：n/a（仅前端 vite build）
- 用户确认：TBD
- 关闭时间：TBD
