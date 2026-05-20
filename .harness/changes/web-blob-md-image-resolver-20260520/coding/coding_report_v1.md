---
change_id: web-blob-md-image-resolver-20260520
version: 1
authored_at: 2026-05-20T12:30:00Z
branch: change/web-blob-md-image-resolver-20260520
base_commit: 5ad8cfd
head_commit: TBD
status: waiting_review
---

# Coding Report v1

## 改动

| 路径 | 改动 | 任务 |
|---|---|---|
| apps/web/package.json | + react-markdown ^9 + remark-gfm ^4 | T-1 |
| apps/web/src/routes/blob.$owner.$name.$hash.tsx | validateSearch 加 commit zod 字段 / 新增 isAbsoluteUrl/resolveRelative/resolveImagePath/splitDirAndBasename helpers / TextOrMarkdownBody 用 ReactMarkdown+remarkGfm 替换 renderMinimalMarkdown / 新 CustomImage 组件用 useSubtreeByPath 解析路径重写 src | T-2/T-4a/T-4b/T-4c |
| apps/web/src/routes/repos/$owner.$name.tsx | FilesSection blob link search 加 commit | T-3 |
| apps/web/src/routes/blob.test.tsx | mock 加 useSubtreeByPath / 新 3 用例 (image rewrite / 绝对 URL / no commit) + 3 helper 单测 | T-5 |
| scripts/_self_check.sh | run_web_blob_md_image_resolver 9 AC + filter + 全跑入口 | T-6 |

renderMinimalMarkdown 完整删除（94 行 dead code）。

## 与 tasks 映射

T-1 done / T-2 done / T-3 done / T-4a done / T-4b done / T-4c done / T-5 done (9 用例) / T-6 done / T-7 done

## 本地

```
typecheck: 0 errors
vitest: 39 passed (16 files)（含 blob.test.tsx 9 + 其他 30）
self_check current: 18/18 PASS
```
