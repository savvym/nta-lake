---
change_id: repo-files-tab-20260517
version: 1
authored_at: 2026-05-17T16:30:00Z
---

# Tasks

## T-1 schemas/ref.py + services/ref.py

- `apps/api/dataplat_api/schemas/ref.py`：`RefRead(name: str, commit_hash: SHA256)` extra=forbid
- `schemas/__init__.py` export `RefRead`
- `apps/api/dataplat_api/services/ref.py`：`RefService.get_by_name(session, repo_id, name) -> RefORM | None`
- `services/__init__.py` export `RefService`
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-1, AC-2

## T-2 routers/repos.py 加 GET /refs/{ref_name}

- 在 `apps/api/dataplat_api/routers/repos.py` 加 `GET /{owner}/{name}/refs/{ref_name}` 路由
- `Depends(get_optional_user)` + `RepoService.get_by_owner_name(session, owner, name, current_user)` visibility check → None 404
- 调 `RefService.get_by_name(...)` → None 404 / 200 + RefRead
- `make codegen` 同步 openapi.json
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-3, AC-4, AC-5

## T-3 后端集成测试 ≥ 3

- 新建 `apps/api/tests/test_refs.py`：
  - (a) admin POST commit 含 ref="main" → GET refs/main → 200 + commit_hash 一致
  - (b) GET 不存在 ref → 404
  - (c) anon GET private repo refs → 404
- depends_on: T-2 / estimated_stage: stage-3 / AC: AC-10

## T-4 前端 queries.ts 加 useRef

- `apps/web/src/lib/api/queries.ts` 加 `interface RefRead { name: string; commit_hash: string }` + `useRef(owner, name, refName)` hook（queryKey `["ref", owner, name, refName]`）
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-6

## T-5 前端 FilesSection 组件

- 改 `apps/web/src/routes/repos/$owner.$name.tsx`：
  - 加 `FilesSection` 内部组件：
    - `const ref = useRef(owner, name, "main")`
    - `const commit = useCommit(owner, name, ref.data?.commit_hash ?? "")`（hash 空时 useCommit 已 disabled）
    - loading / no-main / empty / list 4 状态
    - 头部：`main · {N} files · commit message · time ago`
    - 表格：path / type / sha256 prefix / 下载链
  - 紧接 metadata Card 后插入
- routeTree.gen.ts：本变更不加新页面，无需改
- depends_on: T-4 / estimated_stage: stage-3 / AC: AC-7, AC-8

## T-6 前端 FilesSection 测试

- 加 `apps/web/src/routes/repos.files-section.test.tsx`（或 inline 到 detail test）：mock useRef 返 main commit_hash + mock useCommit 返 tree 2 entries → 断言 path 显示 + 下载 href 含 `/api/repos/.../blobs/$sha`
- depends_on: T-5 / estimated_stage: stage-3 / AC: AC-9

## T-7 lint + type + build

- ruff + mypy 全 PASS（后端）+ pnpm typecheck + pnpm build（前端）
- depends_on: T-1~T-6 / estimated_stage: stage-3 / AC: AC-11, AC-12

## T-8 self_check repo-files-tab block

- `scripts/_self_check.sh` 追加 `run_repo_files_tab` 13 AC + filter；后端 AC-10 走 PG+MinIO+Redis 探针
- depends_on: T-1~T-7 / estimated_stage: stage-3 / AC: AC-13

## process_tasks

## T-9 stage-2 spec/tasks review（process）

- depends_on: T-1~T-8 v1 完
- estimated_stage: stage-2

## T-10 stage-4 coding review（process；可跳过用 self_check 等价）

- depends_on: T-1~T-7
- estimated_stage: stage-4

## T-11 stage-5/6 test_report + review（process）

- depends_on: T-6
- estimated_stage: stage-6

## T-12 stage-7 CI（process）

- depends_on: T-8, T-11
- estimated_stage: stage-7

## T-13 stage-9 deploy verify（process；后端要重启 API）

- depends_on: T-12
- estimated_stage: stage-9

## T-14 stage-10 close（process）

- depends_on: T-12, T-13
- estimated_stage: stage-10

## 任务依赖图

```
T-1 (schemas+service) → T-2 (router) → T-3 (后端 tests)
T-4 (queries) → T-5 (FilesSection) → T-6 (前端 test)
T-3 + T-6 → T-7 (lint/build) → T-8 (self_check)
T-8 → T-9 → T-10 → T-11 → T-12 → T-13 → T-14
```

## AC 覆盖矩阵

| AC | task |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-1 |
| AC-3 | T-2 |
| AC-4 | T-2 |
| AC-5 | T-2 |
| AC-6 | T-4 |
| AC-7 | T-5 |
| AC-8 | T-5 |
| AC-9 | T-6 |
| AC-10 | T-3 |
| AC-11 | T-7 |
| AC-12 | T-7 |
| AC-13 | T-8 |
