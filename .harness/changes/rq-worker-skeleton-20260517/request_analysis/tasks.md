---
change_id: rq-worker-skeleton-20260517
version: 1
authored_at: 2026-05-17T14:00:00Z
---

# Tasks

## T-1 JobORM + alembic 0003

- 新建 `apps/api/dataplat_api/models/job.py`：`JobORM`（id uuid PK / type str / status str / payload jsonb / result jsonb? / error str? / created_at / started_at? / completed_at?）
- 更新 `models/__init__.py` export JobORM
- 新建 `apps/api/alembic/versions/0003_jobs_table.py`：down_revision=0002；create jobs 表 + index on (status, created_at)
- 测试 PG 跑 `alembic upgrade head`
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-1, AC-2

## T-2 apps/api 加 rq + redis 依赖

- `apps/api/pyproject.toml` dependencies 加 `rq>=2.0` + `redis>=5.0`（与 worker/ 已声明对齐）
- 跑 `uv sync --all-extras` 确认安装
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-3, AC-12

## T-3 jobs/redis_client.py

- 新建 `apps/api/dataplat_api/jobs/__init__.py`
- 新建 `apps/api/dataplat_api/jobs/redis_client.py`：
  - `_redis: Redis | None = None`
  - `def get_redis() -> Redis`：env `DATAPLAT_REDIS_URL` 默认 `redis://localhost:6379/0`
  - `def get_queue() -> Queue`：`Queue('default', connection=get_redis())`
- depends_on: T-2 / estimated_stage: stage-3 / AC: AC-3

## T-4 JobsService

- 新建 `apps/api/dataplat_api/jobs/service.py`：
  - `JobsService.enqueue(session, job_type, payload) -> JobORM`：INSERT JobORM(status='queued') + queue.enqueue(run_ingest_job, str(job.id))；失败时 DELETE JobORM + raise 500
  - `JobsService.get_by_id(session, job_id) -> JobORM | None`
  - `JobsService.mark_running(session, job_id) -> None`：set status='running', started_at=now()
  - `JobsService.mark_succeeded(session, job_id, result: dict) -> None`：set status='succeeded', result, completed_at
  - `JobsService.mark_failed(session, job_id, error: str) -> None`：set status='failed', error, completed_at
- depends_on: T-1, T-3 / estimated_stage: stage-3 / AC: AC-4

## T-5 jobs/tasks.py（worker 可调）

- 新建 `apps/api/dataplat_api/jobs/tasks.py`：
  - `run_ingest_job(job_id: str) -> None`（同步函数 RQ 兼容）
  - 内部 `asyncio.run(_run_ingest_job_async(job_id))`
  - `_run_ingest_job_async`：
    1. 新建独立 async engine + session（不依赖 FastAPI lifecycle）+ MinioBlobStore from env
    2. JobsService.get_by_id → 取 payload
    3. JobsService.mark_running
    4. 反构 IngestRequest from payload['request']；取 owner / name；查 RepositoryORM by owner+name
    5. AdapterRunner.run(session, store, repo.id, request) → (commit, dedup, result)
    6. JobsService.mark_succeeded(session, job_id, result={"commit_hash": commit.hash, "deduplicated": dedup, "ingest_summary": {...}})
    7. except 任何 Exception → JobsService.mark_failed(session, job_id, error=str(exc))；不 re-raise
- depends_on: T-1, T-3, T-4 / estimated_stage: stage-3 / AC: AC-5

## T-6 schemas + router

- 新建 `apps/api/dataplat_api/schemas/job.py`：
  - `JobIngestRequest(owner: str, name: str, request: IngestRequest)` extra=forbid
  - `JobRead(id: str, type: str, status: str, payload: dict[str, Any], result: dict[str, Any] | None, error: str | None, created_at, started_at, completed_at)` extra=forbid
