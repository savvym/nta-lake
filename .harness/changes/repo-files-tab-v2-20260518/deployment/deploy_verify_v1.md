---
change_id: repo-files-tab-v2-20260518
version: 1
env: dev
deployed_at: 2026-05-18T22:55:00Z
image_tag: dev-local (worktree build)
commit_sha: (pending push)
verifier: application-owner-agent
verdict: PASS
---

# Deploy Verification v1

## 验证矩阵

| ID | 验收项 | 验证方式 | 期望 | 实际 | 证据 |
|---|---|---|---|---|---|
| AC-1 | 后端 commits.py 含 get_blob_meta + schemas/blob.py BlobMetaResponse | self_check AC-1（4 grep） | 全命中 | PASS | self_check 输出 §AC-1 |
| AC-2 | queries.ts useBlobMeta + BlobMetaResponse | self_check AC-2（4 grep + awk） | 全命中 | PASS | self_check 输出 §AC-2 |
| AC-3 | RepoDetailPage Tabs URL state | self_check AC-3（6 grep + 注释 // ?tab= 命中字面） | 6 grep 全命中 | PASS | self_check 输出 §AC-3 |
| AC-4 | blob.$owner.$name.$hash.tsx 4 渲染策略 + 5MB | self_check AC-4（3 grep + 3 alt-group） | 全命中 | PASS | self_check 输出 §AC-4 |
| AC-5 | FilesSection path 列改 Link → /blob | self_check AC-5（awk + 2 grep） | 全命中 | PASS | self_check 输出 §AC-5 |
| AC-6 | vitest ≥5 PASS | self_check AC-6（NO_COLOR=1 + sed 剥 ANSI + 2 grep alt） | 5 passed | PASS | `Tests  5 passed (5)` |
| AC-7 | pytest ≥3 PASS（blob_meta） | self_check AC-7（PG/MinIO/Redis 真起 + 2 grep alt） | 3 passed | PASS | `3 passed, 18 deselected in 2.21s` |
| AC-8 | self_check 本 block 全 PASS + npm run build 干净 | bash self_check 退码 0 + `built in` + 无 `error TS` 无 `Found N errors` | 退码 0 + build 干净 | PASS | `built in 2.29s` + tsc 0 errors |
| LINT-1 | reviewer-lint 未引回归 | bash self_check.sh reviewer-lint | 退码 0 | PASS | `PASS reviewer-lint` |
| LINT-2 | ac-kind-lint 未引回归 | bash self_check.sh ac-kind-lint | 退码 0 | PASS | `PASS ac-kind-lint` |

## 证据

### Self-check 输出（repo-files-tab-v2 block）

```text
$ DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat \
   DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 \
   bash scripts/_self_check.sh repo-files-tab-v2

=== repo-files-tab-v2-20260518 :: 8 AC ===
PASS  AC-1  commits.py 加 get_blob_meta 路由 + schemas/blob.py 含 BlobMetaResponse（4 直接 grep）
PASS  AC-2  queries.ts 含 BlobMetaResponse interface + useBlobMeta hook（含 awk 锚定 /meta）
PASS  AC-3  repos/$owner.$name.tsx 含 Tabs 实现：tab= + 3 个 Tab key + useSearch
PASS  AC-4  blob.$owner.$name.$hash.tsx 存在 + createFileRoute + useBlobMeta + 5MB 常量 + Markdown renderer + 图片扩展名
PASS  AC-5  FilesSection 函数体含 /blob/$owner/$name/$hash + search（awk 状态机锚定）
PASS  AC-6  vitest 3 测试文件 ≥5 passed（拆 alternation 为 2 grep + shell ||；sed 剥 ANSI 颜色 escape）
PASS  AC-7  pytest blob_meta ≥3 passed（拆 alternation）
PASS  AC-8  npm run build 干净（拆 alternation 为 2 个 !grep）

=== 汇总 ===
PASS: 8 / FAIL: 0 / SKIP: 0
全部通过（FAIL=0；SKIP 不阻塞）。
```

### 单测真跑

```text
$ cd apps/web && NO_COLOR=1 npx vitest run src/lib/api/blob-meta.test.tsx src/routes/repos.tabs.test.tsx src/routes/blob.test.tsx
 Test Files  3 passed (3)
       Tests  5 passed (5)
    Duration  1.73s

$ cd apps/api && uv run pytest -q --tb=no tests/test_commits.py -k blob_meta
... 3 passed, 18 deselected in 2.21s
```

### 生产构建

```text
$ cd apps/web && npm run build
vite v5.4.21 building for production...
✓ 268 modules transformed.
dist/assets/index-C4NjaNB9.js   431.35 kB │ gzip: 131.99 kB
✓ built in 2.29s
（tsc --noEmit 后续运行无 stdout = 0 errors）
```

### Global lint

```text
$ bash scripts/_self_check.sh reviewer-lint
PASS  reviewer-lint  reviewer 字段独立性守门（反向×2 + 白名单）

$ bash scripts/_self_check.sh ac-kind-lint
PASS  ac-kind-lint  AC 分层规约守门（kind 列存在 + AC 行 kind=behavioral 锚定 regex）
```

## 风险评估

- [x] 涉及 schema 不兼容？**否**。新增 BlobMetaResponse schema + GET 路由，与既有 BlobUploadResponse / download_blob 并存；无既有 client 受影响。
- [x] 涉及不可回滚操作？**否**。纯添加（路由 + schema + 前端 Tab + 新路由）；回滚 = revert commit。
- [x] 需要 follow-up？**是**：
  - `web-test-jsdom-scrollTo-shim-*`（清 stderr noise）
  - `web-markdown-renderer-full-*`（完整 markdown 语法）
  - `web-markdown-renderer-direct-test-*`（直接单测 renderMinimalMarkdown）
  - `web-ref-switcher-*`（副信息卡 ref 字段当前固定 "—"）
  - `web-blob-syntax-highlight-*`
  - `web-blob-edit-*`
  - `commit-page-preview-*`
  - `tree-nested-*`

## Verdict

**PASS**

## 处理动作

- PASS → 进入阶段 10 用户确认（浏览器实测：登录 admin → 进 repo 详情 → 点 Files tab 文件 → 看预览页 4 渲染策略）。
- 本次未跑真 dev server（无 remote + 用户实测交付）；后续 stage 10 用户在主 checkout 跑 `cd apps/api && uv run uvicorn dataplat_api.main:app --port 8080 &` + `cd apps/web && npm run dev` 验证 URL `/repos/...` 看 Tab + `/blob/...` 看预览。
