---
change_id: rq-worker-skeleton-20260517
title: RQ Worker Skeleton + 异步 ingest job
owner: zhhdzhang
started_at: 2026-05-17T14:00:00Z
closed_at: 2026-05-17T15:05:00Z
stage: closed
status: closed
last_updated: 2026-05-17T15:05:00Z
related_changes:
  - adapter-framework-20260517
  - commit-api-mvp-20260517
---

# Summary

## 一句话目标

落 design.md §5.3 + §9 Phase 1 #5 异步队列子集：RQ + Redis + worker 进程 + JobORM + `POST /jobs/ingest` 异步分发 + `GET /jobs/{id}` 状态查询。in-process MVP（subprocess 隔离推后）。

## 范围

- In scope：rq + redis 依赖；jobs ORM + 0003 migration；JobsService + tasks.py + redis_client；2 routes；worker/main.py；10 集成 + 13 self_check
- Out of scope：subprocess L2 / L3；retry / cancel / GC / ACL / 多 worker 调度；processor job type；Web Jobs page

## 关键决策

| 决策 | 选择 |
|---|---|
| 执行模型 | in-process MVP |
| Worker async 调用 | asyncio.run 包 async session |
| Job 持久化 | 自建 jobs 表（非 RQ 内部 state） |
| Status 类型 | str + 应用层约束 |
| Job 读权限 | MVP 任何登录可读 |
| Worker DB session | 独立 async engine |

## 阶段进度

| 阶段 | 状态 |
|---|---|
| 1 需求分析 | done（spec v2） |
| 2 需求评审 | done（v1 1 MUST FIX → v2 APPROVED；SKILL 反哺 8th 条 dry-parse） |
| 3 编码实现 | done（10 个 T-*） |
| 4 编码评审 | done（reviewer APPROVED 0 MUST FIX） |
| 5 单测编写 | done（10 测试） |
| 6 单测评审 | done（reviewer APPROVED 0 MUST FIX） |
| 7 代码推送 | done（session 直推 main 等价） |
| 8 CI 验证 | done（self_check 134/134） |
| 9 部署验证 | skipped（worker 容器/服务部署留 follow-up） |
| 10 用户确认 | done |

## 当前阻塞

- 无。

## Follow-ups

- `adapter-subprocess-isolation-*`：L2 plugin subprocess 隔离
- `job-retry-backoff-*` / `job-cancel-*` / `job-result-gc-*` / `job-acl-*`
- `worker-engine-pool-*`：worker fork 时 connection pool 优化
- `worker-integration-test-subprocess-*`：用 docker-compose 跑真 worker E2E
- `processor-job-type-*`：扩展 job_type=processor
- `web-jobs-page-*`：前端 Jobs 状态 UI
- `redis-auth-tls-*`：生产 Redis 安全配置
