---
change_id: web-pdf-mineru-ui-v2-20260520
phase: design
status: approved
authored_at: 2026-05-21T09:30:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：Web PDF→silver row UI v2 (W4-1，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

apps/api 加 `GET /repos/{owner}/{name}/snapshots/{hash}/rows?offset=&limit=` 暴露 silver snapshot 行数据；apps/web 加新路由 `/repos/$owner/$name/pdf-mineru` 提供 PDF 上传 → 跑 pdf_mineru 流水线 → 展示 silver row 表格（替代老的 markdown blob 渲染）。

## 背景

Wave 3 收官（17/27 done）；packages/core 已具备 PdfMineruLoader（W1-4）+ silver snapshot export（W2-6）+ HF datasets exporter（W3-7）；但 apps/api 没有暴露 silver row 的 endpoint，apps/web 也只能通过老的 blob viewer 看 markdown 字符串，看不到 SilverRow 结构（text / images / source_ref / stats / lineage_ops）。

W4-1 是 Wave 4 第一个 change，主线是"用户能在 UI 上看到新模型的核心数据形态"，为 W4-2（通用 row preview）+ W4-3（chain builder）打基础。

`apps/api/dataplat_api/routers/snapshots.py` 已有 GET /{owner}/{name}/snapshots/{hash}（返回 SnapshotRead 元数据）；本 change 加 sibling endpoint 返回 row 数据。

`apps/web/src/routes/repos/$owner.$name.tsx` 已有 ingest + pipelines tab + useEnqueueIngest + useCreatePipelineRun + usePipelineRun hooks 复用。

参考实现：W2-6 `serialize_rows_to_jsonl` 反向；apps/api/routers/snapshots.py 现有 `_resolve_repo` + visibility 矩阵；apps/web/src/lib/api/queries.ts useSnapshot 模板。

## 范围

In scope：

- **Backend** `apps/api/dataplat_api/routers/snapshots.py`（改）：
  - 新增 `GET /{owner}/{name}/snapshots/{hash}/rows`：
    - Auth：`get_optional_user`（与 GET snapshot 一致）+ `_resolve_repo` visibility 过滤
    - Query 参数：`offset: int = 0 (ge=0)`，`limit: int = 50 (ge=1, le=500)`，`blob_sha: str | None = None`（可选；不传则从 snapshot tree 自动找唯一 `.jsonl` entry）
    - 行为：
      - 1) `_resolve_repo` + `CommitService.get_with_tree` 拿 snapshot（404 if 不存在）
      - 2) 解析 blob_sha：若传入 → 用之；否则展开 root tree → 找路径以 `.jsonl` 结尾的 entry（不区分大小写）：
        - 0 个 → 422 `silver_snapshot_no_jsonl_entry`
        - 多个 → 422 `silver_snapshot_ambiguous_blob_sha; pass ?blob_sha=`
        - 1 个 → 取其 sha256
      - 3) `store.get(blob_sha)` 读 bytes（async iterator 时 concat 成 bytes，与 W3-4 同模式）；404 if blob 不存在
      - 4) `text = bytes.decode("utf-8", errors="replace")`；按 `splitlines()` 拆；空行跳过；每非空行 `SilverRow.model_validate_json(line)`
      - 5) total = len(rows)；按 offset/limit slice 返回
    - 返回 `SnapshotRowsResponse(rows: list[SilverRowRead], total: int, offset: int, limit: int, blob_sha: str)`
  - 新增 schema `apps/api/dataplat_api/schemas/snapshot_rows.py`：
    - `SilverRowRead(BaseModel)`：与 SilverRow 等价的薄包装（text / images / source_ref / stats / lineage_ops），`extra="forbid"`
    - `SnapshotRowsResponse(BaseModel)`：rows / total / offset / limit / blob_sha
- **Frontend** `apps/web/src/lib/api/queries.ts`（改）：
  - 新增 `useSnapshotRows(owner, name, hash, opts: { offset, limit, blobSha? })` hook（与 useSnapshot 同模式；queryKey 含分页）
- **Frontend** `apps/web/src/routes/repos/$owner.$name.pdf-mineru.tsx`（新；flat-dot 子路由）：
  - URL search schema（zod）：`{ snapshot?: string, offset?: number, limit?: number, blobSha?: string }`，默认 offset=0/limit=50
  - 组件分 3 区：
    - **(1) 上传区**：复用 `useUploadBlob` + `useEnqueueIngest`（adapter="raw-upload"）；上传后 toast 显示 blob_sha
    - **(2) 流水线区**：固定 yaml fixture（pdf_mineru 单步）；按钮"跑 pdf_mineru on 上次 ingest"；调 `useCreatePipelineRun` + 轮询 `usePipelineRun`；完成后取 `pipeline_run.snapshot_hash` 写入 URL `?snapshot=`
    - **(3) 行展示区**：`?snapshot=` 存在时调 `useSnapshotRows`；渲染基础 `<table>`（无 react-virtual，行虚拟化留 W4-2）：列 `#` / `text` (truncate 200 字符 + "…") / `[详情]` 按钮；点行 → 下方/右侧 `<pre>` 展示完整 row JSON（包含 source_ref / stats / lineage_ops）；上下页按钮（offset ± limit）
