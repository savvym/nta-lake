---
change_id: processor-framework-20260517
version: 1
authored_at: 2026-05-17T18:00:00Z
---

# Tasks

## T-1 packages/core processor.py 协议增 RepoView + ProcessContext blob_store

- `packages/core/src/dataplat_core/protocols/processor.py`：补 `RepoView` Protocol（open(commit_hash, path) -> bytes）+ `ProcessContext` 加 `blob_store`/`repo_view` 字段
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-1, AC-4, AC-9

## T-2 runner 三件套（registry + runner + repo_view）

- `apps/api/dataplat_api/runner/processor_registry.py`：`ProcessorRegistry` + `get_processor_registry()` 单例 + 复用 `AdapterRegistry` 同构
- `apps/api/dataplat_api/runner/processor_runner.py`：`ProcessorRunner.run(processor_id, version, source_ref, target_ref, params, ctx)` async；负责 open source → call processor → CAS write → tree build → commit + update target ref
- `apps/api/dataplat_api/runner/repo_view.py`：`DbRepoView` 实现 RepoView Protocol（read-through DB + BlobStore）
- `runner/runcontext.py`：`StandardRunContext` 加 `blob_store` 字段
- `runner/__init__.py`：export `ProcessorRegistry`, `ProcessorRunner`, `DbRepoView`, `get_processor_registry`
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-1, AC-2, AC-3, AC-9

## T-3 processors 包 + markdown-normalize 实现

- `apps/api/dataplat_api/processors/__init__.py`：import 触发自注册（沿 adapter 模式）
- `apps/api/dataplat_api/processors/markdown_normalize.py`：`MarkdownNormalizeProcessor` 实现 Processor Protocol；规则 CRLF→LF + 行尾 trailing whitespace 去除；id=`markdown-normalize` v=`0.1`
- depends_on: T-2 / estimated_stage: stage-3 / AC: AC-2, AC-4

## T-4 schemas/process.py + routers/process.py

- `apps/api/dataplat_api/schemas/process.py`：`ProcessRequest(repo_id, processor_id, version, source_ref, target_ref, params)` + `ProcessResponse(job_id)` 都 extra=forbid
- `apps/api/dataplat_api/routers/process.py`：`POST /process`（admin only via `Depends(get_current_admin_user)`）→ 调 `JobsService.enqueue(job_type="process", payload=...)` → 返 202 + job_id
- `apps/api/dataplat_api/main.py`：include `process_router`
- depends_on: T-1, T-2 / estimated_stage: stage-3 / AC: AC-5, AC-6

## T-5 jobs/tasks.py 加 run_process_job + service dispatch

- `apps/api/dataplat_api/jobs/tasks.py`：新 `run_process_job(job_id: str)` sync-RQ 入口（asyncio.run + 独立 async engine + ProcessorRunner.run + swallow exception → mark_failed）
- `apps/api/dataplat_api/jobs/service.py`：`enqueue` 按 `job_type` dispatch（"ingest" → run_ingest_job；"process" → run_process_job）
- depends_on: T-2, T-4 / estimated_stage: stage-3 / AC: AC-7, AC-8

## T-6 测试 tests/test_processor.py ≥ 8

- 新建 `apps/api/tests/test_processor.py`（PG + MinIO + Redis）：
  - test_a registry register/get/list
  - test_b markdown-normalize 单元（CRLF + trailing ws）
  - test_c DbRepoView open round-trip
  - test_d admin POST /process → 202 + job 入队
  - test_e user POST /process → 403
  - test_f end-to-end：上传 → ingest → process → target ref 指向新 commit + 内容已 normalize
  - test_g unknown processor → mark_failed
  - test_h source ref missing → mark_failed
- depends_on: T-2~T-5 / estimated_stage: stage-3 / AC: AC-10

## T-7 codegen + lint + type

- `make codegen` 同步 `packages/api-types/openapi.json` + `generated.ts`（包含 /process path）
- `uv run ruff check apps/api packages/core worker/src` 全 PASS
- `uv run mypy apps/api/dataplat_api packages/core/src worker/src` 全 PASS
- depends_on: T-1~T-6 / estimated_stage: stage-3 / AC: AC-11, AC-12

## T-8 self_check processor-framework block

- `scripts/_self_check.sh` 追加 `run_processor_framework` 13 AC + filter + 总入口；AC-10 走 `run_ac_skipif_no_pg_minio_redis` 探针
- depends_on: T-1~T-7 / estimated_stage: stage-3 / AC: AC-13

## process_tasks

## T-9 stage-2 spec/tasks review

- depends_on: T-8 v1 完
- estimated_stage: stage-2

## T-10 stage-4 coding review

- depends_on: T-1~T-7
- estimated_stage: stage-4

## T-11 stage-5/6 test_report + review

- depends_on: T-6
- estimated_stage: stage-6

## T-12 stage-7 CI（本地 self_check 等价跑）

- depends_on: T-8, T-11
- estimated_stage: stage-7

## T-13 stage-9 deploy verify（重启 API + worker）

- depends_on: T-12
- estimated_stage: stage-9

## T-14 stage-10 close

- depends_on: T-12, T-13
- estimated_stage: stage-10

## 任务依赖图

```
T-1 (协议) → T-2 (runner 三件套) → T-3 (markdown-normalize)
T-1, T-2 → T-4 (schema+router) → T-5 (jobs dispatch)
T-2~T-5 → T-6 (8 tests) → T-7 (codegen+lint) → T-8 (self_check)
T-8 → T-9 → T-10 → T-11 → T-12 → T-13 → T-14
```

## AC 覆盖矩阵

| AC | task |
|---|---|
| AC-1 | T-1, T-2 |
| AC-2 | T-2, T-3 |
| AC-3 | T-2 |
| AC-4 | T-1, T-3 |
| AC-5 | T-4 |
| AC-6 | T-4 |
| AC-7 | T-5 |
| AC-8 | T-5 |
| AC-9 | T-1, T-2 |
| AC-10 | T-6 |
| AC-11 | T-7 |
| AC-12 | T-7 |
| AC-13 | T-8 |
