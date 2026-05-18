---
change_id: repo-files-tab-v2-20260518
version: 1
authored_at: 2026-05-18T22:55:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC ID | 测试文件 | 测试函数 |
|---|---|---|
| AC-6 (a) | apps/web/src/lib/api/blob-meta.test.tsx | `useBlobMeta > fetches /meta endpoint and returns sha256 + size` |
| AC-6 (b) | apps/web/src/routes/repos.tabs.test.tsx | `RepoDetailPage Tabs URL state > clicking Pipelines tab updates URL to ?tab=pipelines` |
| AC-6 (c) | apps/web/src/routes/blob.test.tsx | `BlobPage rendering > renders plain text preview for .txt blob within size limit` |
| AC-6 (d) | apps/web/src/routes/blob.test.tsx | `BlobPage rendering > renders binary fallback for unknown extension` |
| AC-6 (e) | apps/web/src/routes/blob.test.tsx | `BlobPage rendering > blocks preview when size > 5 MB and does not fetch` |
| AC-7 (a) | apps/api/tests/test_commits.py | `test_blob_meta_returns_size` |
| AC-7 (b) | apps/api/tests/test_commits.py | `test_blob_meta_not_found` |
| AC-7 (c) | apps/api/tests/test_commits.py | `test_blob_meta_public_anon` |

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| apps/web/src/lib/api/blob-meta.test.tsx | unit (renderHook + spyOn fetch) | 1 |
| apps/web/src/routes/repos.tabs.test.tsx | integration (createMemoryHistory + RouterProvider) | 1 |
| apps/web/src/routes/blob.test.tsx | integration (createMemoryHistory + RouterProvider + mock useBlobMeta) | 3 |
| apps/api/tests/test_commits.py | integration (ASGITransport + 真 PG/MinIO) | 3 (新增 test_blob_meta_*) |

总计：**5 vitest + 3 pytest = 8 测试，全部 PASS**。

## Mock 范围声明

### 允许 mock
- 前端 `useBlobMeta` (T-8c) / 整个 `../lib/api/queries` 模块（T-8b/T-8c）：避免 mount 真 router 时初始化所有 hooks 的副作用。
- 前端 `globalThis.fetch`（T-8a/T-8c）：spyOn 模式，参考既有 `pipeline.test.tsx` L68。

### 禁止 mock
- 后端 `BlobStore` / `BlobService` / `RepoService`：T-3 走 ASGITransport + 真 MinIO + 真 PG，无 mock。
- 前端 `validateSearch` / TanStack Router 内部：T-8b 用 `createMemoryHistory + createRouter` 真渲染，验证 URL 真切到 `?tab=pipelines`。

### 本轮 mock
- T-8c `useBlobMeta` 返回 fixture：避免触发真 fetch / 真 useQuery 副作用（hook 行为已由 T-8a 单测覆盖；T-8c 聚焦 BlobPage 渲染分支）。
- T-8b 全套 hooks mock 为 noop（useMe 返 admin / 其余 noop）：避免 RepoDetailPage mount 时调用真后端。

## 本地运行结果

```text
$ cd apps/web && npx vitest run src/lib/api/blob-meta.test.tsx src/routes/repos.tabs.test.tsx src/routes/blob.test.tsx
 Test Files  3 passed (3)
       Tests  5 passed (5)
    Duration  1.73s

$ cd apps/api && DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
    DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
    DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
    DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx \
    DATAPLAT_MINIO_ENDPOINT=http://localhost:9100 \
    DATAPLAT_REDIS_URL=redis://localhost:6379/0 \
    uv run pytest -q --tb=no tests/test_commits.py -k blob_meta
... 3 passed, 18 deselected in 2.21s
```

## 已知 flaky / 跳过

- 无 skip。
- stderr noise：`Not implemented: window.scrollTo`（jsdom 25 缺 implementation；不影响 pass 计数；follow-up `web-test-jsdom-scrollTo-shim-*` 加 shim 到 test-setup.ts）。

## 覆盖率

未单独跑覆盖率（仓库未配置 vitest coverage / pytest-cov 阈值）。本 change 主要新增代码：
- `blob.$owner.$name.$hash.tsx` ~340 行：4 渲染分支 + 5MB 守门 + minimal markdown renderer 均有测试覆盖。`renderMinimalMarkdown` 是 export，未单独 unit-test 4 类语法（→ follow-up `web-markdown-renderer-direct-test-*`）。
- `commits.py` `get_blob_meta` ~20 行：3 个 pytest 覆盖 200 / 404 / anon 路径。

## 下一步

进入阶段 6 单测评审：spawn sonnet reviewer，加载 expert-reviewer SKILL（artifact 模式），写 `unit_test/review/test_review_v1.md`。