- **Tests Backend** `apps/api/dataplat_api/tests/routers/test_snapshot_rows.py`（新）：4 个 behavioral（happy 分页 / 404 snapshot / 422 no-jsonl / 422 ambiguous）
- **Tests Frontend** `apps/web/src/routes/repos/$owner.$name.pdf-mineru.test.tsx`（新）：2 个 vitest+RTL（与现有 repos.tabs.test.tsx 同模式 `vi.mock("../lib/api/queries", ...)`）：route 渲染 3 行表格 / 点行展开详情

Out of scope：

- **不**做行虚拟化（react-virtual / @tanstack/react-virtual）：W4-2 做
- **不**做通用 row preview 路由 `/snapshots/$hash/rows`：W4-2 做
- **不**新接 pdf_mineru recipe yaml fixture 复杂场景（多步 chain）：W4-3 做
- **不**做实时 websocket 推送 job 状态：留 follow-up `web-jobs-ws-*`
- **不**做导出按钮（HF datasets / parquet 导出）：W4-4 做
- **不**做 silver snapshot 流式读取（whole blob 一次性 decode + parse）：留 follow-up `loader-async-stream-protocol-*`
- **不**改 W1-4 / W2-6 / W3-7 已 merge 产物；**不**改其他 routers（仅 snapshots.py 加 endpoint）
- **不**做 schema 自动 infer 校验（SilverRow 由 W1-2 已固定）
- **不**做 manifest.yaml（D-1 永不做清单）
- **不**做"真浏览器跑通"自动化（playwright 由 W4-6 integration-test-framework 引入）；本 change 只跑 vitest+RTL 组件级

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | Backend happy：admin 用户先 POST 创建含 3 行 silver JSONL 的 snapshot（tree 含 1 个 `data.jsonl` entry）→ GET /repos/{o}/{n}/snapshots/{h}/rows?offset=0&limit=2 → 200 + rows=2 + total=3 + offset=0 + limit=2 + blob_sha 是该 entry 的 sha256；rows[0].text == 原 row 1 text | `cd apps/api && uv run pytest dataplat_api/tests/routers/test_snapshot_rows.py::test_rows_happy_paginated -x -q` | 1 passed |
| AC-2 | behavioral | Backend 404：GET 不存在的 snapshot hash → 404 detail 含 "Snapshot" + "不存在" | `cd apps/api && uv run pytest dataplat_api/tests/routers/test_snapshot_rows.py::test_rows_snapshot_not_found -x -q` | 1 passed |
| AC-3 | behavioral | Backend 422：snapshot tree 无 `.jsonl` entry → 422 detail 含 "no_jsonl_entry"；snapshot tree 有 ≥2 个 `.jsonl` entry 且未传 blob_sha → 422 detail 含 "ambiguous_blob_sha" | `cd apps/api && uv run pytest "dataplat_api/tests/routers/test_snapshot_rows.py::test_rows_jsonl_resolution_errors" -x -q` | 1 passed |
| AC-4 | behavioral | Frontend：vitest+RTL；`vi.mock("../lib/api/queries", ...)` 让 useSnapshotRows 返回 3 行；render router with memory history at `/repos/o/n/pdf-mineru?snapshot=<64 hex>` → 表格 ≥3 行可见；点第 1 行 [详情] → 详情面板含 "source_ref" 字符串 | `cd apps/web && pnpm test -- src/routes/repos/\$owner.\$name.pdf-mineru.test.tsx` | tests pass |

## 决策

1. **rows endpoint 挂 snapshots.py**：与现有 GET snapshot 同 prefix `/repos/{o}/{n}/snapshots/{h}`；保留 visibility 矩阵（`get_optional_user` + `_resolve_repo`）；不新建独立 router。
2. **endpoint 路径 `/rows` 后缀而非 `/silver-rows`**：silver 是层级概念，rows 是数据形态；snapshot 只有 silver/gold 行级语义，行就是行；后续 gold rows 同 endpoint 复用（gold snapshot 也走 JSONL → rows 反序列化）。
3. **blob_sha 自动找 .jsonl entry vs 强制 caller 传**：默认 auto（90% 单 .jsonl 场景）；多个 / 0 个走 422 提示；caller 可显式传 `?blob_sha=` 绕过启发式。降低 caller 心智负担。
4. **rows endpoint 加载整 blob 入内存**：MVP；W2-6 写入也是一次性 bytes；流式留 follow-up；分页是 offset/limit slice 已 deserialize 的 list（不能下沉到 disk-level 因为 JSONL 行分隔需扫描）。
5. **SilverRowRead 薄 schema vs 直接 SilverRow**：保持 apps/api schema 层独立（与 dataplat_core domain 解耦）；字段一一对应；extra="forbid"；避免 packages/core schema 变动直接破坏 OpenAPI。
6. **flat-dot 路由 `repos.$owner.$name.pdf-mineru.tsx`**：与现有 `repos/$owner.$name.tsx` 同级；TanStack 自动嵌套；记忆中 [feedback_tanstack_routing_folder_form](folder form 硬约束) 适用于 index+$param 共存场景，本路径不冲突。
7. **不做 react-virtual**：W4-2 通用 row preview 需要 ≥100 行不卡顿才上虚拟化；W4-1 PDF 单文档典型 ≤50 silver row（每页 1 row）；offset/limit 分页足够。
8. **frontend AC 走 MSW**：不依赖真 backend；apps/web 现有测试都是 vitest+RTL+MSW pattern（参考 repos.tabs.test.tsx / repos.ingest-section.test.tsx）；保持一致。
9. **不做 playwright e2e**：W4-6 integration-test-framework 才引入；本 change 仅组件级；UI 真跑由 user final acceptance 验。
10. **错误码 422 而非 400**：FastAPI 默认 422 = validation error；snapshot 结构不符合"含恰好 1 个 .jsonl"是 caller-correctable validation 性质，沿用 422。

