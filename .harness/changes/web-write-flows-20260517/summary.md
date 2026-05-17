---
change_id: web-write-flows-20260517
title: Web 写流程 UI（建 repo / Edit / Delete / Ingest / Job / Commit 详情）
owner: zhhdzhang
started_at: 2026-05-17T15:30:00Z
closed_at: 2026-05-17T16:05:00Z
stage: closed
status: closed
last_updated: 2026-05-17T16:05:00Z
related_changes:
  - web-mvp-pages-20260517
  - repo-api-mvp-20260517
  - commit-api-mvp-20260517
  - rq-worker-skeleton-20260517
---

# Summary

## 目标

扩 Web UI 覆盖 admin 写流程：建 repo / Edit / Delete / 上传文件 + ingest / Job 状态 / Commit 详情 + 下载 blob。端到端 admin 工作流可在浏览器跑完。

## 范围

- In scope：3 新页面（/repos/new、/jobs/$id、/commits/$o/$n/$h）+ /repos/$o/$n 详情页改造（admin 写按钮）+ /repos 列表加 New 按钮 + queries.ts 扩 7 hook + shadcn textarea + vitest ≥ 3 + self_check 13 AC
- Out of scope：LIST commits/jobs（需先加后端）/ Lineage viz / 用户管理 / 搜索 / 响应式 / E2E

## 关键决策

- 不加后端路由；range tight
- 路由文件 flat naming
- 上传走 fetchJson + Blob body
- 轮询 refetchInterval 1s，成功停
- Delete 用 window.confirm
- Layer/Subtype 用原生 `<select>`

## 阶段进度

| 阶段 | 状态 |
|---|---|
| 1 需求分析 | in_progress |
| 2 需求评审 | pending |
| 3 编码实现 | pending |
| 4 编码评审 | pending |
| 5 单测编写 | pending |
| 6 单测评审 | pending |
| 7 代码推送 | pending |
| 8 CI 验证 | 本地 self_check |
| 9 部署验证 | skipped（静态） |
| 10 用户确认 | 会话级 |

## 当前阻塞

- 无。等 stage 2 reviewer。
