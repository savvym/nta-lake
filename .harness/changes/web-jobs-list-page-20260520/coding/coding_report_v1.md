---
change_id: web-jobs-list-page-20260520
version: 1
authored_at: 2026-05-20T13:50:00Z
branch: change/web-jobs-list-page-20260520
base_commit: 67bba24
head_commit: WIP（未 commit；统一在 stage 7 push）
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| apps/api/dataplat_api/schemas/job.py | edit | 新增 JobListResponse（items/total/limit/offset，extra=forbid） | T-1 |
| apps/api/dataplat_api/jobs/service.py | edit | 新增 JobsService.list_jobs：status/type 过滤 + 分页 + created_at desc 排 | T-2 |
| apps/api/dataplat_api/routers/jobs.py | edit | 新增 GET /jobs (admin only) + status/type 白名单 + 400 校验；路由置于 /{job_id} 前 | T-3 |
| apps/web/src/lib/api/queries.ts | edit | 新增 JobsListResponse interface + useJobs hook（filters → query key） | T-4 |
| apps/web/src/routes/jobs/index.tsx | new | /jobs 列表页：filter 选择器 + 表格 + 分页按钮 + Refresh + 非 admin 提示 | T-5 |
| apps/web/src/routes/jobs/$job_id.tsx | rename+edit | 从 `routes/jobs.$job_id.tsx` 迁入 jobs/ 目录（folder routing 一致；相对 import 适配） | T-5 |
| apps/web/src/routes/jobs/$job_id.test.tsx | rename+edit | 跟随路由文件迁入；mock 路径 ../lib → ../../lib | T-7 |
| apps/web/src/routes/__root.tsx | edit | nav 加 admin 限定 `<Link to="/jobs">` | T-6 |
| apps/web/src/routeTree.gen.ts | regen | TanStack file routing 重新生成（jobs/index + jobs/$job_id） | — |
| apps/api/tests/test_jobs_list.py | new | 5 pytest：admin/user 403/status/分页/400 非白名单 | T-7 |
| apps/web/src/routes/jobs/index.test.tsx | new | 5 vitest：admin/非 admin/status filter/翻页/page size reset | T-7 |
| scripts/_self_check.sh | edit | 新增 run_web_jobs_list_page (10 AC) + dispatcher + full 链；修正 web-write-flows AC-2 路径 | T-9 |
| .harness/changes/web-jobs-list-page-20260520/request_analysis/spec.md | edit | AC-5 与 AC-7 路径升级为 jobs/index.tsx（适配 folder routing 决策） | — |

> **门禁**：本表必须与 `git diff --name-only main...HEAD` 一致；待 stage 7 push 后回填 commit SHA。

## 与 tasks.md 的映射

| Task ID | 状态 | commits | 备注 |
|---|---|---|---|
| T-1 JobListResponse | done | TBD | schemas/job.py |
| T-2 list_jobs | done | TBD | service.py（func.count + filters list） |
| T-3 GET /jobs | done | TBD | router；whitelist 在文件顶定义 |
| T-4 useJobs | done | TBD | queries.ts |
| T-5 jobs/index.tsx | done | TBD | folder routing 决策见下 |
| T-6 nav link | done | TBD | __root.tsx |
| T-7 测试（vitest+pytest） | done | TBD | 5+5 全 PASS |
| T-8 typecheck/ruff/mypy | done | TBD | AC-9 PASS |
| T-9 self_check | done | TBD | AC-10 PASS |
| T-10 stage 4+6 reviewer 合并版 | pending | — | 本报告后立即 spawn |

## 偏离 spec / trade-off

| # | 偏离点 | 原因 | 评审请关注 |
|---|---|---|---|
| D-1 | 路由文件从 `apps/web/src/routes/jobs.tsx` 改为 `apps/web/src/routes/jobs/index.tsx`（同时把已有 `jobs.$job_id.tsx` 迁入 `jobs/` 目录） | TanStack file-based routing：当父名同时承担"自身页"与"子路由"时，flat-dot `jobs.tsx` 不会被 generator 识别为 `/jobs` index（实测 routeTree.gen.ts 不生成 `JobsRoute`，且与 `jobs.$job_id.tsx` 在生成期混合）。consolidate 到 folder 形式后两者都正确生成（`/jobs/` + `/jobs/$job_id`）。改动是局部的、可逆的，spec AC-5 / AC-7 已同步升级 | 决策是否接受 folder routing 形态；`<Link to="/jobs">` 在 TS 层仍兼容（TanStack 把 `/jobs` 视为同义于 `/jobs/`） |
| D-2 | spec AC-5 grep 文本：`createFileRoute("/jobs")` → `createFileRoute("/jobs/")` | TanStack 对 folder/index 路由的固定输出形式（带尾斜杠）；nav `<Link>` 不受影响 | — |
| D-3 | self_check AC-8 加 `export DATAPLAT_COOKIE_SECURE=false` | httpx ASGI 走 `http://test`，若 cookie `Secure` 标记被强加（默认 true）登录后 set-cookie 不会被 httpx 回传 → 后续 admin 端点 401。沿用 AC-13/processor-pdf-mineru-live-fix 既有模式 | — |
| D-4 | 顺手修正 `web-write-flows-20260517 AC-2` 的 grep 路径（`jobs.$job_id.tsx` → `jobs/$job_id.tsx`） | 文件已随 D-1 迁入 `jobs/` 子目录；不修会让 stage 8 full self_check 失败 | 是否接受跨 change 的 self_check 修正（小，单行）|

## 本地校验结果

```text
bash scripts/_self_check.sh web-jobs-list-page           → 10 PASS / 0 FAIL
pnpm --filter web typecheck                              → 0 errors
pnpm --filter web test (vitest 全量 16 files / 46 tests) → 全 PASS
uv run pytest tests/test_jobs_list.py                    → 5 PASS
uv run ruff check apps/api/dataplat_api                  → 0 errors
bash scripts/_self_check.sh full                         → PASS 340 / FAIL 5（均为 pre-existing：
  AC-11 ingest / AC-11 jobs / AC-10 processor / AC-10 llm / AC-10 firecrawl
  — 跟 AC-13 标记的 3 个 pdf-mineru flake 同源，不在本 change 范围内）
```

## 已知未解决问题

- pre-existing：`tests/test_processor.py / test_llm.py / test_firecrawl.py / test_ingest.py / test_jobs.py`
  在某些环境下需要等 redis/minio 副作用清理；本 change 不触碰。
- 列表无 live poll，5 秒级更新依赖手动 Refresh 按钮（spec 范围外，follow-up `web-jobs-list-live-poll-*`）。

## 下一步

进入阶段 4 编码评审 + 阶段 6 单测评审（合并 spawn 一个 sonnet reviewer）。