- 更新 `schemas/__init__.py`
- 新建 `apps/api/dataplat_api/routers/jobs.py`：
  - `APIRouter(prefix="/jobs", tags=["jobs"])`
  - `POST /ingest`：admin + `_resolve_repo`（owner/name 不可见 → 404）→ `JobsService.enqueue(session, "ingest", payload={"owner","name","request"})` → 201 + JobRead
  - `GET /{job_id}`：require login → `JobsService.get_by_id` → None 404 / 200 + JobRead
- main.py include + make codegen
- depends_on: T-4, T-5 / estimated_stage: stage-3 / AC: AC-6, AC-7, AC-8, AC-9

## T-7 worker/main.py

- 新建 `worker/src/dataplat_worker/main.py`：
  - import os, redis, rq
  - `def main() -> int`：env `DATAPLAT_REDIS_URL` → Redis → `Worker(['default'], connection=...).work()`
  - 改 `__main__.py` 调 `main.main()`
- depends_on: T-2 / estimated_stage: stage-3 / AC: AC-10

## T-8 集成测试 ≥ 10

- 新建 `apps/api/tests/test_jobs.py`：
  - 探针：PG + MinIO + Redis 三 skipif
  - Fixture：admin_user / normal_user / `_override_blob_store`（复用模式）
  - 测试 (a)~(j) 10 个对应 AC-11
  - (g)(h)(i)(j) 需 SimpleWorker burst：
    ```python
    from rq import SimpleWorker
    worker = SimpleWorker(["default"], connection=get_redis())
    worker.work(burst=True)
    ```
- depends_on: T-1~T-7 / estimated_stage: stage-3 / AC: AC-11

## T-9 self_check rq-worker-skeleton block

- 追加 `run_rq_worker_skeleton` 13 AC + filter；Redis 探针 helper（_redis_reachable）；三探针组合
- depends_on: T-1~T-8 / estimated_stage: stage-3 / AC: AC-13

## T-10 lint+mypy gate

- ruff + mypy 全 PASS（含 worker/src）
- depends_on: T-9 / estimated_stage: stage-3 / AC: AC-12

## T-11 stage-2 spec/tasks review（process）

- description：独立 reviewer 评审 spec + tasks
- depends_on: T-1~T-10 v1 完
- estimated_stage: stage-2

## T-12 stage-4 coding review（process）

- description：独立 reviewer 对 working-tree diff 评审
- depends_on: T-1~T-10
- estimated_stage: stage-4

## T-13 stage-5/6 test_report + unit-test review（process）

- description：写 unit_test/test_report + 独立 reviewer review
- depends_on: T-8
- estimated_stage: stage-6

## T-14 stage-7 CI 验证（process）

- description：`bash scripts/_self_check.sh` 全仓
- depends_on: T-9, T-13
- estimated_stage: stage-7

## T-15 stage-9 deploy verify（process，skipped）

- description：worker 是新进程但 MVP 用 SimpleWorker burst 测试不部署独立服务；deploy_verify_v1.md skipped
- depends_on: T-14
- estimated_stage: stage-9

## T-16 stage-10 close（process）

- description：summary.md stage=closed；更新 session_handoff（10 个 closed change）
- depends_on: T-14, T-15
- estimated_stage: stage-10

## 任务依赖图

```
T-1 (JobORM + 0003) ─┐
T-2 (deps) ──────────┼──→ T-3 (redis_client) ──→ T-4 (JobsService) ──→ T-5 (tasks) ──┐
                     └──→ T-7 (worker main)                                            ├──→ T-6 (router) ──→ T-8 (tests) ──→ T-9 (self_check) ──→ T-10 (lint)
                                                                                       
T-10 → T-11 → T-12 → T-13 → T-14 → T-15 → T-16
```

## AC 覆盖矩阵

| AC | task |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-1 |
| AC-3 | T-2, T-3 |
| AC-4 | T-4 |
| AC-5 | T-5 |
| AC-6 | T-6 |
| AC-7 | T-6 |
| AC-8 | T-6 |
| AC-9 | T-6 |
| AC-10 | T-7 |
| AC-11 | T-8 |
| AC-12 | T-2, T-10 |
| AC-13 | T-9 |
