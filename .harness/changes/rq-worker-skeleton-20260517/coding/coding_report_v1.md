---
change_id: rq-worker-skeleton-20260517
version: 1
authored_at: 2026-05-17T14:45:00Z
branch: main
base_commit: 23a5fcb (web-mvp-pages close)
head_commit: working-tree
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 说明 |
|---|---|---|
| `apps/api/pyproject.toml` | edit | 加 rq>=2.0 + redis>=5.0 |
| `apps/api/dataplat_api/models/job.py` | new | JobORM（9 字段） |
| `apps/api/dataplat_api/models/__init__.py` | edit | export JobORM |
| `apps/api/alembic/versions/0003_jobs.py` | new | jobs 表 + 3 索引 |
| `apps/api/dataplat_api/jobs/__init__.py` | new | 模块入口 |
| `apps/api/dataplat_api/jobs/redis_client.py` | new | get_redis + get_queue 单例 |
| `apps/api/dataplat_api/jobs/service.py` | new | JobsService（5 方法） |
| `apps/api/dataplat_api/jobs/tasks.py` | new | run_ingest_job（sync + asyncio.run wrap） |
| `apps/api/dataplat_api/schemas/job.py` | new | JobIngestRequest / JobRead |
| `apps/api/dataplat_api/schemas/__init__.py` | edit | export 2 job schemas |
| `apps/api/dataplat_api/routers/jobs.py` | new | POST /jobs/ingest + GET /jobs/{job_id} |
| `apps/api/dataplat_api/main.py` | edit | include_router(jobs_router) |
| `worker/src/dataplat_worker/main.py` | new | Worker.work() 阻塞循环 |
| `worker/src/dataplat_worker/__main__.py` | edit | 调 main.main() 取代 placeholder |
| `apps/api/tests/test_jobs.py` | new | 10 集成测试（含端到端 worker 跑通） |
| `packages/api-types/openapi.json` | edit | codegen 同步 /jobs 2 paths |
| `scripts/_self_check.sh` | edit | 追加 run_rq_worker_skeleton 13 AC + 三探针 helper；auth-scaffold AC-2 兼容 0003 head |

## 与 tasks.md 的映射

| Task | 状态 |
|---|---|
| T-1 JobORM + 0003 | done（PG migrate 通过） |
| T-2 deps | done（rq 2.8 + redis 5.x） |
| T-3 redis_client | done |
| T-4 JobsService | done（5 方法 + 失败 rollback） |
| T-5 tasks.py | done（asyncio.run + 独立 engine + swallow exception） |
| T-6 schemas + router | done |
| T-7 worker/main.py | done |
| T-8 tests | done（10 PASS） |
| T-9 self_check | done（13 AC） |
| T-10 lint+mypy | done（67 files clean） |

## 偏离 spec / trade-off

- **测试 RQ worker 用 thread + 直接 dequeue**（非 SimpleWorker）：spec AC-11 写 SimpleWorker burst，但实测：
  - SimpleWorker 装 SIGINT/SIGTERM signal handler → 线程内 `ValueError: signal only works in main thread`
  - SimpleWorker 装 SIGALRM death penalty → 同上
  - 改用 `queue.pop_job_id() + Job.fetch + 直接 import call`，跳过 RQ Worker 抽象
  - 等价：直接调用 `dataplat_api.jobs.tasks.run_ingest_job(job_id)` 同步函数；语义不变
  - 生产用真 `worker/main.py` 跑 RQ Worker（主进程，signal 正常）
- **`asyncio.run` 嵌套**：tasks.run_ingest_job 用 asyncio.run 跑 async session，但 pytest-asyncio 的测试主线程有 event loop running → 直接调会 raise。**缓解**：测试用 `asyncio.to_thread(...)` 把 worker 循环移到子线程；子线程 fresh event loop；OK
- **auth-scaffold AC-2 兼容更新**：head 现在 0003 → grep history 而非 current
- **worker tasks 用独立 engine**：每个 task 调 `_make_engine_factory()` 创建新 engine + sessionmaker；不复用 FastAPI engine（跨进程边界清晰）。性能 trade-off：每个 task 都建 engine（数毫秒 connect pool warmup）；MVP 接受

## 本地校验

```text
ruff: All checks passed!
mypy: Success: no issues found in 67 source files
pytest: 74 passed in ~30s（含 10 新 test_jobs.py + 64 既有回归）
self_check rq-worker-skeleton: PASS=13 FAIL=0
self_check 全仓: PASS=134 FAIL=0
make codegen: openapi.json 同步含 /jobs 2 paths
```

## 已知未解决

- worker fork 时的 SQLAlchemy engine 共享：生产用 RQ Worker fork 模式时，每个 forked subprocess 调 `_make_engine_factory` 新建 engine——若并发上来 connection 数线性增长，需 follow-up `worker-engine-pool-*` 加 process-level pool
- 测试通过 thread + dequeue 跳过真 RQ Worker，**没覆盖生产 Worker 的 signal/death penalty 路径**——follow-up `worker-integration-test-subprocess-*` 用 docker compose 跑真 worker

## reviewer 重点

1. **asyncio.run + 独立 engine 在跨进程是否真稳**？fork worker 时 connection 复用问题
2. **测试用 thread + dequeue 是否合理 trade-off**？还是应该写真 worker 集成测试
3. **JobORM payload jsonb plain dict 序列化**：IngestRequest model_dump(mode="json") 与 worker 反构 model_validate 是否真的 round-trip 一致
4. **auth-scaffold AC-2 跨变更兼容更新**是否 scope creep

## 下一步

stage 4 编码评审：独立 reviewer。
