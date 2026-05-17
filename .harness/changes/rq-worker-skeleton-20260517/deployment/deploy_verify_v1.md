---
change_id: rq-worker-skeleton-20260517
version: 1
env: skipped
deployed_at: 2026-05-17T15:00:00Z
status: skipped
---

# Deploy Verify v1

## 部署面

本变更引入新进程 `worker/dataplat_worker/main.py`，但 MVP 不部署独立 worker 服务：

- 测试用 thread + dequeue 同进程替身覆盖语义
- alembic 0003 已 PG 跑过 upgrade head（CI 等价 self_check AC-2）
- 生产部署独立 worker 进程 / k8s Deployment 留 follow-up `worker-deploy-k8s-*`

## skipped 理由

- 无新 docker image 要 push（worker 已存在的 worker.Dockerfile 是 bootstrap-monorepo 占位）
- 测试已覆盖 worker 逻辑等价路径
- design.md §11.5 Phase 2+ 才上 k8s

## 下一步

stage 10 close。
