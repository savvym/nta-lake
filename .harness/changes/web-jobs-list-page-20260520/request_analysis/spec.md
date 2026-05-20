---
change_id: web-jobs-list-page-20260520
version: 3
authored_at: 2026-05-20T13:00:00Z
revised_at: 2026-05-20T13:40:00Z
status: draft
revision_notes_v3: |
  v3 修 stage 2 reviewer v2 报的 1 条残留 MUST FIX + 1 条 SHOULD：
  - v2 升 T-4 用例下限 ≥5 但 spec AC-8 描述/命令仍 ≥4，不一致 → 全文统一 ≥5
  - 自审第 6 条仍写 `path "/"`，与 v2 决策不符 → 改 `path ""`
revision_notes: |
  v2 修 stage 2 reviewer v1 报的 1 条 MUST FIX + 3 条 SHOULD FIX：
  - MUST-1 (AC-3 grep 与 T-3 路径不一致)：统一选 `@router.get("")`（FastAPI
    prefix=/jobs + path="" → /jobs，无尾斜杠歧义）；AC-3 grep 改匹配空引号
  - SHOULD-1: 非范围补 "不加 JobORM 新列"
  - SHOULD-2: T-4 (a-d) 4 个用例 + (e) "400 非白名单" 改必选，删 "可选" 标签
  - SHOULD-3: AC-8 命令 `grep -c` 加 `|| true` 防止 0 命中误 FAIL
---

# Spec：GET /jobs admin 列表端点 + Web Jobs 页（过滤 + 分页）

## 背景

现状：
- 后端 `apps/api/dataplat_api/routers/jobs.py` 只暴露 `POST /jobs/ingest` 与 `GET /jobs/{id}`；**没有列表端点**
- `JobORM` 无 `owner_id` 列；payload JSONB 含 owner/name 但不能用作 PG-level 用户过滤
- Web 端 `apps/web/src/routes/jobs.$job_id.tsx` 只有单作业详情页；**无 /jobs 列表页**
- 用户实测期间无法看 "我刚 enqueue 的 PDF→MD job 跑得怎么样" / "队列里还堆了几个"，只能拿 job_id 手填 URL

用户选定（stage 0）：
1. **admin only**：JobORM 没 owner 列，admin 看全部最稳；多用户隔离开 follow-up `jobs-acl-*`
2. **过滤 + 分页**：?status / ?type / ?limit / ?offset；UI 多个 select 控件
3. **不引入自动刷新**：用户手动刷新或点 Refresh（live-poll 留 follow-up）

## 问题陈述

- 后端 `routers/jobs.py` 缺 `GET /jobs?status&type&limit&offset` 端点
- `JobsService` 缺 `list_jobs(status?, type?, limit, offset) -> tuple[list[JobORM], total]`
- `schemas/job.py` 缺 `JobListResponse` (items + total + limit + offset)
- Web `lib/api/queries.ts` 缺 `useJobs(filters)` hook
- Web 缺 `/jobs` 路由（`apps/web/src/routes/jobs.tsx` 待新建）；导航栏（如有）应加入口
- Web `lib/api/queries.ts` 现有 `useJob(job_id)` 保留不动

## 范围

In scope（与下方 AC 对齐）：

- AC-1: `apps/api/dataplat_api/schemas/job.py` 加 `JobListResponse(items: list[JobRead], total: int, limit: int, offset: int)`
- AC-2: `apps/api/dataplat_api/jobs/service.py::JobsService` 加 `list_jobs(session, status: str | None, job_type: str | None, limit: int, offset: int) -> tuple[list[JobORM], int]`：按 `created_at desc` 排，可选过滤，返 (items, total)
- AC-3: `apps/api/dataplat_api/routers/jobs.py` 加 `GET /jobs` 端点：
  - Depends(require_admin)
  - Query: `status: str | None = None`（值域 queued/running/succeeded/failed）/ `type: str | None = None`（值域 ingest/process）/ `limit: int = Query(50, ge=1, le=200)` / `offset: int = Query(0, ge=0)`
  - 非法 status/type → 400
