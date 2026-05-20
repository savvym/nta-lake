---
change_id: gold-loader-hf-datasets-20260520
phase: implementation
status: done
authored_at: 2026-05-21T08:00:00Z
author: implementer-agent
model_used: sonnet
branch: change/gold-loader-hf-datasets-20260520
---

# Implementation：HF datasets exporter (W3-7)

## 实施摘要

按 design.md 蓝图端到端实现 HF datasets exporter。新增 `exporters/` 子包（与 adapters/loaders/operators/ 同层），实现 `async export_to_hf_datasets(silver_blob_sha, target_path, store)` + `HfDatasetExportResult` Pydantic 模型。pyproject.toml 新增 `datasets>=2.14,<4` 依赖（实际安装 3.6.0）。4 个 behavioral 测试全部 PASS，全套 88 → 92 passed。

## 改动文件清单

| 路径 | 类型 | 说明 |
|---|---|---|
| `packages/core/src/dataplat_core/exporters/__init__.py` | new | module docstring + 导出 HfDatasetExportResult + export_to_hf_datasets |
| `packages/core/src/dataplat_core/exporters/hf_datasets.py` | new | HfDatasetExportResult model + export_to_hf_datasets async 函数 + _write_empty_dataset_dir 辅助 |
| `packages/core/tests/test_exporter_hf_datasets.py` | new | 4 behavioral 测试（AC-1..AC-4）+ inline _StubBlobStore |
| `packages/core/pyproject.toml` | edit | dependencies 加 `"datasets>=2.14,<4"` |
| `packages/core/uv.lock` | edit | uv sync 后自动更新 |

不动文件（设计规定）：`packages/core/src/dataplat_core/dataset.py` / `apps/api/*` / W1..W3-6 产物。

## 测试通过证据

### 单元测试（各 AC 独立跑）

```text
$ cd packages/core && uv run --with "pytest>=9" --with "pytest-asyncio>=0.23" --with "anyio" python -m pytest tests/test_exporter_hf_datasets.py::test_export_hf_datasets_roundtrip_happy -x -q
1 passed in 0.92s

$ ... tests/test_exporter_hf_datasets.py::test_export_hf_datasets_result_fields -x -q
1 passed in 0.90s

$ ... tests/test_exporter_hf_datasets.py::test_export_hf_datasets_empty -x -q
1 passed in 0.93s

$ ... tests/test_exporter_hf_datasets.py::test_export_hf_datasets_rejects_malformed_jsonl -x -q
1 passed in 0.91s
```

### 全套回归

```text
$ cd packages/core && uv run --with "pytest>=9" --with "pytest-asyncio>=0.23" --with "anyio" python -m pytest tests/ -q
92 passed in 1.33s
```

88 → 92（+4 新增测试）。

## 偏离 design.md（DEVIATIONS）

### DEV-1：AC-3 空 snapshot 特殊路径（datasets 3.x SchemaInferenceError workaround）

**原 design 期望实现**：`Dataset.from_list([])` → `save_to_disk()` 直接走标准路径。

**实际问题**：`datasets 3.6.0` 中 `Dataset.from_list([])` 可成功创建 0 行 Dataset，但调用 `save_to_disk` 时抛 `SchemaInferenceError: Please pass features or at least one example when writing data`——因为无任何行 / 无显式 features，Arrow writer 无法推断 schema。

**解决方案**：新增 `_write_empty_dataset_dir(target)` 辅助函数，使用 `pyarrow`（datasets 的间接依赖，已在 venv 中）直接写空 IPC Stream Arrow 文件（empty schema） + `DatasetInfo.write_to_directory()` 写 `dataset_info.json` + 手写 `state.json`。`datasets.load_from_disk(path)` 可成功加载 0 行 0 列 Dataset。

**对 AC-3 断言的影响**：无。`column_names==[]` 与 `row_count==0` 严格满足；`total_bytes > 0`（三个文件合计 ~400-500 字节）。

**设计依据**：design.md 风险 3 明确预计此风险，回退方案正是本路径。

### DEV-2：pyarrow 直接 import

实现中顶层导入 `pyarrow as pa` 与 `datasets.DatasetInfo`、`datasets.Features`。pyarrow 是 datasets 强制间接依赖，不需额外 pin。这是 DEV-1 的必然要求。

## 依赖新增

| 包 | 范围 | 实际安装版本 |
|---|---|---|
| `datasets` | `>=2.14,<4` | `3.6.0` |
| `pyarrow` | 间接（datasets 强制依赖） | 已随 datasets 安装 |

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 PR。
