---
change_id: web-ingest-path-default-20260520
title: Ingest 上传默认 path 改为文件名（去 content/ 前缀）
owner: application-owner-agent
started_at: 2026-05-20T02:35:05Z
stage: user_confirmation
status: done
last_updated: 2026-05-20T11:35:00Z
related_changes:
  - tree-nested-domain-20260520
  - web-tree-nested-ui-20260520
---

# Summary

## 一句话目标

Web Ingest tab 默认上传 path 改为 `f.name`（仓根），不再硬加 `content/` 前缀。

## 范围摘要

- **In scope**：`$owner.$name.tsx:583` 默认 path 改 + 测试断言同步 + self_check 6 AC
- **Out of scope**：后端 / "upload into folder" UI 控件 / 历史 commit

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 阶段 commit | 产物 / 报告 |
|---|---|---|---|---|---|
| 1 需求分析 | done | v1 | — | TBD | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | revision_required | v1 | REVISION REQUIRED（spec 3 MUST FIX / tasks 1 MUST FIX） | — | [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) |
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
| 2026-05-20 | 默认 path = f.name（仓根） | 用户选定；与"上传一个 PDF"直觉一致；批量分目录可手工改 path |
| 2026-05-20 | stage 2/4/6 走完整 reviewer spawn | 沿 tree-nested-domain / web-tree-nested-ui 模式 |

## 当前阻塞

- 无；等 stage 2 reviewer

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| 非范围 | "upload into folder" UI 控件 | follow-up `web-ingest-folder-picker-*` |

## 交付

- Branch：`change/web-ingest-path-default-20260520`（已合并 + 删除）
- PR：跳过 PR → no-ff merge
- Merge commit：`2f7a34e`
- 部署版本：n/a
- 用户确认：2026-05-20
- 关闭时间：2026-05-20T11:35:00Z
