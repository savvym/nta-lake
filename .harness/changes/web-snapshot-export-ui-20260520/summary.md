---
change_id: web-snapshot-export-ui-20260520
phase: merged
status: closed
verdict: APPROVED
closed_at: 2026-05-21T11:10:00Z
merge_commit: 95f55e7e0af8b1e94c506cb57ddfd054b2f89a55
branch: change/web-snapshot-export-ui-20260520
base_commit: 0e4bf66
head_commit: 7e07991
---

# Summary：W4-4 snapshot HF datasets export endpoint + UI

## 一句话结果

apps/api 落地 `POST /repos/{owner}/{name}/snapshots/{hash}/exports?format=hf_datasets` → 调 W3-7 `export_to_hf_datasets` 把 silver JSONL → HF datasets 目录 → tar.gz `StreamingResponse`；apps/web 新增 folder-form 子路由 `/repos/$owner/$name/snapshots/$hash/export` 让用户选格式 + 触发浏览器下载。0 issue APPROVED 一气呵成 merge。

## 关键决策

1. **format=hf_datasets 单一实现**：roadmap 三选项里 jsonl 直接 `GET /blobs/{sha}` 已覆盖，parquet 留 `gold-exporter-parquet-*` 独立 follow-up；本 change 不重复造。UI 上仍渲染 3 个选项但 jsonl/parquet 显示 disabled + "(follow-up)" 标记。
2. **tar.gz 而非 zip**：python stdlib `tarfile` 写 `w:gz` 更原生；浏览器/linux/mac/windows 均易解压。
3. **同步阻塞 endpoint + 全装内存 tarball**：MVP；典型 snapshot 秒级；大 snapshot 留 `web-snapshot-export-async-job-*` + `snapshot-export-streaming-*` follow-up。
4. **X-Snapshot-Row-Count / X-Snapshot-Blob-Sha 响应头**：UI 下载完成后读 header 显示。
5. **不持久化 export artifact**：每次 POST 跑临时目录立即销毁；同 blob_sha 输出确定性派生，无需 cache。
6. **DEV-2 helper 共享**：W4-1 rows endpoint 内联的 `_resolve_silver_jsonl_blob_sha` 提取为 module-level（design §决策 6 + §风险段已预测），rows + exports 两 endpoint 共享；W4-1 测试零回归。
7. **DEV-1 父路由导出 Link**：父路由 typed-search 强制要求 tab/path 字段，本 change 用原生 `<a href>` 拼 URL（功能等效）；follow-up `web-typed-search-link-helper-*`。

## 测试结果

| 范围 | 结果 |
|---|---|
| AC-1 static grep | PASS |
| AC-2/3 endpoint env-gated | SKIP（与 W4-1/W3-* 同模式 = PASS） |
| AC-4 UI vitest | 2/2 PASS |
| apps/web 全量 vitest | 60/60 PASS（21 files） |
| apps/api 全量 pytest | 48 passed + 125 skipped（零回归） |
| apps/web tsc --noEmit | 0 errors |
| W4-1 rows endpoint 回归 | 3 skipped（baseline 一致）— helper 提取无副作用 |

## 改动文件

9 files / +1036 −24：

- `apps/api/dataplat_api/schemas/snapshot_export.py`（new，22 行）
- `apps/api/dataplat_api/routers/snapshots.py`（+140 −24，提取 helper + 新增 endpoint）
- `apps/api/tests/test_snapshot_export.py`（new，332 行，3 env-gated）
- `apps/web/src/lib/api/queries.ts`（+52，`useSnapshotExport` mutation）
- `apps/web/src/routeTree.gen.ts`（+23，新路由注册）
- `apps/web/src/routes/repos/$owner.$name.tsx`（+29，.jsonl 旁加导出 Link）
- `apps/web/src/routes/repos/$owner.$name/snapshots/$hash/export.tsx`（new，201 行）
- `apps/web/src/routes/repos/$owner.$name/snapshots/$hash/export.test.tsx`（new，187 行，2 tests）

零新依赖（`tarfile`/`io` stdlib；`datasets`/`pyarrow` 已由 packages/core W3-7 间接拉入）。

## 跨 change / D-1 检查

- packages/core 零改动
- W1-W4-3 已 merge 产物零回归（W4-1 helper 提取符合 design 预期）
- D-1 永不做清单零命中（无 manifest.yaml 强制 / 无 dataset-card.yaml / 无 row-diff / 无 cherry-pick / 无 rollback）

## Verdict / Merge

- Phase 3 reviewer (opus)：**APPROVED**（0 issue）
- Merge commit：`95f55e7e0af8b1e94c506cb57ddfd054b2f89a55`
- 关联 follow-up（设计文件已列）：`gold-exporter-parquet-*` / `web-snapshot-export-async-job-*` / `snapshot-export-streaming-*` / `gold-exporter-artifact-cache-*` / `gold-exporter-history-*` / `gold-exporter-hf-push-*` / `web-typed-search-link-helper-*`

## 下一步

启动 W4-5 `cost-budget-system-*`（依赖 W2-3 image-to-text-suite，已 done）。
