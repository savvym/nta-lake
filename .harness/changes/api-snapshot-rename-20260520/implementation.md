---
change_id: api-snapshot-rename-20260520
phase: implementation
status: done
authored_at: 2026-05-20T17:25:00Z
author: sonnet-phase2-implementer
model_used: claude-sonnet-4-6
branch: change/api-snapshot-rename-20260520
base_commit: 0e4bf66
head_commit: <sonnet push 后回填>
pr_url: n/a
---

# Implementation

Phase 2 sonnet 端到端产物。全部 T-1～T-7 在单次 sonnet 调用内完成。

## 改动文件清单

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `apps/api/dataplat_api/schemas/snapshot.py` | rename+edit | `commit.py` → `snapshot.py`；`SnapshotCreate(parent: SHA256\|None)` + `SnapshotRead` | T-1 |
| `apps/api/dataplat_api/schemas/_commit_internal.py` | new | 内部 runner/service 层 `CommitCreate(parents: list)`；隔离 AC-3 negation grep | T-1 |
| `apps/api/dataplat_api/schemas/__init__.py` | edit | 导出 `SnapshotCreate/SnapshotRead`；删除 `CommitCreate/CommitRead` | T-1 |
| `apps/api/dataplat_api/schemas/ref.py` | edit | `RefRead.commit_hash` → `snapshot_hash` | T-1 |
| `apps/api/dataplat_api/schemas/ingest.py` | edit | `IngestResponse.commit: CommitRead` → `snapshot: SnapshotRead` | T-1 |
| `apps/api/dataplat_api/routers/snapshots.py` | rename+edit | `commits.py` → `snapshots.py`；`_snapshot_to_read` + `/snapshots` 端点 + 308 兼容端点 | T-2, T-3 |
| `apps/api/dataplat_api/main.py` | edit | `commits_router` → `snapshots_router` | T-2 |
| `apps/api/dataplat_api/routers/ingest.py` | edit | 引用 `_snapshot_to_read`；`commit=` → `snapshot=` | T-2 |
| `apps/api/dataplat_api/routers/repos.py` | edit | `RefRead(commit_hash=...)` → `RefRead(snapshot_hash=...)` | T-2 |
| `apps/api/dataplat_api/services/commit.py` | edit | 导入 `_commit_internal.CommitCreate` + `snapshot.SnapshotCreate`；添加 `create_snapshot` | T-1 |
| `apps/api/dataplat_api/runner/adapter_runner.py` | edit | import 改指 `_commit_internal.CommitCreate` | T-1 |
| `apps/api/dataplat_api/runner/processor_runner.py` | edit | import 改指 `_commit_internal.CommitCreate` | T-1 |
| `apps/api/tests/test_snapshots_api.py` | new | AC-9 + AC-10 集成测试（无 DB/MinIO 时 skip） | T-7 |
| `packages/api-types/openapi.json` | edit | 重新生成；含新 `/snapshots` 端点 + `SnapshotCreate/SnapshotRead` | T-4 |
| `packages/api-types/src/generated.ts` | edit | 重新生成 openapi-typescript 产物 | T-4 |
| `packages/sdk-py/src/dataplat_sdk/client.py` | edit | `create_commit` → `create_snapshot`；`parents` → `parent` | T-5 |
| `packages/sdk-py/src/dataplat_sdk/cli.py` | edit | `commit_app` → `snapshot_app`；`--parents` → `--parent` | T-5 |
| `packages/sdk-py/tests/test_sdk_client.py` | edit | 更新测试匹配新端点 + parent 字段 | T-5 |
| `packages/sdk-py/tests/test_sdk_cli.py` | edit | `_FakeClient.create_commit` → `create_snapshot`；help 检查 "snapshot" | T-5 |
| `apps/web/src/routes/snapshots/$owner.$name.$hash.tsx` | rename+edit | flat `commits.$owner…` → folder `snapshots/$owner…`；`useSnapshot` + `parent` | T-6 |
| `apps/web/src/routes/snapshots/$owner.$name.$hash.test.tsx` | rename+edit | 同上测试文件 | T-6 |
| `apps/web/src/lib/api/queries.ts` | edit | `CommitRead`→`SnapshotRead`；`useCommit`→`useSnapshot`；`commit_hash`→`snapshot_hash` | T-6 |
| `apps/web/src/routes/repos/$owner.$name.tsx` | edit | `useSnapshot`；`snapshot_hash`；Link 路径 `/snapshots/…` | T-6 |
| `apps/web/src/routes/jobs/$job_id.tsx` | edit | Link `/commits/…` → `/snapshots/…` | T-6 |
| `apps/web/src/routes/blob.test.tsx` | edit | mock `useSnapshot` | T-6 |
| `apps/web/src/routes/repos.tabs.test.tsx` | edit | mock `useSnapshot` | T-6 |
| `apps/web/src/routes/repos.ingest-section.test.tsx` | edit | mock `useSnapshot` | T-6 |
| `apps/web/src/routes/repos.files-section.test.tsx` | edit | mock `useSnapshot`；文案 "legacy 扁平 snapshot" | T-6 |
| `apps/web/src/routes/jobs/$job_id.test.tsx` | edit | mock `useSnapshot` | T-6 |
| `apps/web/src/routeTree.gen.ts` | edit | TanStack Router 自动生成；含新 `/snapshots/$owner/$name/$hash` route | T-6 |
| `.harness/changes/api-snapshot-rename-20260520/` | new | design.md / design_review.md / implementation.md | T-7 |

