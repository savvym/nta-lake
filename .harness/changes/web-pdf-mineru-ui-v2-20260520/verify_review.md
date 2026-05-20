---
change_id: web-pdf-mineru-ui-v2-20260520
phase: verify
status: approved
verdict: APPROVED
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
reviewed_at: 2026-05-20T22:25:00Z
ac_kind_lint: enforce
---

# Verify Review：Web PDF→Silver Row UI v2 (W4-1) — APPROVED

**VERDICT：APPROVED**（0 MUST FIX / 0 SHOULD FIX / 1 NICE TO HAVE，非阻塞）。

4 个 behavioral AC 全 PASS（3 backend + 2 frontend，需 Postgres+MinIO env）；apps/web 全套 17/17 files 49/49 tests PASS（+2 新增）；apps/api 全套 48 failed / 122 passed 与 main 48 failed / 119 passed 失败集合**逐字一致**（diff 空，仅 +3 新 PASS），零回归引入；diff scope 严格限定在 design 允许范围（packages/core 0 行、其他 routers 0 行）；3 个 DEV 偏离全部 ACCEPT（已在 design 风险表/已知噪音预批）。

## 输入

- Design：`.harness/changes/web-pdf-mineru-ui-v2-20260520/design.md`
- Implementation：`.harness/changes/web-pdf-mineru-ui-v2-20260520/implementation.md`
- Git diff：`git diff main...change/web-pdf-mineru-ui-v2-20260520`
- HEAD：`5afa515` (branch `change/web-pdf-mineru-ui-v2-20260520`)

## 1. AC 对照表

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL |
|---|---|---|---|---|
| AC-1 | behavioral | `cd apps/api && DATAPLAT_* env vars ... uv run --extra dev pytest tests/test_snapshot_rows.py::test_rows_happy_paginated -x -q` | 1 passed | PASS |
| AC-2 | behavioral | `... pytest tests/test_snapshot_rows.py::test_rows_snapshot_not_found -x -q` | 1 passed | PASS |
| AC-3 | behavioral | `... pytest tests/test_snapshot_rows.py::test_rows_jsonl_resolution_errors -x -q` | 1 passed | PASS |
| AC-4 | behavioral | `cd apps/web && pnpm test -- pdf-mineru.test` | 2 passed (renders 3 rows / clicking detail expands JSON) | PASS |

实际跑（合并）：

```text
$ cd apps/api && DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
  DATAPLAT_MINIO_ENDPOINT=http://localhost:9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat \
  DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_MINIO_REGION=us-east-1 \
  DATAPLAT_BLOB_BUCKET=dataplat-blobs DATAPLAT_REDIS_URL=redis://localhost:6379/0 \
  DATAPLAT_JWT_SECRET=local-dev-secret-not-prod-x32-bytes-xxxxx \
  uv run --extra dev pytest tests/test_snapshot_rows.py -x -q -v
collected 3 items
tests/test_snapshot_rows.py::test_rows_happy_paginated PASSED            [ 33%]
tests/test_snapshot_rows.py::test_rows_snapshot_not_found PASSED         [ 66%]
tests/test_snapshot_rows.py::test_rows_jsonl_resolution_errors PASSED    [100%]
========== 3 passed, 2 warnings in 2.79s ==========

$ cd apps/web && pnpm test -- pdf-mineru.test
✓ src/routes/repos/$owner.$name/pdf-mineru.test.tsx (2 tests) 164ms
   ✓ /repos/$owner/$name/pdf-mineru > renders 3 rows table from useSnapshotRows
   ✓ /repos/$owner/$name/pdf-mineru > clicking detail button expands row JSON
Test Files  1 passed (1)
     Tests  2 passed (2)
```

无需 env 时 backend 3 测试走 `pytestmark = pytest.mark.skipif(not (DATAPLAT_DATABASE_URL and DATAPLAT_MINIO_ENDPOINT))` 跳过（与 test_commits.py / test_snapshots_api.py 同模式）；env 设上后全 PASS。

## 2. Cross-regression

### apps/web（17/17 files，49/49 tests）

```text
$ cd apps/web && pnpm test
Test Files  17 passed (17)
     Tests  49 passed (49)
Duration  3.43s
```

47 → 49（+2 AC-4 新增），零回归。

### apps/api（branch vs main：失败集合逐字一致）

```text
branch (5afa515):  48 failed, 122 passed
main   (d706fd1):  48 failed, 119 passed
diff /tmp/api_fail_main.txt /tmp/api_fail_branch.txt → (empty)
```

122 - 119 = +3 = W4-1 新增 3 backend test。**零新失败**。48 pre-existing failures（tree_nested / processor / jobs / pipeline_e2e / refs / commits / firecrawl / llm / ingest / llm_qa_gen / pipeline_orchestrator）均与本 change 改的 snapshots.py 无关；session_handoff_20260519 标注的"42 failed pre-existing"已增长到 48，但增长发生在 main 上、与本 change 无关（应由 owner 单独 follow-up）。

## 3. Diff scope 审计

```text
$ git diff main...HEAD --name-only
.harness/changes/web-pdf-mineru-ui-v2-20260520/design.md          (4 harness)
.harness/changes/web-pdf-mineru-ui-v2-20260520/implementation.md
.harness/changes/web-pdf-mineru-ui-v2-20260520/summary.md
.harness/changes/web-pdf-mineru-ui-v2-20260520/verify_review.md
apps/api/dataplat_api/routers/snapshots.py                       (+92 纯追加)
apps/api/dataplat_api/schemas/snapshot_rows.py                   (new, 29 行)
apps/api/tests/test_snapshot_rows.py                             (new, 411 行)
apps/web/src/lib/api/queries.ts                                  (+47 hook)
apps/web/src/routeTree.gen.ts                                    (TanStack 自动 regen)
apps/web/src/routes/repos/$owner.$name.tsx                       (+2: Outlet)
apps/web/src/routes/repos/$owner.$name/pdf-mineru.tsx            (new, 183 行)
apps/web/src/routes/repos/$owner.$name/pdf-mineru.test.tsx       (new, 155 行)
```