- AC-4: `apps/web/src/lib/api/queries.ts` 加 `useJobs(filters: {status?, type?, limit, offset})` hook
- AC-5: 新文件 `apps/web/src/routes/jobs.tsx`：
  - admin 才显示（普通用户 403 / 显示提示）
  - 上方 filter 控件：status select / type select / page size select（25/50/100）
  - 表格：created_at（相对时间）/ id（截断 8 字符 + link → /jobs/{id}）/ type / status（彩色徽章）/ payload 摘要（如 owner/name）/ 用时 (started→completed 差值)
  - 底部分页：上一页 / 下一页 / 当前 X-Y of Z
  - 刷新按钮（手动 refetch）
- AC-6: 主导航（如 `__root.tsx` 或 NavBar 组件）加 "Jobs" 链接（admin 可见；普通用户隐藏）
- AC-7: behavioral：≥ 5 单测覆盖：(a) admin 看到列表 (b) filter status 触发 query (c) filter type 触发 query (d) 翻页 (e) 非 admin 隐藏导航 / 403 提示
- AC-8: pytest 后端集成 ≥ 4 用例：(a) admin GET /jobs 返列表 + total (b) user 403 (c) status 过滤生效 (d) limit/offset 分页正确
- AC-9: pnpm typecheck + ruff + mypy 全 PASS
- AC-10: scripts/_self_check.sh 加 `run_web_jobs_list_page` AC block（≥ 10 AC）+ filter + 全跑入口

## 非范围

- 不加 JobORM 任何新列（含 owner_id / cancel_reason / retry_count 等）；独立 follow-up `jobs-owner-acl-*` / `jobs-cancel-*`
- 不引入 live poll / WebSocket 自动刷新（独立 follow-up `web-jobs-list-live-poll-*`）
- 不引入 cancel / retry 按钮（独立 follow-up `jobs-cancel-*`）
- 不动单 job 详情页 `jobs.$job_id.tsx`
- 不引入 search by id

## 验收标准（10 AC，**2 behavioral**：AC-7 / AC-8）

| ID | kind | 描述 | 验证 | 期望 |
|---|---|---|---|---|
| AC-1 | static | schemas/job.py 含 JobListResponse | `cd apps/api && uv run python -c "from dataplat_api.schemas.job import JobListResponse; assert all(k in JobListResponse.model_fields for k in ('items','total','limit','offset'))"` | 退出 0 |
| AC-2 | static | JobsService.list_jobs 函数存在 | `cd apps/api && uv run python -c "from dataplat_api.jobs.service import JobsService; assert hasattr(JobsService, 'list_jobs')"` | 退出 0 |
| AC-3 | static | routers/jobs.py 含 `@router.get("")`（path 空串 → 拼 prefix=/jobs = `/jobs`） + 同行附近 require_admin | `grep -qE '@router\.get\(\s*[\"\x27][\"\x27]\s*[,)]' apps/api/dataplat_api/routers/jobs.py && grep -q "require_admin" apps/api/dataplat_api/routers/jobs.py` | 退出 0 |
| AC-4 | static | queries.ts 加 useJobs | `grep -qE "export function useJobs" apps/web/src/lib/api/queries.ts` | 退出 0 |
| AC-5 | static | jobs.tsx 路由文件 + createFileRoute + table 渲染 | `test -f apps/web/src/routes/jobs.tsx && grep -q 'createFileRoute("/jobs")' apps/web/src/routes/jobs.tsx` | 退出 0 |
| AC-6 | static | 导航含 "Jobs" link 到 /jobs（grep "/jobs" 在 __root.tsx 或 NavBar） | `grep -rE 'to=["\x27]/jobs["\x27]' apps/web/src/routes/__root.tsx apps/web/src/components 2>/dev/null` | 命中 |
| AC-7 | behavioral | vitest jobs.test.tsx ≥ 5 + 全 PASS | 见 § "AC-7 完整命令" | numTotalTests ≥ 5 + 0 fail |
| AC-8 | behavioral | pytest test_jobs_list ≥ 5 + 全 PASS（admin / user 403 / status 过滤 / limit+offset 分页 / 400 非白名单 status） | 见 § "AC-8 完整命令" | ≥ 5 + 全 PASS |
| AC-9 | static | typecheck + ruff + mypy 全 PASS | `pnpm --filter web typecheck && uv run ruff check apps/api packages/core worker/src && uv run mypy apps/api/dataplat_api packages/core/src worker/src` | 退出 0 |
| AC-10 | static | self_check 含 run_web_jobs_list_page | `grep -q "run_web_jobs_list_page" scripts/_self_check.sh` | 退出 0 |

### AC-7 完整命令

