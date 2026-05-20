---
change_id: web-jobs-list-page-20260520
title: GET /jobs admin 列表端点 + Web Jobs 页（过滤 + 分页）
owner: application-owner-agent
started_at: 2026-05-20T04:54:04Z
stage: request_analysis
status: waiting_review
last_updated: 2026-05-20T13:05:00Z
related_changes:
  - rq-worker-skeleton-20260517
---

# Summary

## 一句话目标

后端加 GET /jobs admin 列表端点（过滤 status/type + 分页）；Web 新建 /jobs 列表页 + 导航入口；解决"看不到队列里有什么 job / 跑得怎么样"的痛点。

## 范围摘要

- **In scope**：JobListResponse / list_jobs / GET /jobs (admin) / pytest ≥ 4 / useJobs hook / jobs.tsx 列表页 / 导航 link / vitest ≥ 5 / self_check 10 AC
- **Out of scope**：JobORM.owner_id / live poll / cancel/retry / 改单 job 详情页

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 阶段 commit | 产物 / 报告 |
|---|---|---|---|---|---|
| 1 需求分析 | done | v1 | — | TBD | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | pending | — | — | — | 待 spawn |
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
| 2026-05-20 | GET /jobs admin only | JobORM 无 owner 列；admin 看全部最稳；多用户隔离开 follow-up |
| 2026-05-20 | 过滤 status/type + 分页 | 用户选定 |
| 2026-05-20 | 不引入 live poll | 手动 refresh 够用 |
| 2026-05-20 | stage 2/4/6 全 reviewer spawn | 沿前 change 模式 |

## 当前阻塞

- 无；等 stage 2 reviewer

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| 非范围 | JobORM 加 owner_id + ACL | `jobs-owner-acl-*` |
| 非范围 | live poll / WebSocket | `web-jobs-list-live-poll-*` |
| 非范围 | cancel / retry / kill 按钮 | `jobs-cancel-*` |

## 交付

- Branch：`change/web-jobs-list-page-20260520`（基于 main）
- PR：TBD（直 merge）
- Merge commit：TBD
- 部署版本：n/a
- 用户确认：TBD
- 关闭时间：TBD
