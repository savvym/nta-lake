---
change_id: web-jobs-list-page-20260520
version: 1
authored_at: 2026-05-20T13:50:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC ID | 测试文件 | 测试函数 / 命令 |
|---|---|---|
| AC-1 JobListResponse | apps/api/tests/test_jobs_list.py | 所有 5 用例隐式：response body 必须含 items/total/limit/offset |
| AC-2 list_jobs 服务方法 | apps/api/tests/test_jobs_list.py | test_pagination_preserves_desc_order + test_status_filter_narrows_results |
| AC-3 GET /jobs admin | apps/api/tests/test_jobs_list.py | test_admin_list_returns_items_and_total + test_user_list_returns_403 |
| AC-4 useJobs hook | apps/web/src/routes/jobs/index.test.tsx | 所有 5 用例隐式：mock useJobs 验证 filters 传参 |
| AC-5 /jobs 路由文件 | apps/web/src/routes/jobs/index.test.tsx | "admin sees jobs table with status badges" |
| AC-6 nav Jobs link | (静态 grep) | scripts/_self_check.sh AC-6 |
| AC-7 vitest ≥ 5 | apps/web/src/routes/jobs/index.test.tsx | 5 用例：admin/非 admin/status 过滤/翻页/page size reset |
| AC-8 pytest ≥ 5 | apps/api/tests/test_jobs_list.py | 5 用例：admin/user 403/status/分页/400 |
| AC-9 typecheck/ruff/mypy | (静态) | self_check AC-9 |
| AC-10 self_check 自递归 | (静态) | self_check AC-10 |

## 测试文件清单

### apps/api/tests/test_jobs_list.py（5 测试，全 PASS）

| # | 函数 | 断言 | 用什么数据 |
|---|---|---|---|
| 1 | test_admin_list_returns_items_and_total | 200 + body.items ≥ 4 marker 行 + total ≥ 4 + created_at desc 顺序 | `_seed_jobs(marker)` 注入 4 行 JobORM（含 marker 隔离） |
| 2 | test_user_list_returns_403 | 普通 user 登录后 GET /jobs → 403 | normal_user 夹具 |
| 3 | test_status_filter_narrows_results | ?status=queued 过滤后 marker 行只剩 1 | seed 4 行（status 各异） |
| 4 | test_pagination_preserves_desc_order | items[1].id == seed 顺序的第 2 个 id | 同上 |
| 5 | test_invalid_status_returns_400 | ?status=bogus → 400 + 含"非白名单" | (无 seed) |

清理：每用例独占一个 UUID-marker，结束时 `DELETE FROM jobs WHERE payload->>'_marker' = :m`。

### apps/web/src/routes/jobs/index.test.tsx（5 测试，全 PASS）

| # | 用例 | mock 策略 |
|---|---|---|
| 1 | admin sees jobs table with status badges | currentMe=admin；预置 2 行 mockJobs；断言 id slice + status badge 出现 |
| 2 | non-admin sees 403-equivalent message | currentMe=user；断言"仅 admin 可见"出现 |
| 3 | status filter narrows visible rows and updates useJobs args | renderAt /jobs?status=running；只剩 running 行；lastFilters.status === "running" |
| 4 | pagination next/prev affects useJobs offset | limit=1；点"下一页" offset=1；点"上一页" offset=0 |
| 5 | changing page size resets offset to 0 | offset=5 → 切 page size → offset 回到 0；limit=新值 |

## 测试结果

```text
pnpm exec vitest run src/routes/jobs/index.test.tsx
   Test Files  1 passed (1)
        Tests  5 passed (5)

uv run pytest tests/test_jobs_list.py
   ============================== 5 passed in 2.24s ==============================

pnpm test (全 web)
   Test Files  16 passed (16)
        Tests  46 passed (46)
```

## 与上游 / 兄弟 change 的回归

- jobs/$job_id.test.tsx 跟随主文件迁入 `routes/jobs/` 后 mock 路径已修；2/2 通过。
- 全 web vitest 16/16 通过，无回归。
- pytest 整库 5 个 pre-existing flake（AC-13 既已标注，非本 change 引入）。

## 下一步

进入阶段 6 单测评审 + 阶段 4 编码评审：合并 spawn 一个 sonnet reviewer，写两份 review（code_review_v1.md + test_review_v1.md）。
