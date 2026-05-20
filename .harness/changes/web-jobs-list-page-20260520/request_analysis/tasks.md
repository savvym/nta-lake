---
change_id: web-jobs-list-page-20260520
version: 1
authored_at: 2026-05-20T13:00:00Z
---

# Tasks

```yaml
tasks:
  - id: T-1
    title: schemas/job.py 加 JobListResponse
    description: |
      apps/api/dataplat_api/schemas/job.py。
      class JobListResponse(BaseModel, extra="forbid"):
        items: list[JobRead]
        total: int
        limit: int
        offset: int
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending

  - id: T-2
    title: JobsService.list_jobs
    description: |
      apps/api/dataplat_api/jobs/service.py。
      list_jobs(session, status, job_type, limit, offset) -> tuple[items, total]：
      按 created_at desc 排，可选 status/type 过滤，count + limit/offset 分页。
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-2]
    status: pending

  - id: T-3
    title: routers/jobs.py 加 GET /jobs
    description: |
      apps/api/dataplat_api/routers/jobs.py。
      @router.get("") response_model=JobListResponse；
      Query: status / job_type(alias="type") / limit ge=1 le=200 / offset ge=0；
      白名单 status={queued,running,succeeded,failed} / type={ingest,process}；
      非白名单 → 400；Depends(require_admin)。
    depends_on: [T-2]
    estimated_stage: coding
    covers_ac: [AC-3]
    status: pending

  - id: T-4
    title: pytest test_jobs_list.py ≥ 4 用例
    description: |
      apps/api/tests/test_jobs_list.py（沿 test_jobs.py 模式）。
      用例：admin list / user 403 / status 过滤 / limit+offset 分页 /（可选）400 / type 过滤。
    depends_on: [T-3]
    estimated_stage: unit_test
    covers_ac: [AC-8]
    status: pending

  - id: T-5
    title: queries.ts 加 useJobs hook
    description: |
      apps/web/src/lib/api/queries.ts。
      接口 JobsListResponse { items, total, limit, offset }；
      useJobs(filters: { status?, type?, limit, offset }) queryKey=["jobs", status, type, limit, offset]。
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-4]
    status: pending

  - id: T-6
    title: jobs.tsx 路由 + UI
    description: |
      apps/web/src/routes/jobs.tsx 新建。
      validateSearch: status/type/limit/offset zod 默认。
      非 admin 隐藏 + 提示；admin 显 filter select 控件 + 表格 + 分页 + 刷新按钮。
    depends_on: [T-5]
    estimated_stage: coding
    covers_ac: [AC-5]
    status: pending

  - id: T-7
    title: __root.tsx 导航加 Jobs link
    description: |
      apps/web/src/routes/__root.tsx 或 NavBar。
      admin-only 导航区加 <Link to="/jobs">Jobs</Link>。
    depends_on: [T-6]
    estimated_stage: coding
    covers_ac: [AC-6]
    status: pending

  - id: T-8
    title: jobs.test.tsx ≥ 5 用例
    description: |
      apps/web/src/routes/jobs.test.tsx。
      mock useMe + useJobs；用例：admin 表渲染 / filter status / filter type / 翻页 / 非 admin 隐藏。
    depends_on: [T-6]
    estimated_stage: unit_test
    covers_ac: [AC-7]
    status: pending

  - id: T-9
    title: scripts/_self_check.sh 加 run_web_jobs_list_page 10 AC
    description: |
      在 run_web_blob_md_image_resolver 后插入；filter case + 全跑入口 list 都加上。
    depends_on: [T-4, T-7, T-8]
    estimated_stage: coding
    covers_ac: [AC-10]
    status: pending

  - id: T-10
    title: 本地 typecheck/lint/pytest/vitest/self_check 全绿
    description: |
      pnpm --filter web typecheck
      uv run ruff check apps/api packages/core worker/src
      uv run mypy apps/api/dataplat_api packages/core/src worker/src
      pnpm --filter web test -- --run
      cd apps/api && uv run pytest -q tests/test_jobs_list.py
      bash scripts/_self_check.sh current web-jobs-list-page-20260520
    depends_on: [T-9]
    estimated_stage: ci_result
    covers_ac: [AC-9]
    status: pending
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: pending
  - id: P-code-review
    estimated_stage: coding_review
    status: pending
  - id: P-test-review
    estimated_stage: unit_test_review
    status: pending
  - id: P-push
    estimated_stage: stage-7
    status: pending
  - id: P-ci
    estimated_stage: ci_result
    status: pending
  - id: P-deploy
    estimated_stage: deployment
    status: pending
  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG

T-1 → T-2 → T-3 → T-4
T-1 → T-5 → T-6 → T-7
T-6 → T-8
{T-4, T-7, T-8} → T-9 → T-10
（无环；T-5 与 T-2/T-3/T-4 后端链可并行）

## 验收覆盖

| AC | 任务 |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3 | T-3 |
| AC-4 | T-5 |
| AC-5 | T-6 |
| AC-6 | T-7 |
| AC-7 | T-8 |
| AC-8 | T-4 |
| AC-9 | T-10 |
| AC-10 | T-9 |
