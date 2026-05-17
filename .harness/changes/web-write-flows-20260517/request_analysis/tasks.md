---
change_id: web-write-flows-20260517
version: 1
authored_at: 2026-05-17T15:30:00Z
---

# Tasks

## T-1 queries.ts 扩 7 hook

- `useCreateRepo` / `useUpdateRepo(owner, name)` / `useDeleteRepo(owner, name)` / `useUploadBlob(owner, name)` / `useEnqueueIngest` / `useJob(job_id)`（含 refetchInterval 1s + 成功/失败时 false）/ `useCommit(owner, name, hash)`
- 写操作（Create / Update / Delete）成功后 `queryClient.invalidateQueries(["repos"])` + 对应 `["repo", o, n]`
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-5, AC-6, AC-7

## T-2 textarea 组件

- 新建 `apps/web/src/components/ui/textarea.tsx`（shadcn 风格）
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-8

## T-3 /repos/new 页

- 新建 `apps/web/src/routes/repos.new.tsx`：rhf + zod schema（owner / name / layer select / subtype select / visibility select / description optional）→ useCreateRepo.mutate → navigate `/repos/$owner/$name`
- depends_on: T-1, T-2 / estimated_stage: stage-3 / AC: AC-1

## T-4 改造 /repos/$owner/$name

- 加 useMe（已有）+ admin 条件 render：
  - `+ Edit` 按钮 toggle inline 表单：visibility select + description textarea + Save / Cancel → useUpdateRepo.mutate
  - `Delete` 按钮 → `window.confirm` → useDeleteRepo.mutate → navigate `/repos`
  - **Ingest section**（admin only）：`<input type="file" multiple>` + 表单（每个文件一行 path mapping 默认 `content/<filename>`）+ author input + ref input（默认 main）+ Submit → 串行 useUploadBlob 拿 sha256 → useEnqueueIngest.mutate → navigate `/jobs/$job_id`
- 非 admin：仍只显 metadata（与现状一致）
- depends_on: T-1, T-2 / estimated_stage: stage-3 / AC: AC-4, AC-10

## T-5 /jobs/$job_id 页

- 新建 `apps/web/src/routes/jobs.$job_id.tsx`：useJob(id, { refetchInterval: status in [queued, running] ? 1000 : false }) → 状态卡片显 status / created_at / started_at / completed_at / result.commit_hash 链 / error
- succeeded 时自动停轮询 + 显 link to commit 详情
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-2

## T-6 /commits/$owner/$name/$hash 页

- 新建 `apps/web/src/routes/commits.$owner.$name.$hash.tsx`：useCommit → 显 metadata + tree entries + 每条 `<a href="/api/repos/$owner/$name/blobs/$sha">下载</a>`
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-3

## T-7 /repos 列表加 New 按钮

- 改 `apps/web/src/routes/repos/index.tsx`：useMe + admin 时顶部加 `+ New Repository` Link to `/repos/new`
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-9

## T-8 vitest 测试 ≥ 3 新

- `apps/web/src/routes/repos.new.test.tsx`：渲染 + 空表单提交 → 必填错
- `apps/web/src/routes/jobs.$job_id.test.tsx`：mock useJob queued → 显排队中；succeeded → 显 commit_hash 链
- `apps/web/src/routes/commits.$owner.$name.$hash.test.tsx`：mock useCommit → tree entries 链显示
- depends_on: T-3, T-5, T-6 / estimated_stage: stage-3 / AC: AC-11

## T-9 build + typecheck

- pnpm typecheck → pnpm build → dist/index.html 生成 + grep `/repos/new`、`/jobs/$job_id`、`/commits/$owner/$name/$hash` in routeTree.gen.ts 真生成
- depends_on: T-1~T-8 / estimated_stage: stage-3 / AC: AC-12

## T-10 self_check web-write-flows block

- `scripts/_self_check.sh` 追加 `run_web_write_flows` 13 AC + filter
- depends_on: T-1~T-9 / estimated_stage: stage-3 / AC: AC-13

## process_tasks（T-11~T-16）

## T-11 stage-2 spec/tasks review（process）

- depends_on: T-1~T-10 v1 完
- estimated_stage: stage-2

## T-12 stage-4 coding review（process）

- depends_on: T-1~T-10
- estimated_stage: stage-4

## T-13 stage-5/6 test_report + review（process）

- depends_on: T-8
- estimated_stage: stage-6

## T-14 stage-7 CI 验证（process）

- depends_on: T-10, T-13
- estimated_stage: stage-7

## T-15 stage-9 deploy verify（process，skipped 仅前端静态）

- depends_on: T-14
- estimated_stage: stage-9

## T-16 stage-10 close（process）

- depends_on: T-14, T-15
- estimated_stage: stage-10

## 任务依赖图

```
T-1 (queries) ─┬─ T-3 (new repo) ──┐
T-2 (textarea) ┤   T-4 (edit/delete/ingest on detail) ──┐
               ├─ T-5 (job status) ─┤
               └─ T-6 (commit detail) ─┘                  ├─ T-8 (tests) ─ T-9 (build) ─ T-10 (self_check)
                                       T-7 (repos list New btn) ┘

T-10 → T-11 → T-12 → T-13 → T-14 → T-15 → T-16
```

## AC 覆盖矩阵

| AC | task |
|---|---|
| AC-1 | T-3 |
| AC-2 | T-5 |
| AC-3 | T-6 |
| AC-4 | T-4 |
| AC-5 | T-1 |
| AC-6 | T-1 |
| AC-7 | T-1 |
| AC-8 | T-2 |
| AC-9 | T-7 |
| AC-10 | T-4 |
| AC-11 | T-8 |
| AC-12 | T-9 |
| AC-13 | T-10 |
