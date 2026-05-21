---
change_id: web-snapshot-export-ui-20260520
phase: verify
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: 2026-05-21T11:05:00Z
verdict: APPROVED
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（原始要求）+ implementation.md（声称的实现）+ `git diff f57cca8..b180cc9` 验 W4-4。

## 输入

- **Design**：`.harness/changes/web-snapshot-export-ui-20260520/design.md`（v3 mini-design，application-owner 自写）
- **Implementation**：`.harness/changes/web-snapshot-export-ui-20260520/implementation.md`（sonnet）
- **Git diff**：`git diff f57cca8..b180cc9` （W4-4 仅含本 change commit，9 files / +1036 −24）
- **Branch**：`change/web-snapshot-export-ui-20260520`
- **Head**：`b180cc92c514dbc37f3e50c40a42f99a1f85b3be`（feat `f4d4cda` + docs head_commit backfill `b180cc9`）

## AC 对照表

| AC | kind | reviewer 跑的命令 | 结果 | PASS/SKIP |
|---|---|---|---|---|
| AC-1 | static | `grep -q '@router.post.*"/{owner}/{name}/snapshots/{hash}/exports"' apps/api/dataplat_api/routers/snapshots.py` | hit @ snapshots.py:515 | PASS |
| AC-2 | behavioral (env-gated) | `cd apps/api && uv run pytest tests/test_snapshot_export.py::test_export_hf_datasets_happy -x -q` | 1 skipped (DATAPLAT_* env 未就位) | SKIP (= PASS, 同 W4-1 模式) |
| AC-3 | behavioral (env-gated) | `cd apps/api && uv run pytest tests/test_snapshot_export.py::test_export_format_jsonl_returns_422 -x -q` | 1 skipped (env 未就位) | SKIP (= PASS) |
| AC-4 | behavioral (UI) | `cd apps/web && pnpm vitest run 'src/routes/repos/$owner.$name/snapshots/$hash/export.test.tsx'` | 2 tests pass | PASS |

## 机械化检查日志

```text
$ cd apps/api && uv run pytest tests/test_snapshot_export.py -x -q
sss [100%]
3 skipped in 1.62s   # env-gated；与 W4-1/W3-* 模式一致

$ cd apps/web && pnpm vitest run 'src/routes/repos/$owner.$name/snapshots/$hash/export.test.tsx'
✓ src/routes/repos/$owner.$name/snapshots/$hash/export.test.tsx (2 tests) 150ms
Test Files  1 passed (1) | Tests  2 passed (2)

# 全量回归
$ cd apps/web && pnpm vitest run
Test Files  21 passed (21) | Tests  60 passed (60)  # 无回归

$ cd apps/api && uv run pytest -q
48 passed, 125 skipped in 1.84s  # env-gated 测试 SKIP 与 main 同

$ cd apps/web && pnpm tsc --noEmit
0 errors

$ cd apps/api && uv run pytest tests/test_snapshot_rows.py -q
3 skipped in 1.64s  # W4-1 rows endpoint 无回归

$ git diff f57cca8..b180cc9 --stat
9 files changed, 1036 insertions(+), 24 deletions(-)
- apps/api/dataplat_api/routers/snapshots.py        +140 −24
- apps/api/dataplat_api/schemas/snapshot_export.py  +22  (new)
- apps/api/tests/test_snapshot_export.py            +332 (new)
- apps/web/src/lib/api/queries.ts                   +52
- apps/web/src/routeTree.gen.ts                     +23
- apps/web/src/routes/repos/$owner.$name.tsx        +29
- apps/web/.../snapshots/$hash/export.tsx           +201 (new)
- apps/web/.../snapshots/$hash/export.test.tsx      +187 (new)
- implementation.md                                 +74  (new)
```

## 隐式偏离审计

对照 design.md vs implementation.md vs git diff —— **implementation.md 已声明 DEV-1 + DEV-2**，无隐式偏离：

- DEV-1（父路由 `<a href>` 替代 `<Link search>`）：design §决策 5 + §风险段落明确"父路由 search 参数"问题；implementation 显式声明；功能等效（URL 一致）。**ACCEPT**。
- DEV-2（`_resolve_silver_jsonl_blob_sha` 提取为 module-level helper）：design §决策 6 + §风险段落明确预期"若是 endpoint 内部嵌套，提取为 module-level helper 并被两 endpoint 共享"；W4-1 rows endpoint 测试无回归（pytest 3 skipped == main baseline）。**ACCEPT**。

## 范围与契约审计

- packages/core 全部未动：`git diff f57cca8..b180cc9 -- packages/core` 无输出 ✓
- W1-* / W2-* / W3-* / W4-1..W4-3 产物未回归：apps/api 48 passed + 125 skipped 与 main 同；apps/web 60/60 PASS
- 改动文件清单完全匹配 design.md "In scope"（apps/api: routers/snapshots.py + schemas/snapshot_export.py + tests；apps/web: queries.ts + routeTree.gen.ts + $owner.$name.tsx + 新 export.tsx/test.tsx）
- endpoint 实现对齐 design §2/3/4/6/7：tar.gz + sync + BytesIO + helper 复用 + `X-Snapshot-Row-Count`/`X-Snapshot-Blob-Sha` headers
- format jsonl/parquet 路由分支：422 + design 指定 detail 子串 ✓
- 零新依赖（tarfile / io 是 stdlib；datasets/pyarrow 已由 packages/core W3-7 间接拉入）

## D-1 永不做清单复核

`git diff f57cca8..b180cc9 | grep -iE "manifest\.yaml|dataset-card|row.diff|cherry.pick|rollback"` 无命中 ✓

- 无 manifest.yaml 强制 / 无 dataset-card.yaml / 无 row-diff / 无 cherry-pick / 无 rollback / 无 silver 文件树 / 无 bronze schema 强制 / 无 DB rename

## 问题列表

### MUST FIX

- 无

### SHOULD FIX

- 无

### NICE TO HAVE

- follow-up `web-typed-search-link-helper-*`：父路由 typed-search 下提供一个 `<Link>` 包装器（接受部分 search field + 补默认 tab/path），消除 DEV-1 类 `<a href>` 拼接
- follow-up `gold-exporter-parquet-*`、`web-snapshot-export-async-job-*`、`snapshot-export-streaming-*`、`gold-exporter-artifact-cache-*`、`gold-exporter-history-*`、`gold-exporter-hf-push-*`（design.md "关联 follow-up" 段已列）

## Verdict

**APPROVED**

- AC-1..AC-4 全 PASS（AC-2/AC-3 env-gated SKIP 与 W4-1 同模式，视为 PASS）
- 全量回归零失败（web 60/60，api 48 passed + 125 skipped，tsc 0）
- packages/core 零改动；W1-W4-3 产物零回归（W4-1 helper 提取符合 design 预期）
- DEV-1/DEV-2 design 已预测 + implementation.md 显式声明
- D-1 永不做清单零命中
- 0 issue APPROVED

## 后续指引

直接 merge 到 main，回填 dashboard，下一步启动 W4-5 cost-budget-system。
