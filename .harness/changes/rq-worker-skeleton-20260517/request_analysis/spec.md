---
change_id: rq-worker-skeleton-20260517
version: 2
authored_at: 2026-05-17T14:15:00Z
status: draft
revisions:
  - v1 → v2：消化 stage 2 reviewer 1 MUST FIX（AC-4 Python 复合语句 SyntaxError），
    `for m in [...]: assert ...` 改 `assert all(hasattr(JobsService, m) for m in [...])` generator；
    同步反哺 .harness/skills/request-analysis/SKILL.md 跨 AC 自审清单第 8 条
    「AC 验证命令必须真跑 dry-parse」（rq-worker-skeleton 触发的新型反哺）。
---

# Spec：RQ Worker Skeleton + 异步 ingest job

## 背景

9 个变更后数据底座 + Adapter 框架 + Web UI 完整。adapter-framework 的 `AdapterRunner.run()` 是**同步 in-process** 执行；长跑 adapter 会阻塞 FastAPI 线程池。design.md §5.3 + §9 Phase 1 #5 要求"Worker：RQ + subprocess 启动 plugin"——本变更落 RQ + Redis 异步队列最小子集。

## 问题陈述

- `POST /repos/{o}/{n}/ingest` 同步；adapter 长跑时阻塞请求
- 没有 job 持久化：客户端关闭连接后无法查状态
- 没有跨进程 worker pool
- `worker/dataplat_worker/` 仅占位

## 范围

In scope：

- 复用 worker/pyproject.toml 已声明 `rq>=2.0` + `redis>=5.0`
- 新 ORM `jobs(id PK uuid, type str, status str, payload jsonb, result jsonb, error str, created_at, started_at, completed_at)` + alembic 0003
- `apps/api/dataplat_api/jobs/`：`service.py` + `tasks.py` + `redis_client.py`
- `schemas/job.py`：JobIngestRequest + JobRead
- `routers/jobs.py`：POST /jobs/ingest（admin）+ GET /jobs/{job_id}（logged-in）
- `worker/dataplat_worker/main.py`：连 Redis + RQ Worker.work() loop
- 集成测试 ≥ 10（RQ SimpleWorker burst 同进程）
- self_check ≥ 13 AC

Out of scope（follow-up）：

- subprocess 隔离 L2：`adapter-subprocess-isolation-*`
- L3 容器：Phase 2+
- Job retry / backoff / cancel / result GC / ACL / 多 worker 调度
- Processor job type：`processor-job-type-*`
- Web Jobs page：`web-jobs-page-*`

## 验收标准（13 AC + 验证方式）

### 结构 / 接口（AC-1 ~ AC-5）

- **AC-1**：`apps/api/dataplat_api/models/job.py` 含 `JobORM`：id uuid PK / type str / status str（约束值 queued|running|succeeded|failed）/ payload jsonb / result jsonb? / error str? / created_at / started_at? / completed_at?；models/__init__.py export。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.models import JobORM; cols={c.name for c in JobORM.__table__.columns}; need={'id','type','status','payload','result','error','created_at','started_at','completed_at'}; assert need <= cols, cols"`

- **AC-2**：`apps/api/alembic/versions/0003_*.py` 创建 jobs 表。
  - **验证命令**：`ls apps/api/alembic/versions/0003_*.py >/dev/null && grep -q "jobs" apps/api/alembic/versions/0003_*.py`

- **AC-3**：`apps/api/dataplat_api/jobs/redis_client.py`：`get_redis()` 单例 + `get_queue()`；env `DATAPLAT_REDIS_URL`（默认 `redis://localhost:6379/0`）。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.jobs.redis_client import get_redis, get_queue; assert callable(get_redis) and callable(get_queue)"`

- **AC-4**：`apps/api/dataplat_api/jobs/service.py`：`JobsService.enqueue / get_by_id / mark_running / mark_succeeded / mark_failed`。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.jobs.service import JobsService; assert all(hasattr(JobsService, m) for m in ['enqueue','get_by_id','mark_running','mark_succeeded','mark_failed'])"`

- **AC-5**：`apps/api/dataplat_api/jobs/tasks.py`：`run_ingest_job(job_id: str)` 同步函数（RQ 兼容）；内部 `asyncio.run(...)` 跑 async session + AdapterRunner.run + mark_succeeded/failed。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.jobs.tasks import run_ingest_job; import inspect; sig=inspect.signature(run_ingest_job); assert 'job_id' in sig.parameters"`

### 路由 / 行为（AC-6 ~ AC-10）

- **AC-6**：`schemas/job.py`：`JobIngestRequest(owner: str, name: str, request: IngestRequest)` + `JobRead(id, type, status, payload, result, error, created_at, started_at, completed_at)`；全 `extra="forbid"`。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.schemas.job import JobIngestRequest, JobRead; assert JobIngestRequest.model_config.get('extra')=='forbid' and JobRead.model_config.get('extra')=='forbid'"`

- **AC-7**：`routers/jobs.py`：`APIRouter(prefix='/jobs', tags=['jobs'])`；POST `/ingest`（admin + repo visibility 检查）→ 201 + JobRead(status=queued)；GET `/{job_id}`（logged-in；不存在返 404）→ JobRead。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.routers.jobs import router; paths={r.path for r in router.routes}; assert '/jobs/ingest' in paths and '/jobs/{job_id}' in paths"`

