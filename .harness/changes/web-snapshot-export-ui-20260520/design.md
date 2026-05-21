---
change_id: web-snapshot-export-ui-20260520
phase: design
status: approved
authored_at: 2026-05-21T13:00:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：snapshot export UI + endpoint (W4-4，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

apps/api 新增 POST `/repos/{owner}/{name}/snapshots/{hash}/exports?format=hf_datasets` → 调 W3-7 `export_to_hf_datasets` 把 silver JSONL → HF datasets 目录 → tar.gz 流式返回；apps/web 新增 `/repos/$owner/$name/snapshots/$hash/export` 路由（folder form 子路由）让 user 选格式 + 触发下载。

## 背景

W3-7 落了 `packages/core/exporters/hf_datasets.py::export_to_hf_datasets` —— 把 silver JSONL blob → HF datasets 目录（dataset_info.json + Arrow shards）。但目前没有 apps/api endpoint 触发它；packages/core 单测覆盖 + W3-7 设计明确"apps/api routes 留 follow-up `gold-exporter-hf-route-*`"。

W4-4 就是那个 follow-up 的落地，并加上 UI 端的"选格式 + 下载"体验。roadmap W4-4 文本提到 parquet / jsonl / hf_datasets 三种格式 + zip 下载；本 change **只实现 hf_datasets**（W3-7 现成），parquet / jsonl 列入 follow-up（roadmap 提到不等于本 change 范围）。zip 改成 tar.gz（更原生 stdlib `tarfile`；浏览器 + linux 均支持解压；体积通常更小）。

为什么前后端在一个 change：本 change 的核心叙事是"user 在 UI 点导出，浏览器下载 tar.gz"——前端 + 后端是同一根因果链。W4-1 已先例 full-stack 单 change（apps/api snapshot rows endpoint + apps/web pdf-mineru 路由）。本 change 范围控制在 1 endpoint + 1 路由 + ~6 测试，与 W4-1 量级一致。

## 范围

In scope：

- `apps/api/dataplat_api/schemas/snapshot_export.py`（新）：
  - `SnapshotExportFormat = Literal["hf_datasets", "jsonl", "parquet"]`
  - `SnapshotExportTriggerBody(BaseModel)`：`format: SnapshotExportFormat`、`blob_sha: SHA256 | None = None`、`split: str = "train"`；`model_config = ConfigDict(extra="forbid")`
- `apps/api/dataplat_api/routers/snapshots.py`（改，+~90 行）：新增 `POST /{owner}/{name}/snapshots/{hash}/exports`：
  - body 解析 `SnapshotExportTriggerBody`；query `?format=` 也接受（body 优先）
  - format == `"jsonl"` → 422 `detail="format=jsonl 未实现；可直接 GET /repos/{owner}/{name}/blobs/{blob_sha} 获取原始 silver JSONL"` （为啥不实现：silver JSONL blob 本身就是 raw，下载已经可由 blob endpoint 完成；本 change 不重复封装）
  - format == `"parquet"` → 422 `detail="format=parquet 未实现；follow-up gold-exporter-parquet-*"`
  - format == `"hf_datasets"`：
    - visibility：`Depends(get_optional_user)` + `_resolve_repo(...)` 与 GET snapshot 同矩阵
    - `commit = await CommitService.get_with_tree(...)`；404 if not found
    - 解析 `blob_sha`：若 body 传则用；否则同 W4-1 row endpoint 模式找 `.jsonl` / `.jsonl.gz` 入口（0 或 ≥2 → 422，与 row endpoint 复用 `_resolve_silver_jsonl_blob_sha` helper 若存在，否则 inline 实现）
    - 创建临时目录 `tempfile.TemporaryDirectory()`；调 `await export_to_hf_datasets(blob_sha, tmp_dir, store, split=body.split)`
    - 把临时目录打包为 tar.gz（`tarfile.open(mode="w:gz")` 写到 `io.BytesIO`）
    - `StreamingResponse(BytesIO_bytes, media_type="application/gzip")` + `Content-Disposition: attachment; filename="snapshot-{hash[:12]}.tar.gz"` + custom headers `X-Snapshot-Row-Count`、`X-Snapshot-Blob-Sha`
- `apps/web/src/lib/api/queries.ts`（改，+~30 行）：新增 `useSnapshotExport()` mutation hook（`useMutation`），返回 `{ blob, headers }`；调用 `fetch` 而非 `fetchJson`（因为是 binary 流）
- `apps/web/src/routes/repos/$owner.$name/snapshots/$hash/export.tsx`（新；folder form 多级嵌套）—— **注意**：现有 `apps/web/src/routes/repos/$owner.$name.tsx` 是父路由（W4-2 已加 `<Outlet />`，可复用）；本 change 在 `routes/repos/$owner.$name/` 子目录下新增 `snapshots/$hash/export.tsx`（folder form 多级），URL = `/repos/$owner/$name/snapshots/$hash/export`
  - zod search schema：`format: "hf_datasets" | "jsonl" | "parquet"` (default `"hf_datasets"`)、`blobSha?: string`
  - state：mutation 进行中显示 spinner；完成后显示 row_count + 文件 size + 触发浏览器下载（`URL.createObjectURL(blob)` + a[download]）
  - format select：3 个选项；`jsonl` / `parquet` 显示 "(follow-up)" 标记；点导出时若 format 不是 hf_datasets → 直接显示 frontend 提示，不发 request
- `apps/web/src/routes/repos/$owner.$name.tsx`（小改）：tree entries 表 `.jsonl` 文件旁加 "导出" Link 指向新路由
- 测试：
  - `apps/api/tests/test_snapshot_export.py`（新，3 tests，env-gated 与 W4-1 同模式）：
    - happy hf_datasets：含 2 行 silver mock → POST 返 200 + tar.gz binary + headers
    - format jsonl → 422
    - snapshot 不存在 → 404
  - `apps/web/src/routes/repos/$owner.$name/snapshots/$hash/export.test.tsx`（新，2 tests，vi.mock pattern）：
    - 渲染 format select + 默认 hf_datasets
    - 点 "导出" → mutation 触发 + 显示 result panel（mock fetch 返 blob + headers）

Out of scope：

- **不**做 parquet 格式（留 follow-up `gold-exporter-parquet-*` + 配套 ui）
- **不**做 jsonl 格式（已能 GET /blobs/{sha}）
- **不**做 async job 模式（大 snapshot 可能超时；MVP 同步阻塞，user 等浏览器下载即可；W4-7 observability 后再做 async + 进度条 follow-up `web-snapshot-export-async-job-*`）
- **不**做 push 到 HuggingFace Hub（follow-up `gold-exporter-hf-push-*`）
- **不**做格式校验外的 schema 校验（前端 zod search schema 限制 format 枚举即可）
- **不**做 export 历史记录持久化（每次都是临时目录，无 audit log）：留 follow-up `gold-exporter-history-*`
- **不**改 W3-7 exporter 实现
- **不**做 playwright e2e（W4-6 + user final acceptance 验）
- **不**做 dataset-card.yaml / manifest.yaml（D-1）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | export endpoint 文件 + path 存在 | `grep -q '@router.post.*"/{owner}/{name}/snapshots/{hash}/exports"' apps/api/dataplat_api/routers/snapshots.py` | 命中 |
| AC-2 | behavioral | endpoint happy：DATAPLAT_* env 就位下 fixture 含 silver blob → POST format=hf_datasets → 200 + content-type=application/gzip + tar.gz bytes 解开含 dataset_info.json + state.json + .arrow file + X-Snapshot-Row-Count header == 2 | `cd apps/api && uv run pytest tests/test_snapshot_export.py::test_export_hf_datasets_happy -x -q` | 1 passed |
| AC-3 | behavioral | endpoint format=jsonl → 422 含 "未实现" 子串 | `cd apps/api && uv run pytest tests/test_snapshot_export.py::test_export_format_jsonl_returns_422 -x -q` | 1 passed |
| AC-4 | behavioral | UI 渲染：mock useSnapshotExport mutation，点"导出"按钮 → 调用 mutation + 显示 result panel 含 row_count | `cd apps/web && pnpm vitest run src/routes/repos/\$owner.\$name/snapshots/\$hash/export.test.tsx -t "triggers export"` | 1 passed |

## 决策

1. **format=hf_datasets 单一实现**：W3-7 现成；roadmap 列的另外两格式都有其他更好路径（jsonl 直接 blob GET；parquet 是独立 exporter follow-up），本 change 不重复造。
2. **tar.gz 而非 zip**：python stdlib `tarfile` 写 `w:gz` 比 zipfile 写 .zip 更原生（Arrow 二进制 + json 文件，gz 压缩率好）；浏览器解压能力 tar.gz 接近 .zip；用户 linux/mac 解压方便 `tar -xzf`；windows 用户用 7-zip 同等便利。
3. **同步阻塞 endpoint（无 async job 队列）**：MVP；W3-7 export_to_hf_datasets 是异步函数但内部 datasets.save_to_disk 是同步阻塞；典型 silver snapshot（几百行）秒级返回；大 snapshot OOM/超时由 caller 自决；async job 模式留 follow-up。
4. **tarball 全装内存返**：`io.BytesIO` + tarfile.write → 一次性 bytes → StreamingResponse；不真流式 chunked（python tarfile 流式 API 复杂；小 snapshot 内存 OK；大 snapshot follow-up `snapshot-export-streaming-*`）。
5. **路由 `/repos/$owner/$name/snapshots/$hash/export`**：放 repos namespace 下而非 `/snapshots/$owner/$name/$hash/export`（W4-2 是后者），因为 repo-scoped 操作 + 入口从 `repos/$owner.$name` 的 tree entries 跳过来更自然。folder form 多级 (`routes/repos/$owner.$name/snapshots/$hash/export.tsx`)；父路由 `$owner.$name.tsx` W4-2 已加 `<Outlet />`。
6. **blob_sha 自动解析复用 W4-1 模式**：与 row endpoint 同语义；找 .jsonl/.jsonl.gz 单一 entry；0 或 ≥2 → 422 with 具体 detail（"snapshot 含 N 个 jsonl entry，请显式传 blob_sha"）。
7. **响应 headers 加 `X-Snapshot-Row-Count` + `X-Snapshot-Blob-Sha`**：UI 拿到下载完成后读 header 显示给用户；不嵌在 binary 流前面（违反 HTTP 语义）。
8. **不持久化 export artifact**：每次 POST 都跑临时目录 + 立即 tar 完毁；不入 CAS、不入 DB。理由：silver_blob_sha 已不可变标识 source；HF dataset 输出是确定性派生（同 blob_sha → 同 tar），无需 cache；持久化引入 GC / 命名 / cleanup 复杂度。需要 cache 留 follow-up `gold-exporter-artifact-cache-*`。
9. **UI mutation 用 `useMutation`**：W4-1 / W4-2 都用 `useQuery`，但 export 是显式触发的 side effect，react-query mutation 语义贴；error/success 状态机现成；fetch 返 blob 用 `response.blob()`。
10. **format jsonl / parquet 在 UI 显示为 disabled + "(follow-up)"**：清晰告诉用户为何不能选；不直接隐藏选项（与 roadmap 三选项一致），方便后续 follow-up 直接开启。

## 风险

| 风险 | 缓解 |
|---|---|
| `export_to_hf_datasets` 在大 snapshot 上耗时 / OOM | MVP 接受；docstring + UI 提示"大 snapshot 可能超时，后续 W4-x async job 支持"；用户可拒绝长等待 |
| tarfile 内存爆（dataset 几 GB） | 与上同；follow-up 流式 |
| `tempfile.TemporaryDirectory` 在 server 失败（fs 满 / perm） | 错误冒泡到 500；现有 FastAPI exception handler 接管 |
| 浏览器下载大 binary 卡 UI | useMutation pending state + spinner；下载完成后浏览器原生处理 |
| Content-Disposition 文件名含 hash slice 与多 snapshot 同名冲突 | hash 前 12 字符冲突概率 < 2^-48；接受 |
| custom header `X-*` 跨域 CORS 不允许 expose | apps/web 与 apps/api 同 origin（dev/prod 都 reverse proxy）；CORS 不阻；如未来跨 origin 需要 `expose_headers` |
| W4-1 row endpoint 的 `_resolve_silver_jsonl_blob_sha` helper 已 inline 在 snapshots.py（私有函数）| 本 change 重用：若已是顶层函数 import 即可；若是 endpoint 内部嵌套，提取为 module-level helper 并被两 endpoint 共享 |
| HF datasets 库 transitive `datasets`+`pyarrow` 已在 packages/core，apps/api 通过 packages/core 间接拉入 | 无需新依赖；apps/api 已能 import |
| 跨 origin fetch 收不到 X-Snapshot-* header | 同 origin 不影响；CORS expose_headers 留 follow-up |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/exporters/hf_datasets.py`（W3-7 exporter，直接调用）
  - `packages/core/src/dataplat_core/protocols/storage.py`（BlobStore Protocol）
  - `apps/api/dataplat_api/services/commit.py`（get_with_tree，W1-1 复用）
  - `apps/web/src/routes/repos/$owner.$name.tsx`（W4-2 已加 Outlet 的父；增加 Preview rows 旁的"导出" Link）
  - `apps/api/dataplat_api/routers/snapshots.py` 中 W4-1 的 row endpoint 与 `_resolve_silver_jsonl_blob_sha` helper
- 应当不动：
  - `packages/core/*` 全部
  - W1-* / W2-* / W3-* / W4-1 / W4-2 / W4-3 已 merge 产物（W4-2 父路由 Outlet 已就位，本 change 只在 repos 子路由层挂载）
  - 既有 `routes/snapshots/$owner.$name.$hash.tsx`（W4-2 已改的；本 change 不动）
- 引用的其他 change：W3-7（exporter）、W4-1（endpoint + blob_sha 解析模式）、W4-2（Outlet + folder form 多级）

## 关联 follow-up

- `gold-exporter-parquet-*`：parquet shards exporter（packages/core + apps/api 同时落）
- `web-snapshot-export-async-job-*`：async job 队列 + 进度条 UI
- `snapshot-export-streaming-*`：tarball 流式 chunked encoding
- `gold-exporter-artifact-cache-*`：export 结果入 CAS 缓存 + 命中复用
- `gold-exporter-history-*`：export 历史记录（audit log + 可重新下载）
- `gold-exporter-hf-push-*`：直推 HuggingFace Hub（不下载到本地）
