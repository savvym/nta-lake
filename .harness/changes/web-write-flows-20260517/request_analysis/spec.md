---
change_id: web-write-flows-20260517
version: 1
authored_at: 2026-05-17T15:30:00Z
status: draft
---

# Spec：Web 写流程 UI（建 repo / Edit / Delete / Ingest / Job / Commit 详情）

## 背景

10 个变更后后端能力齐：auth + repo CRUD + commit/blob/tree + ingest + jobs queue。Web UI 仅 3 页全只读。本变更扩 UI 覆盖 admin 写流程，让人能在浏览器跑完整 ingest 端到端：建 repo → 上传文件 → 触发 ingest → 看 job 状态 → 看 commit + 下载 blob。

## 问题陈述

- 后端 9 写/读路由零 UI；所有写操作必须 curl
- Admin 在 UI 里建不了 repo / 改不了 visibility / 删不了

## 范围

In scope（**不加新后端路由**）：

- 新页面：
  - `/repos/new`（admin）：表单 → POST /api/repos → navigate 详情
  - `/jobs/$job_id`（logged-in）：状态卡片 + 1s 轮询 + 成功后 link 到 commit 详情
  - `/commits/$owner/$name/$hash`：commit metadata + tree entries + 每条 blob 下载链
- 改造 `/repos/$owner/$name`（详情）：admin 显 Edit / Delete / Ingest section（多文件上传 + 路径映射 + author + ref → 串行 POST blobs + POST /jobs/ingest → navigate /jobs/$id）
- 列表 `/repos` 加 admin-only `+ New Repository` 按钮
- queries.ts 扩 7 个 hook：useCreateRepo / useUpdateRepo / useDeleteRepo / useUploadBlob / useEnqueueIngest / useJob（refetchInterval 1s）/ useCommit
- shadcn 加 `textarea`；layer / subtype / visibility 用原生 `<select>`
- vitest 新增 ≥ 3；self_check 13 AC

Out of scope（follow-up）：

- LIST commits / LIST jobs（需先加后端）：`commits-list-api-*` / `jobs-list-api-*`
- Lineage viz / 多 ref 选择 / 用户管理 / 搜索 / 响应式 / Storybook / E2E

## 验收标准（13 AC + 验证方式）

- **AC-1**：`apps/web/src/routes/repos.new.tsx` 含 rhf + POST /api/repos + navigate。
  - 验证：`test -f apps/web/src/routes/repos.new.tsx && grep -q "react-hook-form" apps/web/src/routes/repos.new.tsx && grep -q "/repos" apps/web/src/routes/repos.new.tsx`

- **AC-2**：`apps/web/src/routes/jobs.\$job_id.tsx` 含 refetchInterval。
  - 验证：`test -f 'apps/web/src/routes/jobs.$job_id.tsx' && grep -q "refetchInterval" 'apps/web/src/routes/jobs.$job_id.tsx'`

- **AC-3**：`apps/web/src/routes/commits.\$owner.\$name.\$hash.tsx` 显示 tree + blob 下载链。
  - 验证：`test -f 'apps/web/src/routes/commits.$owner.$name.$hash.tsx' && grep -q "blobs" 'apps/web/src/routes/commits.$owner.$name.$hash.tsx'`

- **AC-4**：`apps/web/src/routes/repos.\$owner.\$name.tsx` 改造含 PATCH/DELETE/ingest（admin only）。
  - 验证：`grep -qE "PATCH|DELETE" 'apps/web/src/routes/repos.$owner.$name.tsx' && grep -q "/jobs/ingest" 'apps/web/src/routes/repos.$owner.$name.tsx'`

- **AC-5**：queries.ts 新增 7 个 hook。
  - 验证：`[ "$(grep -cE 'export function (useCreateRepo|useUpdateRepo|useDeleteRepo|useUploadBlob|useEnqueueIngest|useJob|useCommit)' apps/web/src/lib/api/queries.ts)" -ge 7 ]`

- **AC-6**：useUploadBlob 用 fetch + body=Blob/File；可见 octet-stream 处理（或借 fetchJson 内部）。
  - 验证：`grep -q "useUploadBlob" apps/web/src/lib/api/queries.ts && grep -qE "Blob|File|octet" apps/web/src/lib/api/queries.ts`

