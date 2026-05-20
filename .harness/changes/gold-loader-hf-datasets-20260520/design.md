---
change_id: gold-loader-hf-datasets-20260520
phase: design
status: approved
authored_at: 2026-05-21T07:00:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：HF datasets exporter (W3-7，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

新增 `packages/core/src/dataplat_core/exporters/hf_datasets.py`：`async export_to_hf_datasets(silver_blob_sha, target_path, store)`，把 W2-6 写出的 Silver snapshot JSONL blob 反序列化 + `Dataset.save_to_disk(target_path)` → 落 HuggingFace `datasets` library 兼容目录（Arrow + dataset_info.json），供 SFT / CPT 训练直接 `load_from_disk`。

## 背景

W2-6 落了 `serialize_rows_to_jsonl` + `export_silver_snapshot`：silver rows → JSONL bytes → CAS blob_sha；这是 silver 持久化的原语。

W3-7 是 Wave 3 收官 change，**消费** W2-6 输出（silver_blob_sha）→ 落地为 HF datasets 目录（dataset_info.json + state.json + data-*.arrow），让训练侧（HF `transformers` / `trl` / `peft`）直接 `load_from_disk(path)` 跑 SFT / DPO / CPT。

roadmap W3-7（北极星 §gold-layer）：

- 一句话目标：gold snapshot → HuggingFace `datasets` library 兼容格式（dataset_info.json + parquet/arrow shards）
- 范围：`packages/core/exporters/hf_datasets.py`
- 核心 AC：（behavioral）export 后用 `datasets.load_from_disk(path)` 能加载 + iterate；schema 含 text 列

参考实现：W2-6 dataset.py 的 `serialize_rows_to_jsonl` + BlobStore.get / put + `pydantic.BaseModel` 返回值结构。

新依赖：`datasets>=2.14,<4`（HuggingFace 官方 `datasets` 库），是 Wave 3 第二批 packages/core 业务依赖（继 W3-5 的 python-docx / python-pptx 之后）。`datasets` 间接拉入 `pyarrow` / `fsspec` / `huggingface_hub` / `dill` / `multiprocess`，体积较大（~100MB），但属于本 change 的**核心算子语义**——绕不开。

## 范围

In scope：

- `packages/core/src/dataplat_core/exporters/__init__.py`（新；空 module 加 `__all__ = ["HfDatasetExportResult", "export_to_hf_datasets"]`）
- `packages/core/src/dataplat_core/exporters/hf_datasets.py`（新）：
  - **schema**：
    - `HfDatasetExportResult(BaseModel)`：
      - `target_path: str`（resolved absolute path of dataset dir）
      - `row_count: int (ge=0)`
      - `column_names: list[str]`（按 dataset.column_names 顺序）
      - `dataset_info_path: str`（`<target_path>/dataset_info.json` 绝对路径）
      - `total_bytes: int (ge=0)`（target_path 下所有文件大小累加）
    - `model_config = ConfigDict(extra="forbid")`
  - **exporter 函数**：`async export_to_hf_datasets(silver_blob_sha: SHA256, target_path: Path | str, store: BlobStore, *, split: str = "train") -> HfDatasetExportResult`
    - 1) `payload_bytes = await store.get(silver_blob_sha)`；若 store 返回 async iterator → concat 成 bytes（与 W3-4 html_md 同模式）
    - 2) `text = payload_bytes.decode("utf-8", errors="replace")`
    - 3) 按行 `splitlines()`；空行跳过；每行 `json.loads(line)`；坏行 → raise `ValueError(f"silver snapshot 含非法 JSON 行 (line={idx})")`（与 jsonl loader 的"坏行跳过"不同——silver snapshot 是 CAS 保证完整的内部产物，坏行表示上游写入故障，必须抛）
    - 4) `dataset = datasets.Dataset.from_list(rows)` （空 list 也合法，HF 支持 0-row dataset）
    - 5) `target = Path(target_path).expanduser().resolve()`；目录存在则按 datasets 默认行为覆盖；不存在则 mkdir parents
    - 6) `dataset.save_to_disk(str(target))`（save_to_disk 是 sync 调用，async 函数里直接调；不嵌 thread pool——decision 5）
    - 7) `info_path = target / "dataset_info.json"`；如未生成则 raise ValueError（防御 datasets 库行为漂移）
    - 8) `total_bytes = sum(f.stat().st_size for f in target.rglob("*") if f.is_file())`
    - 9) 返 `HfDatasetExportResult(target_path=str(target), row_count=len(rows), column_names=list(dataset.column_names), dataset_info_path=str(info_path), total_bytes=total_bytes)`
    - `split` 参数当前仅作 metadata 占位（reserved for HF DatasetDict 多 split 场景；本 change 不实际多 split）
- `packages/core/pyproject.toml`（改）：dependencies 加 `datasets>=2.14,<4`
- `packages/core/tests/test_exporter_hf_datasets.py`（新）：4 个 behavioral 用例（stub BlobStore + tmp_path fixture）