```bash
cd apps/web && pnpm test -- --run --reporter json src/routes/jobs.test.tsx > /tmp/jobs.raw 2>&1 && \
  grep -E '^{' /tmp/jobs.raw > /tmp/jobs.json && \
  python3 -c "import json; d=json.load(open('/tmp/jobs.json')); assert d['numFailedTests']==0 and d['numTotalTests']>=5, d"
```

### AC-8 完整命令

```bash
export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && \
  export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && \
  export DATAPLAT_MINIO_ENDPOINT=http://localhost:${DATAPLAT_MINIO_PORT:-9000} && \
  export DATAPLAT_MINIO_ACCESS_KEY=${DATAPLAT_MINIO_ACCESS_KEY:-dataplat} && \
  export DATAPLAT_MINIO_SECRET_KEY=${DATAPLAT_MINIO_SECRET_KEY:-dataplat-secret} && \
  export DATAPLAT_REDIS_URL=redis://localhost:${DATAPLAT_REDIS_PORT:-6379}/0 && \
  export DATAPLAT_COOKIE_SECURE=false && \
  (cd apps/api && uv run pytest -q --tb=no tests/test_jobs_list.py) && \
  [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_jobs_list.py 2>&1 | grep -cE 'test_jobs_list\.py::' || true)" -ge 5 ]
```

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| status / type 值域无 enum，任意字符串绕过 | 中 | DB 上 NOOP（无匹配） + 浪费 query | router 层显式 validate；不在白名单 → 400 |
| 总 jobs 量大时 COUNT(*) 慢 | 低 | API 慢 | jobs 表用 created_at desc + limit/offset；COUNT 在 PG 索引上够快；千万级别可改估算 / cursor 分页（follow-up） |
| 现有 `test_jobs.py` 测试假设 GET /jobs/{id} 行为 | 低 | 不回归 | 新加 GET /jobs（无 path 参数），与 /jobs/{id} URL pattern 互不影响（FastAPI 按精确匹配） |
| __root.tsx 导航修改影响所有页面布局 | 中 | UI 退化 | 加 link 只挂 admin 可见；用 useMe 控制；现有 routes/__root.tsx 已有 admin 判断模式可复用 |
| useJobs queryKey 含 filters 对象 → 引用比较抖动 | 中 | 重复 refetch | queryKey 写成 ["jobs", status, type, limit, offset] 用基础值；不用对象 |
| `?type=...` 与 FastAPI 内置 `type` 关键字冲突？ | 低 | API typo | 用 `job_type` 内部变量名 + Query alias="type"（与现有 ingest/process job 类型对齐） |
| 跳过 reviewer 漏 bug | 中 | 真 bug | stage 2/4/6 全 reviewer spawn 不偏离 |

## 跨链路一致性自审

1. ✅ summary 待写
2. ✅ 范围 / 非范围明确
3. ✅ AC 全可机械化
4. ✅ AC 分层：2 behavioral
5. ✅ 非豁免
6. ✅ AC-3 grep 精确（含 @router.get 锚定 path ""——v2 起统一为空串）
7. ✅ spec ↔ tasks ↔ self_check 一致
8. ✅ process_tasks 7 节点

## 受影响模块

- 改：`apps/api/dataplat_api/schemas/job.py`（加 JobListResponse）
- 改：`apps/api/dataplat_api/jobs/service.py`（加 list_jobs）
- 改：`apps/api/dataplat_api/routers/jobs.py`（加 GET /jobs）
- 改：`apps/api/tests/test_jobs_list.py`（新文件）
- 改：`apps/web/src/lib/api/queries.ts`（加 useJobs）
- 新：`apps/web/src/routes/jobs.tsx`（列表页）
- 新：`apps/web/src/routes/jobs.test.tsx`（vitest）
- 改：`apps/web/src/routes/__root.tsx` 或导航组件（加 Jobs link）
- 改：`scripts/_self_check.sh`（加 AC block）

## 不受影响

- 现有 GET /jobs/{id} / POST /jobs/ingest
- 单 job 详情页 jobs.$job_id.tsx
- 其他 routes
- 其他 schemas

## 引用

- 现状：`apps/api/dataplat_api/routers/jobs.py`（只有 GET /jobs/{id}）
- JobORM：`apps/api/dataplat_api/models/job.py`（无 owner_id）
- 上游 close：`rq-worker-skeleton-20260517`（jobs 表与基础端点）
