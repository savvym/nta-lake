---
change_id: dataset-export-engine-20260520
phase: design
status: approved
authored_at: 2026-05-21T01:50:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：dataset export engine (W2-6，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

落 `packages/core/src/dataplat_core/dataset.py`：`serialize_rows_to_jsonl()` + async `export_silver_snapshot()`，把 `RecipeRunResult.rows` 序列化为 JSONL 字节、按 sha256 PUT 进 BlobStore、返回 snapshot 元数据。

## 背景

W2-5 落了 `run_recipe_v2(recipe, ctx) -> RecipeRunResult{rows, total_input, total_output, loader_notes}`，是 in-memory 引擎。北极星 §silver-layer 要求 Silver snapshot 持久化到 CAS（sha256 寻址），让 W3 / W4 下游可按 blob_sha 拉取并按 owner/name@ref 在 repo 层挂载。

W2-6 的职责是**把 in-memory rows → CAS bytes**：

- **JSONL 序列化**：每行一个 `SilverRow.model_dump_json()`，末尾 `\n`；空 list → `b""`
- **CAS 写入**：`BlobStore.put(stream)` 是 W1-4 已有的 async 接口（apps/api MinioBlobStore；测试用 stub）
- **元数据返回**：sha256 / size_bytes / row_count / dataset_name / notes

repo 层挂载（silver/owner/name@ref → blob_sha）是 W3 / W4 范围，**本 change 不涉及**；本 change 是纯的"行流 → CAS blob"原语，与 recipe.py 同模块层 self-contained。

## 范围

In scope：

- `packages/core/src/dataplat_core/dataset.py`（新）：
  - **schema**：
    - `SnapshotExportResult(BaseModel)`：`sha256: SHA256`、`size_bytes: int (ge=0)`、`row_count: int (ge=0)`、`dataset_name: str (min_length=1)`、`deduplicated: bool`、`notes: str | None = None`
    - `model_config = ConfigDict(extra="forbid")`
  - **serializer**：`serialize_rows_to_jsonl(rows: list[SilverRow]) -> bytes`
    - 空 list → `b""`
    - 非空：每行 `row.model_dump_json()` + `"\n"`，全部 join 后 `.encode("utf-8")`
    - 确定性：同输入永远同 bytes（依赖 pydantic model_dump_json 稳定顺序）
  - **exporter**：`async export_silver_snapshot(rows: list[SilverRow], dataset_name: str, store: BlobStore, *, notes: str | None = None) -> SnapshotExportResult`
    - 1) `payload = serialize_rows_to_jsonl(rows)`
    - 2) `stream = io.BytesIO(payload)`
    - 3) `put_result = await store.put(stream, declared_size=len(payload))`
    - 4) 返 `SnapshotExportResult(sha256=put_result.sha256, size_bytes=put_result.size, row_count=len(rows), dataset_name=dataset_name, deduplicated=put_result.deduplicated, notes=notes)`
- `packages/core/tests/test_dataset_export.py`（新）：4 个 behavioral 用例

Out of scope：