Out of scope：

- **不**接 apps/api routes / orchestrator：留 follow-up `gold-exporter-hf-route-*`
- **不**写多 split（train/val/test 拆分）：留 follow-up `gold-exporter-hf-multi-split-*`；本 change `split` 参数仅占位
- **不**做远程 push 到 HuggingFace Hub：留 follow-up `gold-exporter-hf-push-*`
- **不**做 parquet 强制输出（HF datasets save_to_disk 默认 Arrow，性能足够；parquet shards 是 HF Hub 上传时才用）
- **不**做 schema 自动推断校验（让 datasets 库自己 infer；caller 负责 silver 一致性）
- **不**做 chunked / shard size 控制（小 dataset 单 shard 即可；多 shard 留 follow-up）
- **不**回收 / 删除已有 target_path（caller 负责清理；exporter 直接调 save_to_disk，由 datasets 库决定覆盖语义）
- **不**改 W2-6 dataset.py / W3-1..W3-6 任何产物
- **不**做 dataset-card.yaml / manifest.yaml（D-1 永不做清单）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | happy roundtrip：stub BlobStore 含 3 行 silver JSONL（每行 `{"text":"...","images":[],"source_ref":{...},"stats":{},"lineage_ops":[]}`）→ export_to_hf_datasets → target_path 目录含 dataset_info.json；`datasets.load_from_disk(target_path)` 返 Dataset，len(ds)==3，"text" in ds.column_names，ds[0]["text"] 等于原 row.text | `cd packages/core && uv run pytest tests/test_exporter_hf_datasets.py::test_export_hf_datasets_roundtrip_happy -x -q` | 1 passed |
| AC-2 | behavioral | HfDatasetExportResult 字段正确：返回值 row_count==3, "text" in column_names, dataset_info_path 以 dataset_info.json 结尾且文件存在, total_bytes > 0 | `cd packages/core && uv run pytest tests/test_exporter_hf_datasets.py::test_export_hf_datasets_result_fields -x -q` | 1 passed |
| AC-3 | behavioral | 空 silver snapshot（b""）→ export 仍成功，Dataset.load_from_disk 返回 len(ds)==0；HfDatasetExportResult.row_count==0；column_names==[]（HF 空 dataset 行为）；total_bytes > 0（dataset_info.json 自身有内容） | `cd packages/core && uv run pytest tests/test_exporter_hf_datasets.py::test_export_hf_datasets_empty -x -q` | 1 passed |
| AC-4 | behavioral | 坏行（非 JSON）→ raise ValueError 含 "非法 JSON 行" 子串；target_path 未被部分写入（防御性：要么完整成功要么干净失败）注：因 save_to_disk 仅在解析全部成功后才调用，所以 target 路径根本不会被 datasets 库写入，但若 caller 复用脏 dir，本 change 不擦 | `cd packages/core && uv run pytest tests/test_exporter_hf_datasets.py::test_export_hf_datasets_rejects_malformed_jsonl -x -q` | 1 passed |

## 决策

1. **新建 exporters/ 目录**：与 adapters/ loaders/ operators/ 同层级；W3-7 是第一个 exporter，未来 parquet / push-to-hub / 其他 gold 格式都落 exporters/ 子模块。W2-6 的 dataset.py 是 silver 持久化原语（JSONL → CAS），exporters/ 是 gold 派生（CAS → 训练格式），职责分明。
2. **消费 silver_blob_sha 而非直接传 rows**：W3-7 的上游是 W2-6 写出的 CAS blob；caller 用 `silver_blob_sha` 表达"这次导出基于哪个版本的 snapshot"，自然继承 CAS 不可变保证。直接传 rows 会绕过 CAS（caller 可能传入未持久化的 in-memory rows），破坏血缘。
3. **引入 `datasets>=2.14,<4`**：核心算子语义；`datasets.Dataset.from_list` + `save_to_disk` 是 HF 训练侧标准入口；自实现 Arrow / parquet shard 写入工作量大且易错。`datasets` 是业界事实标准 (HF 1k+ stars / SFT / DPO 训练全用)。版本下限 2.14 因为 `from_list` API 在 2.14+ 稳定；上限 <4 防 major 破裂。
4. **save_to_disk 默认 Arrow 而非 parquet**：roadmap 提到 "parquet shards"，但 HF `save_to_disk` 默认产 `data-00000-of-00001.arrow`，是 HF datasets 标准本地存储格式；`load_from_disk` 原生支持。parquet shards 是 HF Hub 上传专用，本地 disk 用 Arrow 性能更好且无需额外 codec 配置。如未来需要 parquet 走 `dataset.to_parquet(...)`，留 follow-up。
5. **save_to_disk 同步调用不嵌 thread pool**：HF datasets save_to_disk 内部已用 multiprocess + 分 shard 优化；从 asyncio 主线程直接调虽阻塞，但 export 任务本身就是粗粒度操作（不会跟其他 task 并发）；嵌 `loop.run_in_executor` 反而增复杂度无收益。caller 已通过 `asyncio.run(...)` 调本 exporter，整体仍是 fire-and-forget 模型。
6. **坏行 fail-fast（vs W3-6 jsonl loader 的 skip）**：silver snapshot 是 CAS 保证 + W2-6 引擎写出的内部产物，坏行表示**写入故障**，必须 caller 知情并处理（重新跑 recipe）。W3-6 jsonl loader 处理用户上传的 jsonl（外部数据），坏行是数据质量问题，skip 合理。两个 loader 语义不同。
7. **column_names 用 dataset.column_names 直接复用**：避免重复推断；HF 已按字段顺序排好。
8. **target_path 接受 Path | str**：caller 友好；内部统一 `Path(...).expanduser().resolve()`；不做 path safety 校验（caller 应保证 target_path 不指向系统目录）。
9. **不写 dataset_card.yaml / README.md**：D-1 永不做清单；HF datasets 库自己产 dataset_info.json + state.json，已是 metadata 完整集。
10. **split 参数占位**：reserved 给未来 multi-split；当前实现不实际使用（不写 DatasetDict）；保留参数让 caller 不需在 follow-up 时改签名。