- **AC-8**：`main.py` include + OpenAPI 含 `/jobs/ingest` + `/jobs/{job_id}`。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); assert '/jobs/ingest' in s['paths'] and '/jobs/{job_id}' in s['paths']"`

- **AC-9**：Repo visibility 复用 `RepoService.get_by_owner_name`；不重复实现 `_visibility_visible`。
  - **验证命令**（test -f 前置 + 正向 grep + 反向 grep；不吞 stderr）：`test -f apps/api/dataplat_api/routers/jobs.py && test -f apps/api/dataplat_api/jobs/service.py && grep -qE "_resolve_repo|RepoService.get_by_owner_name" apps/api/dataplat_api/routers/jobs.py && ! grep -rE "_visibility_visible" apps/api/dataplat_api/jobs apps/api/dataplat_api/routers/jobs.py`

- **AC-10**：`worker/dataplat_worker/main.py` 含 `main()`：连 Redis + RQ Worker(['default']) + work()；`python -m dataplat_worker` 可启动；测试用 SimpleWorker burst。
  - **验证命令**：`test -f worker/src/dataplat_worker/main.py && grep -qE "Worker|work\(" worker/src/dataplat_worker/main.py`

### 测试 / 质量（AC-11 ~ AC-13）

- **AC-11**：`apps/api/tests/test_jobs.py` ≥ 10 测试（PG + MinIO + Redis 三探针）：
  - (a) admin POST `/jobs/ingest` → 201 status=queued
  - (b) GET 已存在 job → 200 + status
  - (c) GET 不存在 job → 404
  - (d) user POST → 403
  - (e) anon POST → 401
  - (f) 缺 blob 时入队成功 + worker 跑后 status=failed + error 含 missing
  - (g) 端到端：上传 blob → POST → SimpleWorker burst → GET status=succeeded + result.commit_hash 存在
  - (h) 二次 ingest 同 ref → 第二次 commit.parents=[第一次 commit_hash]
  - (i) worker 异常 swallow → job status=failed
  - (j) 幂等：相同 spec 二次 enqueue → 两个 job 各自跑 → 第二次 result.deduplicated=true

- **AC-12**：ruff + mypy 全 PASS（含 worker/src）。
  - **验证命令**：`uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src`

- **AC-13**：`scripts/_self_check.sh rq-worker-skeleton` 13 AC PASS（三探针；任一不可达 SKIP）。

## 风险

1. **RQ 跨进程 session**：worker 跑 task 时 FastAPI session 不可用。**缓解**：tasks.py 在 task 函数内新建独立 async engine + session；async 用 `asyncio.run` 包
2. **RQ SimpleWorker 同进程测试**：fork 在 pytest 内复杂。**缓解**：用 `rq.SimpleWorker` + `work(burst=True)` 不 fork；AC-11 (g)(h)(i)(j) 覆盖
3. **alembic 0003 base 链接**：基于 0002 head（auth-scaffold）。**缓解**：alembic env 检查；AC-2 验证
4. **Redis 无认证 MVP**：`redis://localhost:6379/0`；生产留 `redis-auth-tls-*`
5. **JobORM.payload 反序列化**：plain dict 存（client 自负 schema），worker 反构 IngestRequest Pydantic 校验
6. **跨 AC 一致性（SKILL 7 条 checklist 第三次回归）**：
   - 四链路：本变更不引入新 hash；payload→worker→result 路径直链
   - 事务：worker 独立 session（决策表声明；与 FastAPI session 隔离）
   - AC 验证命令一行式：实测 14
   - 反向 grep + test -f：AC-9 应用模板
   - process_tasks 6 条：tasks v1 列 T-11~T-16
   - parents：沿用 commit-api 接链；spec 无裸 `parents=[]`

## 关键决策

| 决策 | 选项 | 选择 | 理由 |
|---|---|---|---|
| 任务执行模型 | in-process / subprocess L2 | **in-process MVP** | subprocess 推后 |
| Worker sync vs async | sync / asyncio.run async | **asyncio.run** | 与 ORM async 一致 |
| Job 持久化 | RQ 自带 / 自建 jobs 表 | **自建 jobs 表** | 业务字段 + 长期可查 |
| Status 类型 | enum / str + check | **str + 应用层约束** | alembic enum 修改成本高 |
| Job 读权限 | owner / 任何登录 / admin | **任何登录可读** | MVP；ACL 留 follow-up |
| Task 错误 | swallow + mark_failed / raise + RQ retry | **swallow + mark_failed** | MVP 不 retry |
| Worker DB session | 共享 / 独立 | **独立 async engine + session** | 进程边界清晰 |

## 跨 AC 自审 grep（SKILL 7 条 checklist 第三次回归）

```bash
grep -nE "事务前|事务内|事务外" spec.md      # 风险 #1 + 决策表用"独立 session"措辞，无矛盾
grep -nE "parents=\[\]" spec.md             # 0（沿用 adapter-framework parent 接链）
grep -nE "! *grep" spec.md                  # AC-9 1 次，配 test -f + 不吞 stderr
grep -nE "2>/dev/null" spec.md              # 0
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md   # 期望 ≥ 6
grep -cE "test -f|cd apps/api|grep -q|uv run python" spec.md  # 期望 ≥ 12
```

## 流程偏离

无功能性偏离。SKILL 7 条 checklist 第三次正式回归（commit-api-mvp + adapter-framework + web-mvp-pages 反哺后）。
