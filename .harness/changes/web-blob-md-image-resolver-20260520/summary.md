---
change_id: web-blob-md-image-resolver-20260520
title: MD 预览支持 ![](images/x.jpg) → 仓内 blob
owner: application-owner-agent
started_at: 2026-05-20T03:09:54Z
stage: user_confirmation
status: done
last_updated: 2026-05-20T12:50:00Z
related_changes:
  - web-tree-nested-ui-20260520
  - processor-pdf-mineru-assets-20260520
---

# Summary

## 一句话目标

Web blob 预览页 markdown 支持 `![](images/x.jpg)` 相对路径自动解析为仓内 blob sha 并显示；用 react-markdown 替换最小 renderer。

## 范围摘要

- **In scope**：react-markdown + remark-gfm 依赖 / BlobPage 加 ?commit / FilesSection link 带 commit / CustomImage 用 useSubtreeByPath 解析路径 / ≥ 3 单测 / 9 AC self_check
- **Out of scope**：后端 / video/audio/iframe / syntax highlight / markdown editor / 远程图片代理

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 阶段 commit | 产物 / 报告 |
|---|---|---|---|---|---|
| 1 需求分析 | done | v1 | — | TBD | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | done | v1 | REVISION REQUIRED | — | [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) |
| 3 编码实现 | | | | | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | | | | | [code_review_v1.md](coding/review/code_review_v1.md) |
| 5 单测编写 | | | | | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | | | | | [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | | | | | _branch / push ref_ |
| 8 CI 验证 | | | | | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | | | | | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) |
| 10 用户确认 | | | | | _确认人 / 时间_ |

## 关键决策

| 时间 | 决策 | 理由 |
|---|---|---|
| 2026-05-20 | renderer 用 react-markdown + remark-gfm | 用户选定；业界标准；完整 markdown + GFM table |
| 2026-05-20 | 图片 src 重写在 BlobPage 组件里同步做 | 用户选定；用 useSubtreeByPath 异步拿 tree → entries 找 basename → 重写 src |
| 2026-05-20 | BlobPage URL 加 ?commit；FilesSection link 显式传 | 解相对路径必须知道 commit；URL search 比 main ref 兜底更准 |
| 2026-05-20 | stage 2/4/6 reviewer spawn 不偏离 | 沿前 change 模式 |

## 当前阻塞

- 无；等 stage 2 reviewer

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| 非范围 | syntax highlight | `web-md-syntax-highlight-*` |
| 非范围 | PDF / DOCX preview | `web-blob-pdf-preview-*` |
| 非范围 | markdown editor | `web-md-editor-*` |

## 交付

- Branch：`change/web-blob-md-image-resolver-20260520`（已合并 + 删除）
- PR：跳过 PR → no-ff merge
- Merge commit：`29486a1`
- 部署版本：n/a（vite build 自动 pick up）
- 用户确认：2026-05-20
- 关闭时间：2026-05-20T12:50:00Z
