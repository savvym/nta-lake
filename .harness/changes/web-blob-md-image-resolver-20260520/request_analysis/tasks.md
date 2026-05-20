---
change_id: web-blob-md-image-resolver-20260520
version: 1
authored_at: 2026-05-20T11:50:00Z
---

# Tasks

```yaml
tasks:
  - id: T-1
    title: 加 react-markdown + remark-gfm 依赖
    description: |
      apps/web/package.json 加 dependencies:
        "react-markdown": "^9.x"
        "remark-gfm": "^4.x"
      pnpm install。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending

  - id: T-2
    title: BlobPage validateSearch 加 commit 可选字段
    description: |
      apps/web/src/routes/blob.$owner.$name.$hash.tsx validateSearch:
        加 commit?: string；默认 undefined；用 zod schema 风（与 web-tree-nested-ui 一致）。
      BlobPage useSearch 解构 commit；传给 TextOrMarkdownBody。
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-2]
    status: pending

  - id: T-3
    title: FilesSection blob link 加 commit
    description: |
      apps/web/src/routes/repos/$owner.$name.tsx FilesSection 中 type=blob 行的
      Link search 加 commit（来自 commitQuery.data.hash）；两者都缺则不传。
    depends_on: [T-2]
    estimated_stage: coding
    covers_ac: [AC-3]
    status: pending

  - id: T-4
    title: BlobPage 用 ReactMarkdown + CustomImage 替换 renderMinimalMarkdown
    description: |
      blob.$owner.$name.$hash.tsx TextOrMarkdownBody:
        - 改用 <ReactMarkdown remarkPlugins={[remarkGfm]} components={{img: CustomImage}}>
          {text}</ReactMarkdown>
      CustomImage(props {src?, alt?, owner, name, commit, mdPath}):
        - 绝对 URL (http/https/data:) → 透传 <img src>
        - commit 缺 → 透传 + 文字提示
        - 否则：dirname(mdPath) 拼相对 src → useSubtreeByPath 拿 tree → entry 找 basename →
          重写 src=/api/repos/{o}/{n}/blobs/{target_hash}
        - loading / not found → 占位文字
      辅助 resolveRelative(dir, rel)：解析 .. / . / 空段；拒 leading /。
      Hooks rules：useSubtreeByPath 无条件调（enabled 内部 sha 正则把关）。
    depends_on: [T-3]
    estimated_stage: coding
    covers_ac: [AC-4, AC-5]
    status: pending

  - id: T-5
    title: blob.test.tsx 加 ≥ 3 用例
    description: |
      a. md_image_resolves_to_blob_url: mock useSubtreeByPath 返 images/a.jpg entry,
         commit 提供 → <img src=/api/.../blobs/{sha}>
      b. md_absolute_url_passes_through: src=https://... 不重写
      c. md_image_without_commit_passes_through: commit 缺 → 透传
      d.（可选）md_nested_md_relative_path
      mock useSubtreeByPath；不 mock react-markdown 让真渲染。
    depends_on: [T-4]
    estimated_stage: unit_test
    covers_ac: [AC-6, AC-8]
    status: pending

  - id: T-6
    title: scripts/_self_check.sh 加 run_web_blob_md_image_resolver 9 AC
    description: |
      在 run_web_ingest_path_default 后插入；filter case + 全跑入口 list 都加上。
    depends_on: [T-5]
    estimated_stage: coding
    covers_ac: [AC-9]
    status: pending

  - id: T-7
    title: 本地 typecheck / test / self_check current 全绿
    description: |
      pnpm --filter web typecheck
      pnpm --filter web test -- --run
      bash scripts/_self_check.sh current web-blob-md-image-resolver-20260520
    depends_on: [T-6]
    estimated_stage: ci_result
    covers_ac: [AC-7, AC-8]
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

T-1 → T-2 → T-3 → T-4 → T-5 → T-6 → T-7（无环）

## 验收覆盖

| AC | 任务 |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3 | T-3 |
| AC-4 | T-4 |
| AC-5 | T-4 |
| AC-6 | T-5 |
| AC-7 | T-7 |
| AC-8 | T-5, T-7 |
| AC-9 | T-6 |
