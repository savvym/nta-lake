---
change_id: web-blob-md-image-resolver-20260520
version: 2
authored_at: 2026-05-20T11:50:00Z
revised_at: 2026-05-20T12:15:00Z
revision_notes: |
  v2 修 stage 2 reviewer v1 报的 1 条 tasks MUST FIX：
  - MUST-1（T-4 粒度过大）：拆 T-4a（ReactMarkdown 切换 + 删 renderMinimalMarkdown）
    + T-4b（resolveRelative 算法 + 路径模式分支）+ T-4c（CustomImage 组件 + hook
    集成）。三段串行，每段独立验证。
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

  - id: T-4a
    title: TextOrMarkdownBody 切换到 ReactMarkdown + remarkGfm
    description: |
      apps/web/src/routes/blob.$owner.$name.$hash.tsx::TextOrMarkdownBody：
        - 删 renderMinimalMarkdown 调用
        - 改用 <ReactMarkdown remarkPlugins={[remarkGfm]} components={{img: CustomImage}}>
          {text}</ReactMarkdown>
        - components.img 暂时占位 (alt, src) => <img alt={alt} src={src} />（T-4c 替换为
          真正的 CustomImage）
      保留 Source/Rendered 切换按钮；保留 fenced code 等渲染（ReactMarkdown 自带）。
      不动 renderMinimalMarkdown 函数定义（避免 typescript dead code 警告，标记 @deprecated 暂留供
      follow-up 清；或直删——选直删）。
    depends_on: [T-3]
    estimated_stage: coding
    covers_ac: [AC-4]
    status: pending

  - id: T-4b
    title: resolveRelative + 路径模式分支辅助函数
    description: |
      apps/web/src/routes/blob.$owner.$name.$hash.tsx 新增（top-level 或同文件 helper）：
        - isAbsoluteUrl(src): boolean —— src 以 "http://" / "https://" / "data:" 起头
        - resolveRelative(dir: string, rel: string): string —— 处理 `.` / `..` / 空段
          算法：把 dir.split("/") 与 rel.split("/") 合并；遍历每段 ".." → pop / "." → skip /
          空段 → skip；其余 push。返 join("/")。
        - resolveImagePath(mdPath: string, src: string): string | null
          - isAbsoluteUrl(src) → 返 null（调用方表示"不重写"）
          - src 以 "/" 起头 → 去掉 leading "/"，作为"仓根绝对路径"返
          - 否则 → dirname(mdPath) 与 src 用 resolveRelative 拼算，返完整仓内 path
        - splitDirAndBasename(fullPath): [dirpath, basename] 元组（用于 useSubtreeByPath 调用）
    depends_on: [T-4a]
    estimated_stage: coding
    covers_ac: [AC-5]
    status: pending

  - id: T-4c
    title: CustomImage 组件（替换 T-4a 占位）
    description: |
      新组件 CustomImage(props {src?, alt?, owner, name, commit, mdPath}):
        1. 用 T-4b 的 resolveImagePath(mdPath, src)：
           - 返 null（绝对 URL） → 透传 <img src={src} alt={alt}>
           - 返 string 路径 → 继续
        2. commit 缺 / 不是 64-hex sha → 透传 + 小字提示 "(no commit, 路径不解析)"
        3. 否则：用 splitDirAndBasename 拆，调 useSubtreeByPath(owner, name, commit,
           dirpath) —— 注意：hooks rules，无论分支都要无条件调（不能放 if 后）
           - isLoading → <span className="text-gray-400">(loading {src})</span>
           - isError 或 entries 里找不到 basename / entry_type != "blob" → 透传 + 提示
           - 找到 → 渲染 <img src={`/api/repos/${owner}/${name}/blobs/${target_hash}`} alt={alt}>
        集成进 T-4a 的 components.img。
    depends_on: [T-4b]
    estimated_stage: coding
    covers_ac: [AC-5]
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
    depends_on: [T-4c]
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

T-1 → T-2 → T-3 → T-4a → T-4b → T-4c → T-5 → T-6 → T-7（无环）

## 验收覆盖

| AC | 任务 |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3 | T-3 |
| AC-4 | T-4a |
| AC-5 | T-4b, T-4c |
| AC-6 | T-5 |
| AC-7 | T-7 |
| AC-8 | T-5, T-7 |
| AC-9 | T-6 |