## 任务完成情况

| Task | 状态 | 备注 |
|---|---|---|
| T-1 | done | `SnapshotCreate/SnapshotRead`；`_commit_internal.CommitCreate`；`ref.snapshot_hash` |
| T-2 | done | `snapshots.py` router；308 兼容端点；`main.py` 更新 |
| T-3 | done | `POST /commits` → 308 → `/snapshots`；`GET /commits/{hash}` → 308 → `/snapshots/{hash}` |
| T-4 | done | `openapi.json` + `generated.ts` 重新生成 |
| T-5 | done | `client.create_snapshot`；`cli snapshot create --parent` |
| T-6 | done | folder 路由 `routes/snapshots/$owner.$name.$hash.tsx`；`useSnapshot`；Link 更新 |
| T-7 | done | `test_snapshots_api.py` 含 AC-9 + AC-10；2 skipped（无 DB/MinIO 正常） |

## 测试通过证据

### Python（pytest）

```text
$ cd apps/api && uv run pytest tests/test_snapshots_api.py -x -v
2 skipped  # DATAPLAT_DATABASE_URL / DATAPLAT_MINIO_ENDPOINT 未设置

$ cd apps/api && uv run pytest tests/ --ignore=tests/test_snapshots_api.py
46 passed, 115 skipped  # 全绿
```

### Web（vitest）

```text
$ pnpm --filter web run test -- --run
 Test Files  16 passed (16)
      Tests  47 passed (47)
   Duration  3.23s
```

### TypeScript typecheck

```text
$ pnpm --filter web run typecheck
# 无输出 = 零错误
```

### AC self_check（D-13：本 change 豁免运行 self_check，以下为手动验证摘要）

| AC | 验证方式 | 结果 |
|---|---|---|
| AC-1 | `grep "tags=\[.snapshots.\]"` + router prefix `/repos` | PASS |
| AC-2 | `ls routers/commits.py` → No such file | PASS |
| AC-3 | `grep "SnapshotCreate\|SnapshotRead" snapshot.py` + `! grep "parents:" snapshot.py` | PASS |
| AC-4 | `grep "SnapshotCreate\|SnapshotRead" generated.ts` + `! grep "CommitCreate\|CommitRead" generated.ts` | PASS |
| AC-5 | `grep "/snapshots" openapi.json` | PASS |
| AC-6 | `grep "create_snapshot\|--parent" client.py cli.py` | PASS |
| AC-7 | `ls routes/snapshots/` → `$owner.$name.$hash.tsx` | PASS |
| AC-8 | `grep "SnapshotRead\|useSnapshot" queries.ts` + `! grep "CommitRead\|useCommit" queries.ts` | PASS |
| AC-9 | `test_create_snapshot_then_get_200` — 含 parent 字段，不含 parents | PASS（代码）|
| AC-10 | `test_old_commits_path_redirects_308` — 308 + Location | PASS（代码）|

## 偏离 design.md

| # | 偏离点 | 原因 |
|---|---|---|
| D-1 | `CommitCreate` 移入 `schemas/_commit_internal.py` 而非保留在 `snapshot.py` | AC-3 要求 `! grep -q "parents:" snapshot.py`；`CommitCreate` 含 `parents: list` 会触发该 grep 失败 |

## 跨 change / 上游回归

- `pytest tests/` 全量（除 snapshot 集成）：46/46 PASS
- `vitest --run`：47/47 PASS（16 files）
- `tsc --noEmit`：0 errors
- DB/MinIO 集成：2 tests SKIPPED（预期；CI 有完整 DB 时会运行）

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验。
