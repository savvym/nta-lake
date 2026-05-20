---
change_id: adapter-jsonl-import-20260520
phase: design
status: approved
authored_at: 2026-05-21T04:05:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：jsonl import adapter (W3-3，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

新增 `JsonlImportAdapter` 到 `packages/core/src/dataplat_core/adapters/jsonl_import.py`，把"已上传 .jsonl 整文件"的 file refs 转 IngestResult（**单文件 spec**，整文件入 bronze，loader-jsonl 在 W3-6 拆行）。

## 背景

W3-1 / W3-2 已落 `RawFileUploadAdapter` / `FolderMdAssetsAdapter`，模板复用验证通过；W3-3 是第三个 refs-only adapter，覆盖**单文件 JSONL** 上传场景。

业务诉求（roadmap W3-3）："一份 1k 行 jsonl 上传，bronze 单 blob；后续 loader-jsonl 可读出 1k row"——明确决策**整文件存 bronze**，行级拆分由 loader 处理。本 adapter 仅做 refs → IngestResult，强制 path 以 `.jsonl` / `.jsonl.gz` 结尾，可选 `line_count` 元数据（loader-jsonl W3-6 用得上）。

与 W3-1 raw-upload 的差异：

- raw-upload 接受任意 (path, sha256)，无格式约束
- jsonl-import **强制单文件**且必须 `.jsonl` 或 `.jsonl.gz` 结尾
- 可选 `line_count` 字段透传到 `IngestResult.notes`（loader-jsonl 校验时用得上）

与 W3-2 folder-md-assets 的差异：

- folder-md-assets 强制至少 1 个 `.md` + 多文件 + path safety
- jsonl-import 强制**恰好 1 个**文件且 `.jsonl(.gz)` 后缀，不需 path safety（单文件 + path 校验通过 jsonschema minLength=1 + 内部 path != "" 检查即可）

## 范围

In scope：

- `packages/core/src/dataplat_core/adapters/jsonl_import.py`（新）：
  - class `JsonlImportAdapter`：name="jsonl-import" / version="0.1" / output_subtype="jsonl"
  - `input_schema`：files: [{path, sha256}] minItems=1 maxItems=1；可选 line_count: integer ≥0
  - `ingest(spec, workspace, ctx) -> IngestResult`：
    - pydantic 校验 spec（try/except 包成 ValueError 含 "JsonlImport spec 非法"）
    - 强制 `len(files) == 1`（pydantic schema 已约束 minItems/maxItems，但实现也再 assert 一次防 schema 漂移）
    - 强制 `path.lower().endswith((".jsonl", ".jsonl.gz"))`，否则 raise ValueError 含 **"path 必须以 .jsonl 或 .jsonl.gz 结尾"**
    - `line_count` 若提供，必须 ≥0；否则 raise ValueError 含 "line_count 非负"
    - 返回 `IngestResult(file_count=1, asset_count=0, files=[ref], notes=f"line_count={line_count}" if line_count is not None else None)`
- `packages/core/src/dataplat_core/adapters/__init__.py`（改）：
  - import + auto-register `JsonlImportAdapter`（try/except ValueError）
  - `__all__` 加 `"JsonlImportAdapter"`
- `packages/core/tests/test_adapter_jsonl_import.py`（新）：4 个 behavioral 用例

Out of scope：

- **不**实际读取 / 拆行 JSONL：loader-jsonl 在 W3-6 做
- **不**做 .json / .ndjson 别名（业界 ndjson 一般也叫 jsonl；若需要留 follow-up `adapter-jsonl-import-ndjson-alias-*`）
- **不**接 apps/api routes：留 follow-up
- **不**做 dataset-card.yaml / manifest.yaml（D-1 永不做清单）
- **不**改 SourceAdapter Protocol / 既有 adapter / registry

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | import dataplat_core.adapters 后 get_default().list_names() 含 "jsonl-import" | `cd packages/core && uv run pytest tests/test_adapter_jsonl_import.py::test_jsonl_import_auto_registered -x -q` | 1 passed |
| AC-2 | behavioral | happy path：spec={"files":[{"path":"data.jsonl","sha256":"a"*64}],"line_count":1000} → IngestResult.file_count==1, asset_count==0, files[0].path=="data.jsonl", notes=="line_count=1000" | `cd packages/core && uv run pytest tests/test_adapter_jsonl_import.py::test_jsonl_import_ingest_happy -x -q` | 1 passed |
| AC-3 | behavioral | 非 .jsonl 后缀（如 "data.csv"）→ raise ValueError 含 ".jsonl 或 .jsonl.gz" 子串 | `cd packages/core && uv run pytest tests/test_adapter_jsonl_import.py::test_jsonl_import_rejects_non_jsonl -x -q` | 1 passed |
| AC-4 | behavioral | files 数量 != 1（空 list 或 2 个）→ pydantic 校验失败，raise ValueError 含 "JsonlImport spec 非法" | `cd packages/core && uv run pytest tests/test_adapter_jsonl_import.py::test_jsonl_import_rejects_multi_files -x -q` | 1 passed |

## 决策

1. **按 W3-1 / W3-2 refs-only adapter 模板复制**：第三次复用同模式，证明模板已稳；后续 adapter（firecrawl / git-clone 等）应继续按此切口。
2. **整文件入 bronze**（不拆行）：roadmap W3-3 明确决策；拆行是 loader-jsonl (W3-6) 职责；adapter / loader 分层清晰。
3. **强制 maxItems=1**：jsonl-import 是"单文件" adapter 语义；多文件应走 raw-file-upload 或 folder-md-assets；强制约束让 caller 选 adapter 时有信息量。
4. **支持 .jsonl.gz**：训练数据集常用 gzip 压缩；loader-jsonl 后续负责解压；adapter 只看后缀；不引入 magic byte 校验。
5. **line_count 可选透传到 IngestResult.notes**：loader-jsonl 启动时可校验 "上传时声明 N 行 vs 实际解析 N 行"；用 notes 字符串而非新增字段（避免改 IngestResult schema 引发 W1-2 Protocol 调整）。
6. **input_schema 不加 path pattern .jsonl**：jsonschema regex 跨平台行为不一致；放代码里更可控（与 W3-2 同决策风格）。
7. **不做 ndjson 别名**：业界 ndjson/jsonl 同义；留 follow-up `adapter-jsonl-import-ndjson-alias-*`（如有用户反馈再加）。
8. **不做 dataset-card.yaml / manifest.yaml**：D-1 永不做清单；grep roadmap W3-3 段确认未提及 manifest。

## 风险

| 风险 | 缓解 |
|---|---|
| `.jsonl.gz` 误命中（如 "data.jsonl.gz.txt"）| `.endswith((".jsonl", ".jsonl.gz"))` 严格后缀匹配；"data.jsonl.gz.txt" 不会命中（因为 endswith ".txt"） |
| pydantic maxItems=1 在 W3-1 同类 schema 已工作；不应破裂 | sonnet 实现完 cd packages/core 跑全套测试；W3-1 + W3-2 共 8 个 adapter 测试应不受影响 |
| AdapterRegistry list_names 数量变化破坏既有测试 | 全部用 `name in names`（W3-1 / W3-2 已稳）；不会破裂 |
| line_count 序列化到 notes 字符串后 loader 难以解析 | 决策 5：notes 是 "line_count=N" 简单 KV；loader-jsonl 可 split + int()；若未来字段增多再改 |
| roadmap drift（W3-3 spec 含 manifest） | 已 grep roadmap.md W3-3 段：无 manifest 类 AC；决策 8 显式声明 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/adapter.py`（SourceAdapter Protocol / IngestFileRef / IngestResult）
  - `packages/core/src/dataplat_core/adapters/raw_upload.py`（模板参考）
  - `packages/core/src/dataplat_core/adapters/folder_md_assets.py`（模板参考）
  - `packages/core/src/dataplat_core/adapters/registry.py`（W3-1 已稳）
- 应当不动：
  - `apps/api/*`（全部不动）
  - W1-* / W2-* / W3-1 / W3-2 所有产物
- 引用的其他 change：W1-2（Adapter Protocol）、W3-1（AdapterRegistry）、W3-2（refs adapter 模板验证）

## 关联 follow-up

- `loader-jsonl-20260520`：W3-6 本 change 上游；bronze .jsonl blob → silver rows + line_count 校验
- `adapter-jsonl-import-route-*`：apps/api 加 `POST /repos/.../jsonl-import` 路由 + worker
- `adapter-jsonl-import-ndjson-alias-*`：接受 .ndjson 后缀
- `adapter-jsonl-import-magic-byte-*`：校验首字节是 `{` / gzip magic