## 风险

| 风险 | 缓解 |
|---|---|
| `datasets` 依赖巨大（~100MB 含 pyarrow / fsspec / huggingface_hub） | 接受：本 change 的核心语义即"导出 HF 兼容格式"，绕不开；packages/core 是后端 worker 依赖，非前端 bundle；CI 时间增量可接受 |
| HF datasets API 跨版本变化（`from_list` / `save_to_disk` 签名） | pin 范围 `>=2.14,<4`；CI 锁版本；本 change 只用最基础 API（Dataset.from_list + save_to_disk + load_from_disk），跨版本稳定 |
| `Dataset.from_list([])` 在某些版本不支持空 list | AC-3 显式验证；若版本不兼容，回退方案：`Dataset.from_dict({"text": []})` 显式空字典；sonnet 实现时若 from_list([]) 失败需调整 |
| save_to_disk 在 target_path 已存在 dataset 时的覆盖语义 | HF datasets 默认覆盖；caller 负责传干净的 target_path；out of scope 显式声明不擦旧目录 |
| 跨平台 path 处理（Windows / macOS 大小写敏感差异） | `Path(...).expanduser().resolve()` stdlib 处理；HF datasets 库内部跨平台已测；不需额外处理 |
| dataset.column_names 顺序在某些 schema 下不确定 | HF datasets 按首行字段顺序 infer；本 change AC-1 不断言 column_names 严格顺序，只 assert "text" in column_names |
| empty bytes (`b""`) → `splitlines()` → `[]` → `Dataset.from_list([])` 链路 | AC-3 验证；若 HF 空 dataset 不支持 save_to_disk，回退方案：写 stub dataset_info.json + 空 state.json 手工构造 |
| target_path 是相对路径 | `.resolve()` 转绝对；HfDatasetExportResult.target_path 始终是绝对路径 |
| pyproject.toml 新增依赖触发 uv sync 链式下载 | sonnet 实施时跑 `uv sync`；CI 缓存 .venv；首次安装 ~30-60s 可接受 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/dataset.py`（W2-6 SnapshotExportResult / serialize_rows_to_jsonl 参考；本 change 不 import）
  - `packages/core/src/dataplat_core/protocols/loader.py`（SilverRow schema）
  - `packages/core/src/dataplat_core/protocols/storage.py`（BlobStore Protocol）
  - `packages/core/src/dataplat_core/domain/types.py`（SHA256）
- 应当不动：
  - `apps/api/*`（全部不动）
  - W1-* / W2-* / W3-1..6 已 merge 产物
  - `packages/core/src/dataplat_core/loaders/*` / `adapters/*` / `operators/*`
- 引用的其他 change：W1-2（SilverRow）、W1-4（BlobStore Protocol）、W2-6（dataset_export_engine，上游 silver snapshot 写入方）、W3-6（loader-jsonl，类似的 jsonl 解析模式但 fail-fast 语义不同）

## 关联 follow-up

- `gold-exporter-hf-route-*`：apps/api 加 POST 触发 HF datasets export
- `gold-exporter-hf-multi-split-*`：train/val/test 多 split 拆分（split 参数实际生效）
- `gold-exporter-hf-push-*`：直接 push 到 HuggingFace Hub（非本地 disk）
- `gold-exporter-parquet-*`：纯 parquet shards 输出（不依赖 HF datasets save_to_disk）
- `silver-snapshot-streaming-export-*`：W2-6 大 dataset 流式优化（与 W3-7 大 dataset 加载关联）