- **AC-7**：变更操作成功后 invalidateQueries。
  - 验证：`[ "$(grep -c "invalidateQueries" apps/web/src/lib/api/queries.ts)" -ge 3 ]`

- **AC-8**：textarea 组件存在。
  - 验证：`test -f apps/web/src/components/ui/textarea.tsx && grep -q "Textarea" apps/web/src/components/ui/textarea.tsx`

- **AC-9**：`/repos` 列表 admin-only "New Repository" 按钮 + 链 `/repos/new`。
  - 验证：`grep -qE "New Repository|新建" apps/web/src/routes/repos/index.tsx && grep -q "/repos/new" apps/web/src/routes/repos/index.tsx`

- **AC-10**：详情页 admin 判断逻辑（grep `me\?\.role|isAdmin|role.*admin`）+ Edit/Delete/Ingest 三 section。
  - 验证：`grep -qE "Edit|Delete|Ingest" 'apps/web/src/routes/repos.$owner.$name.tsx' && grep -qE "role|admin" 'apps/web/src/routes/repos.$owner.$name.tsx'`

- **AC-11**：vitest 测试 ≥ 7（既有 4 + 新 ≥ 3：new repo / job status / commit detail）。
  - 验证：`[ "$(find apps/web/src -name '*.test.tsx' -o -name '*.test.ts' | wc -l)" -ge 7 ] && cd apps/web && pnpm test 2>&1 | tail -5 | grep -qE "passed"`

- **AC-12**：typecheck + build + dist/index.html。
  - 验证：`cd apps/web && pnpm typecheck && pnpm build && test -f dist/index.html`

- **AC-13**：`scripts/_self_check.sh web-write-flows` 13 AC PASS。

## 风险

1. **TanStack Router 文件命名歧义**：`repos.new.tsx` vs `repos/index.tsx + repos/$owner.$name.tsx` 共存——v1 flat naming + directory mixing 须验证 routeTree.gen 真生成正确。**缓解**：build 后 grep `/repos/new` in routeTree.gen.ts；若错回退到 `routes/repos/new.tsx` directory style
2. **多文件上传顺序**：串行 await + 任一失败 throw + UI 显错
3. **轮询 stop**：TanStack Query 随组件卸载自动停；成功/失败时 setRefetchInterval=false
4. **3-param URL**：commits.$owner.$name.$hash.tsx flat naming 应能正确生成 routeTree（SKILL 8 条 checklist 第 6 条 dry-parse 借鉴—build 后实证）
5. **invalidateQueries key 一致性**：固化 `["repos"]` / `["repo", owner, name]` / `["job", id]` / `["commit", owner, name, hash]` 4 key
6. **跨 AC 一致性（SKILL 8 条 checklist 第四次回归）**：本变更前端无 hash/事务；AC 验证全 shell；dry-parse 不适用（无 python -c 嵌套）

## 关键决策

| 决策 | 选择 | 理由 |
|---|---|---|
| 不加后端 LIST commits/jobs API | **采用** | 范围严格；follow-up |
| 路由文件 flat naming | **采用** | 与既有一致 |
| 文件上传走 fetchJson + Blob body | **采用** | 减表面积 |
| 轮询 1s refetchInterval | **采用** | TanStack 内置；成功后停 |
| 删除 confirm 用 window.confirm | **采用** | MVP；Dialog 留 follow-up |
| Layer/Subtype 原生 `<select>` | **采用** | MVP；shadcn Select 留 follow-up |

## 跨 AC 自审 grep（SKILL 8 条 checklist 第四次回归）

```bash
grep -nE "事务前|事务内|事务外" spec.md           # 不适用
grep -nE "parents=\[\]" spec.md                  # 不适用
grep -nE "! *grep" spec.md                       # 0
grep -nE "2>/dev/null" spec.md                   # 0
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md  # 期望 ≥ 6
grep -cE "test -f|cd apps/web|grep -q|pnpm" spec.md  # 期望 ≥ 12（实测 13+）
# 第 8 条 dry-parse 不适用（spec 无 python -c 嵌套）
```

## 流程偏离

无。SKILL 8 条 checklist 第四次正式回归（rq-worker-skeleton 反哺第 8 条后）。