## 风险

| 风险 | 缓解 |
|---|---|
| BlobStore.get 返回 AsyncIterator vs bytes Protocol drift（W3-4..W3-7 已知噪音） | concat pattern 与 W3-4 一致；pyright workspace-root 噪音忽略；cd packages/core / apps/api clean |
| 大 silver snapshot（GB 级）OOM | 决策 4 + 风险接受：MVP；caller 通过 `limit` 控制 response size，但 deserialize 仍 full；流式留 follow-up |
| SilverRow.model_validate_json 在 schema 漂移时抛 ValidationError | 整个 endpoint 抛 500（FastAPI 默认）；后续可加 try/except 转 422 with 行号；MVP 不做 |
| TanStack flat-dot 路由解析冲突（已知 memory：index+$param 共存须 folder form） | 本路径只新增 `repos.$owner.$name.pdf-mineru.tsx`，与现有 `repos/$owner.$name.tsx` 不构成 index+$param 冲突；如 sonnet 跑测试时报路由 ambiguous → fallback 改 folder form |
| useSnapshotRows queryKey 变化导致刷新闪烁 | queryKey 含 offset/limit；offset 切换会触发 refetch，但 react-query 默认 keepPreviousData 不强制开；MVP 不开（闪烁可接受），优化留 follow-up |
| MSW mock 与真 backend response shape 漂移 | AC-1 backend pytest 验真 shape；AC-4 frontend mock 用同 shape；schema 都从 SilverRowRead pydantic 模型生成；后续 generated.ts 自动同步 |
| pipeline run 完成后 snapshot_hash 拿不到（pipelines schema 不暴露） | 看现 PipelineRunResponse；本 change 假设 `snapshot_hash` 字段存在；若不存在则降级：UI 给用户手填 snapshot hash 输入框 + jump 按钮，rows 展示部分仍可独立工作 |
| 老 markdown blob viewer 路由（blob/$owner/$name/$hash）保留 | 不动；W4-1 是新增 pdf-mineru 路由，不删老 viewer；新老并存 |
| pyproject.toml 不变 | apps/api 已有 pydantic / fastapi；apps/web 已有 zod / @tanstack/react-query / msw；本 change 不引依赖 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/loader.py`（SilverRow schema；本 endpoint 反序列化目标）
  - `packages/core/src/dataplat_core/dataset.py`（W2-6 serialize 配对，反向参考）
  - `packages/core/src/dataplat_core/protocols/storage.py`（BlobStore Protocol）
  - `apps/api/dataplat_api/routers/snapshots.py`（仅在末尾加新 endpoint）
  - `apps/api/dataplat_api/services/commit.py`（CommitService.get_with_tree 复用）
  - `apps/api/dataplat_api/storage.py`（get_blob_store DI）
  - `apps/web/src/lib/api/queries.ts`（useSnapshot 模板）
  - `apps/web/src/routes/repos/$owner.$name.tsx`（ingest / pipelines tab 模板）
- 应当不动：
  - W1-* / W2-* / W3-* 已 merge 产物
  - `apps/web/src/routes/blob.$owner.$name.$hash.tsx`（老 markdown viewer 保留共存）
  - `apps/web/src/routes/snapshots/$owner.$name.$hash.tsx`（metadata viewer 不动）
- 引用的其他 change：W1-2（Loader Protocol / SilverRow）、W1-4（BlobStore Protocol / PdfMineruLoader 上游）、W2-6（dataset_export_engine，silver JSONL 写入方）、W2-5（recipe yaml v2 / pipeline run 调度）

## 关联 follow-up

- `web-pdf-mineru-ui-v2-stream-*`：流式 rows endpoint（与 silver-snapshot-streaming-export-* 关联）
- `web-jobs-ws-*`：websocket 实时推送 job 状态（替代轮询）
- `web-rows-virtualization-*`：@tanstack/react-virtual 上虚拟化（W4-2 实际落地）
- `web-pdf-mineru-chain-multi-*`：多步 chain（pdf_mineru → chunker → image_to_text）UI（W4-3 关联）
- `apps-api-snapshot-rows-error-detail-*`：rows endpoint 422 加结构化 error code + 行号 + 字段名
