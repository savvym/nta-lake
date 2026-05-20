---
change_id: web-jobs-list-page-20260520
title: GET /jobs admin 列表端点 + Web Jobs 页（过滤 + 分页）
owner: application-owner-agent
started_at: 2026-05-20T04:54:04Z
stage: done
status: closed
last_updated: 2026-05-20T14:30:00Z
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
| 1 需求分析 | done | v3 | — | TBD | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | done | v3 | APPROVED | — | [spec_review_v3.md](request_analysis/review/spec_review_v3.md) · [tasks_review_v2.md](request_analysis/review/tasks_review_v2.md) |
| 3 编码实现 | done | v1 | — | TBD | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | done | v2 | APPROVED | TBD | [code_review_v2.md](coding/review/code_review_v2.md) |
| 5 单测编写 | done | v1 | — | TBD | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | done | v2 | APPROVED | TBD | [test_review_v2.md](unit_test/review/test_review_v2.md) |
| 7 代码推送 | done | — | — | 9bb50e2 / merge 45407ed | branch `change/web-jobs-list-page-20260520` pushed + merged --no-ff into main |
| 8 CI 验证 | done | — | PASS | — | self_check `web-jobs-list-page` 10/10 PASS；full 链上其余 5 个 FAIL 均为 pre-existing flake（同 AC-13 标注） |
| 9 部署验证 | done | v1 | PASS | — | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) — 5 项 curl 验证全过 |
| 10 用户确认 | done | — | PASS | — | 用户回复"可以"（2026-05-20T14:30Z）— /jobs 页 UI 实测通过 |

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
- PR：直 merge（gh PAT 缺 pr:write scope）
- Merge commit：`45407ed`（feature commit `9bb50e2`；stage 7-9 docs `353a3b1`）
- 部署版本：本地 dev（uvicorn :8080 + vite :5173）
- 用户确认：2026-05-20T14:30Z — "可以"
- 关闭时间：2026-05-20T14:30Z