- packages/core：**0 行**改动（grep clean）
- 其他 routers：**0 行**改动（仅 snapshots.py 末尾 +92 追加，不动现有 endpoint）
- $owner.$name.tsx：仅 `Outlet` import + 1 行 `<Outlet />` 渲染，不影响现有 UI
- routeTree.gen.ts：TanStack vite plugin 自动生成，更新 import path 指向 folder 形式
- 不在 design Out-of-scope 列表（react-virtual / 通用 row preview / multi-step chain / websocket / 导出 / 真浏览器 e2e / silver 流式 / W1-* W2-* W3-* 已 merge 产物 / 老 blob viewer / snapshots/$hash metadata viewer / manifest.yaml / SilverRow auto-infer）的任何文件被触及

snapshots.py 的改动是 pure addition（diff 仅 `^+` 行，零 `^-` 行除注释），endpoint 路径与 design § 范围声明完全一致：`GET /repos/{owner}/{name}/snapshots/{hash}/rows` + offset/limit/blob_sha query params + 422 errors `silver_snapshot_no_jsonl_entry` / `silver_snapshot_ambiguous_blob_sha` + auto-find single .jsonl entry。

## 4. DEV 偏离评估

| # | sonnet 报的偏离 | reviewer 判断 | 理由 |
|---|---|---|---|
| D-1 | 路由用 folder 形式 `routes/repos/$owner.$name/pdf-mineru.tsx` 而非 flat-dot | **ACCEPT** | design.md § 风险表第 4 行已 fallback 授权："如 sonnet 跑测试时报路由 ambiguous → fallback 改 folder form"；且与 user memory `feedback_tanstack_routing_folder_form`（index+$param 共存须 folder form）一致 |
| D-2 | `routes/repos/$owner.$name.tsx` 加 `<Outlet />` + Outlet import | **ACCEPT** | folder 形式强制嵌套，父必须渲染 Outlet 才能显示子路由；diff 实测仅 +2 行（import + 1 个 `<Outlet />` JSX），无其他 UI 行为变更；零副作用 |
| D-3 | `async for chunk in store.get(sha)` 而非 `data = await store.get(sha)` | **ACCEPT** | design.md § 风险表第 1 行明确列入 "BlobStore.get 返回 AsyncIterator vs bytes Protocol drift（W3-4..W3-7 已知噪音）"；与 W3-4 同 concat pattern；workspace-root pyright drift 噪音 |

3/3 DEV 全部预批通过。无隐式偏离（reviewer 对照 design § 范围 vs git diff 文件清单，零未声明改动）。

## 5. 永不做清单 / 北极星合规

- 无 manifest.yaml 引入
- 无 branch / merge / cherry-pick / rollback 概念
- 无行级 diff（rows endpoint 是只读 list，非 changeset）
- 无 blob 派生图 / Asset 概念
- 无 silver 文件树（仍 JSONL → row list）
- 无 bronze 强 schema
- 仍走 CAS sha256 整文件版本

## 6. 实现质量抽查

- `SilverRowRead` / `SnapshotRowsResponse` 双 `extra="forbid"` ✓（design 决策 5 / OpenAPI 防漂移）
- `Path(pattern=_SHA256_PATTERN)` snapshot hash 校验 ✓
- `Query(0, ge=0)` / `Query(50, ge=1, le=500)` 参数约束 ✓（design 范围）
- visibility 矩阵复用 `_resolve_repo` + `get_optional_user` ✓（决策 1）
- 422 `silver_snapshot_no_jsonl_entry` + `silver_snapshot_ambiguous_blob_sha; pass ?blob_sha=` ✓（决策 10）
- `errors="replace"` 防解码异常 ✓
- `KeyError` 转 404 `Blob {sha} 不存在` ✓
- frontend `useSnapshotRows` queryKey 含 offset/limit ✓（风险 4：可接受不开 keepPreviousData）

## 7. 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

- **NICE-1**：`implementation.md` § 测试通过证据写的命令 `uv run --extra dev pytest tests/test_snapshot_rows.py -x -q -v` 在无 env vars 时实际是 3 SKIPPED 而非 3 passed；建议 follow-up `harness-test-evidence-env-prefix-*` 在 sonnet 报告测试证据时必须明示 env 前缀（DATAPLAT_DATABASE_URL=... 等），或加 self_check.sh 校验。本 change 不阻塞——env 设上后真实 3 PASS。

## Verdict

**APPROVED** — 0 MUST FIX / 0 SHOULD FIX / 1 NICE TO HAVE（非阻塞）。4 个 AC 全 PASS，apps/web 0 回归，apps/api 失败集合逐字一致零新回归，3 个 DEV 偏离全部预批 ACCEPT，diff scope 严格符合 design § 范围，永不做清单 grep clean。15 连 0-MUST-FIX APPROVED 延续。

## 后续指引

1. application-owner merge `change/web-pdf-mineru-ui-v2-20260520` → main（建议 `--no-ff`）
2. close W4-1 task，更新 orchestration W4 计数 1/10 done
3. 启动下一个 W4-* change（参考 design 决策 / 关联 follow-up）
4. 可选：在 `.harness/follow-ups/` 立 `harness-test-evidence-env-prefix-*`（NICE-1）