- **不**接 repo refs / silver-owner-name-ref mapping：留 follow-up `silver-snapshot-repo-binding-*`
- **不**接 apps/api routers / orchestrator / worker：core engine 独立可测
- **不**接 `run_recipe_v2` 自动 export（caller 显式调）：保持单一职责；引擎组合留 W3 / API 接入
- **不**实现 schema fingerprint / dataset version 字段：留 follow-up `silver-snapshot-schema-fingerprint-*`
- **不**做 chunked / streaming upload：现有 BlobStore.put 接收 BinaryIO，本 change 直接 `io.BytesIO(payload)` 整块传；大 dataset 优化留 follow-up
- **不**改 W1-* / W2-1..W2-5 任何代码（含 recipe.py / Loader / Operator）
- **不**做 dataset 解读 / parse jsonl 回 SilverRow（loader 模式：未来 `gold-loader-hf-datasets` 才需）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | serialize_rows_to_jsonl 空 list → b""；3 row → 3 行 jsonl（每行结尾 \n）；每行 json.loads 后字段与原 row.model_dump 一致；同输入两次调用 bytes 严格相等 | `cd packages/core && uv run pytest tests/test_dataset_export.py::test_serialize_rows_to_jsonl -x -q` | 1 passed |
| AC-2 | behavioral | export_silver_snapshot end-to-end：stub InMemoryBlobStore（test 内 inline）+ 3 row → 返 SnapshotExportResult{sha256 长 64 hex, size_bytes>0, row_count==3, dataset_name=="silver-test", deduplicated==False}；store 内确实有该 blob | `cd packages/core && uv run pytest tests/test_dataset_export.py::test_export_silver_snapshot_writes_blob -x -q` | 1 passed |
| AC-3 | behavioral | export_silver_snapshot 一致性自检：返回的 sha256 == hashlib.sha256(serialize_rows_to_jsonl(rows)).hexdigest()；size_bytes == len(serialized_bytes) | `cd packages/core && uv run pytest tests/test_dataset_export.py::test_export_silver_snapshot_sha256_matches -x -q` | 1 passed |
| AC-4 | behavioral | export_silver_snapshot 空 rows：返 SnapshotExportResult{sha256 == sha256(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", size_bytes==0, row_count==0}；BlobStore.put 仍被调（空 blob 也允许写入） | `cd packages/core && uv run pytest tests/test_dataset_export.py::test_export_silver_snapshot_empty -x -q` | 1 passed |

## 决策

1. **core-only，不接 repo / API**：与 W2-5 同模式；silver-owner-name-ref 挂载是 repo 服务的职责，跨模块；留 follow-up。
2. **JSONL 而非 Parquet/Arrow**：训练数据通用格式；HuggingFace datasets / streamloader 直接消费；schema-free 兼容 SilverRow 演化；Parquet 列存留 follow-up（`silver-snapshot-parquet-*`）。
3. **每行 model_dump_json + "\n"，空 list → b""**：标准 JSONL 约定；不写 trailing newline 时空文件确定性。
4. **使用 BlobStore Protocol（W1-4 抽象），不直接调 MinioBlobStore**：core 不依赖 apps/api；测试用 stub；与 Loader/Operator 同抽象层级。
5. **async exporter**：BlobStore.put 是 async，exporter 顺承；与 recipe.run_recipe_v2 同步的差异是：recipe 是纯计算，export 是 I/O，async 自然。caller 在 sync 上下文用 `asyncio.run(export_silver_snapshot(...))` 调（与 PdfMineruLoader 内部模式对齐）。
6. **SnapshotExportResult 暴露 deduplicated 标志**：BlobPutResult 已有；exporter 透传；caller 可识别是否同字节内容已存在。
7. **不在 v1 加 dataset_name 字符校验**：min_length=1 即可；filename-safe 限制由 caller / repo 层负责（W3 接入时）。
8. **stub InMemoryBlobStore 测试 fixture**：test 文件内 inline 定义，实现 `put / get / exists / get_size / delete` 全 5 个 async 方法（满足 runtime_checkable Protocol）；不污染 production 任何 registry（BlobStore 无 registry，每次实例化）。

## 风险

| 风险 | 缓解 |
|---|---|
| pydantic model_dump_json 顺序不稳定导致 sha256 漂移 | pydantic v2 `model_dump_json` 按字段声明顺序稳定输出（已有 W1-2 SilverRow 模型固定字段顺序）；AC-1 显式断言"同输入两次调用 bytes 严格相等" |
| stub InMemoryBlobStore 不严格遵循 BlobStore Protocol → 测试虚假通过 | test fixture 用 `assert isinstance(store, BlobStore)`（runtime_checkable）；put 须流式读 stream + sha256 + dedup 检查（最小子集实现） |
| BlobStore.put 接收 BinaryIO；io.BytesIO 是 BinaryIO 子类 → 兼容 | Python 标准库保证；不需运行时检查 |
| 大 dataset（百万行）整块加载到内存 → OOM | v1 接受；follow-up `silver-snapshot-streaming-export-*` 改为 generator + 多 part upload；本 change AC-1 用 3 行小 dataset 不触发 |
| 空 rows 也写 blob（sha256 e3b0...）→ 是否合理 | 视为 feature：空 dataset 也是合法 snapshot，caller 显式调即显式表达"导出空集"；AC-4 验证此语义 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/recipe.py`（W2-5 RecipeRunResult.rows 是上游输入；不强依赖，函数签名直接接 `list[SilverRow]`）
  - `packages/core/src/dataplat_core/protocols/loader.py`（SilverRow / LoadResult）
  - `packages/core/src/dataplat_core/protocols/storage.py`（BlobStore Protocol / BlobPutResult）
  - `packages/core/src/dataplat_core/domain/types.py`（SHA256 type alias）
- 应当不动：
  - W1-* / W2-1..W2-5 所有文件（含 recipe.py / Operator / Loader / Protocol）
  - `apps/api/*`（含 MinioBlobStore）
- 引用的其他 change：W1-2（SilverRow）、W1-4（BlobStore Protocol）、W2-5（RecipeRunResult，但本 change 不直接 import）

## 关联 follow-up

- `silver-snapshot-repo-binding-*`：把 SnapshotExportResult.sha256 挂到 silver/owner/name@ref tree entry
- `silver-snapshot-parquet-*`：列存格式 + columnar predicate pushdown
- `silver-snapshot-streaming-export-*`：generator + chunked upload；大 dataset 优化
- `silver-snapshot-schema-fingerprint-*`：dataset metadata 加 schema 指纹（SilverRow 字段集合 hash）
- `gold-loader-hf-datasets-*`（W3-7）：消费 SnapshotExportResult.sha256 → HF datasets 格式（jsonl → Dataset.from_json）
