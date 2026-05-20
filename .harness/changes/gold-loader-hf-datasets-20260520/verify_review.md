---
change_id: gold-loader-hf-datasets-20260520
phase: verify
status: approved
verdict: APPROVED
reviewed_at: 2026-05-21T09:00:00Z
reviewer: verify-reviewer-agent
model_used: opus
ac_kind_lint: enforce
---

# Verify Review：HF datasets exporter (W3-7) — APPROVED

**VERDICT：APPROVED**（0 SHOULD FIX / 0 MUST FIX；2 NICE TO HAVE，非阻塞）。

W3-7 是 Wave 3 收官 change。4 个 behavioral AC 全 PASS；全套 92 passed（88→92）；跨 change 回归 31 passed；真实 `datasets.load_from_disk` 双路径 roundtrip（5 行 + 空 snapshot）均通过；diff scope 严格限定在 design 允许范围；永不做清单 grep clean。DEV-1 经实测确认是满足 AC-3 严格 `column_names==[]` 的**唯一**可行实现，非过度工程。

## 1. 4 个 behavioral AC 执行

```bash
$ cd packages/core && uv run --with "pytest>=9" --with "pytest-asyncio>=0.23" --with "anyio" \
    python -m pytest tests/test_exporter_hf_datasets.py -v
```

输出：

```
collected 4 items
tests/test_exporter_hf_datasets.py::test_export_hf_datasets_roundtrip_happy PASSED [ 25%]
tests/test_exporter_hf_datasets.py::test_export_hf_datasets_result_fields PASSED [ 50%]
tests/test_exporter_hf_datasets.py::test_export_hf_datasets_empty PASSED [ 75%]
tests/test_exporter_hf_datasets.py::test_export_hf_datasets_rejects_malformed_jsonl PASSED [100%]
============================== 4 passed in 0.90s ===============================
```

| AC | kind | 验证点 | 结果 | PASS/FAIL |
|---|---|---|---|---|
| AC-1 | behavioral | 3 行 silver JSONL → `load_from_disk` 返 Dataset，len==3，"text" in column_names，ds[0]["text"]=="row0" | 1 passed | PASS |
| AC-2 | behavioral | row_count==3, "text" in column_names, dataset_info_path 存在且以 dataset_info.json 结尾, total_bytes>0 | 1 passed | PASS |
| AC-3 | behavioral | b"" → row_count==0, column_names==[], total_bytes>0, load_from_disk len==0 | 1 passed | PASS |
| AC-4 | behavioral | "not a json line\n" → ValueError 含 "非法 JSON 行" | 1 passed | PASS |

## 2. 全套回归（92 passed）

```bash
$ cd packages/core && uv run --with "pytest>=9" --with "pytest-asyncio>=0.23" --with "anyio" \
    python -m pytest tests/ -q
........................................................................ [ 78%]
....................                                                     [100%]
92 passed in 1.35s
```

88 → 92（+4 新增），符合预期。

## 3. 跨 change 回归（dataset_export + loaders + adapters）

```bash
$ cd packages/core && uv run ... python -m pytest \
    tests/test_dataset_export.py tests/test_loader_*.py tests/test_adapter_*.py -q
...............................                                          [100%]
31 passed in 0.34s
```

W2-6 silver export + W3-4/5/6 loaders + W3-1/2/3 adapters 全绿。

## 4. Diff 扫描

```bash
$ git diff main..change/gold-loader-hf-datasets-20260520 --stat
 .harness/changes/gold-loader-hf-datasets-20260520/design.md         | 130 +++
 .../implementation.md                                                |  83 ++
 .harness/changes/gold-loader-hf-datasets-20260520/summary.md         |  65 ++
 packages/core/pyproject.toml                                         |   1 +
 packages/core/src/dataplat_core/exporters/__init__.py                |  12 +
 packages/core/src/dataplat_core/exporters/hf_datasets.py             | 139 +++
 packages/core/tests/test_exporter_hf_datasets.py                     | 152 +++
 uv.lock                                                              | 1155 +++++++++++++++++++-
 8 files changed, 1734 insertions(+), 3 deletions(-)
```

确认改动仅限设计允许范围：

- 新增 `packages/core/src/dataplat_core/exporters/{__init__,hf_datasets}.py`
- 新增 `packages/core/tests/test_exporter_hf_datasets.py`
- `packages/core/pyproject.toml` 仅加一行 `"datasets>=2.14,<4"`（顶层 pyproject.toml 未动；pyarrow 未显式 pin，正确做法——pyarrow 是 datasets 强制间接依赖）
- `uv.lock` 链式更新（datasets/pyarrow/fsspec/huggingface_hub/dill/multiprocess 等）

不应出现的均**未出现**：

- `apps/api/*` 任何改动 — 无
- W1-* / W2-* / W3-1..6 已 merge 产物修改 — 无
- `packages/core/src/dataplat_core/{dataset.py, loaders/*, adapters/*, operators/*, protocols/*}` 任何改动 — 无
- 顶层 `/pyproject.toml` 改动 — 无（grep 验证无输出）

## 5. 永不做清单 grep

```bash
$ grep -RInE "manifest\.yaml|dataset-card\.yaml|row.?diff|cherry.?pick|rollback" \
    packages/core/src/dataplat_core/exporters/ \
    packages/core/tests/test_exporter_hf_datasets.py
clean
```

无 manifest.yaml / dataset-card.yaml / row diff / cherry pick / rollback 痕迹。`.harness/rules/data-not-code-pivot.md` D-1 永不做清单合规。

## 6. 不变量检查

### 6.1 `HfDatasetExportResult` Pydantic 模型

- BaseModel + `ConfigDict(extra="forbid")` — 符合
- 五字段全到：
  - `target_path: str` — 符合
  - `row_count: int = Field(ge=0)` — 符合
  - `column_names: list[str]` — 符合
  - `dataset_info_path: str` — 符合
  - `total_bytes: int = Field(ge=0)` — 符合

### 6.2 `export_to_hf_datasets` 函数签名

`async def export_to_hf_datasets(silver_blob_sha: SHA256, target_path: Path | str, store: BlobStore, *, split: str = "train") -> HfDatasetExportResult` — 与 design.md § 范围完全一致。`split` 关键字参数占位但未实际使用（注释明确说明），见 NICE-2。

### 6.3 步骤顺序（与 design.md § 范围一致）

1. `await store.get(silver_blob_sha)` + async iterator 兜底（与 W3-4 html_md 同模式）— OK
2. `decode("utf-8", errors="replace")` — OK
3. `splitlines()` + 空行跳过 + 每行 `json.loads` — OK
4. 坏行 `raise ValueError(f"silver snapshot 含非法 JSON 行 (line={idx}): ...")` fail-fast — OK，AC-4 命中
5. 非 dict 行也 raise（额外的防御性检查，超出 design 字面要求但语义合理，与 silver schema 一致） — OK
6. `Path(target_path).expanduser().resolve()` + `mkdir(parents=True, exist_ok=True)` — OK
7. 非空：`Dataset.from_list(rows).save_to_disk(str(target))` — OK
8. 空快照：`_write_empty_dataset_dir(target)` — 见 DEV-1 评估
9. `dataset_info.json` 存在性防御性 raise — OK
10. `total_bytes = sum(...rglob...)` — OK
11. 返 `HfDatasetExportResult(...)` — OK

### 6.4 `_write_empty_dataset_dir` 实现

读 `packages/core/src/dataplat_core/exporters/hf_datasets.py` L32-59：

- 用 `pa.ipc.new_stream(str(arrow_file), pa.schema([]))` 写空 Arrow IPC Stream（无 batch 写入）— OK
- 用 `DatasetInfo(features=Features({})).write_to_directory(...)` 写 `dataset_info.json` — OK，比手写 JSON 更安全（用 datasets 库本身的序列化）
- 手写 `state.json` 含 datasets 加载所需的 7 个字段（`_data_files / _fingerprint / _format_columns / _format_kwargs / _format_type / _output_all_columns / _split`）— OK

实测 `datasets.load_from_disk` 成功加载 0 行 0 列 Dataset（见 §8 真 roundtrip）。

### 6.5 `__init__.py` 导出

```python
from dataplat_core.exporters.hf_datasets import (
    HfDatasetExportResult, export_to_hf_datasets,
)
__all__ = ["HfDatasetExportResult", "export_to_hf_datasets"]
```

完整、合规、与 design 一致。

### 6.6 依赖检查

```bash
$ grep -E "datasets|pyarrow" packages/core/pyproject.toml
    "datasets>=2.14,<4",
```

仅 `datasets>=2.14,<4`。**未显式 pin pyarrow**，正确做法（pyarrow 由 datasets 间接拉入；DEV-2 ACCEPT）。

## 7. 隐式偏离审计

implementation.md 已声明 DEV-1（空快照特殊路径）+ DEV-2（pyarrow 直接 import），均经评估 ACCEPT。

verify 对照 design.md vs implementation.md vs git diff：

- 非 dict 行额外 raise：implementation.md 未显式列为 DEV，但在源码注释中说明，且 design.md § 范围 step 3 文字暗含（"每行 json.loads（坏行 → raise）"——非 dict 行也是坏数据）；不视为隐式偏离。
- 其余无隐式偏离。

## 8. DEV 评估

### DEV-1：空 snapshot 特殊路径 — **ACCEPT**（不是过度工程）

design.md 风险 3 预见 `from_list([])` 失败可能性，给出的回退方案是 `Dataset.from_dict({"text": []})`。sonnet 实际走了更深的方案（pyarrow IPC 空 Arrow + DatasetInfo + state.json）。verify 时实测了所有替代路径：

| 路径 | save_to_disk | load 后 column_names | 满足 AC-3 `column_names==[]` |
|---|---|---|---|
| `from_list([])` | SchemaInferenceError | — | 不满足（save fail） |
| `from_dict({})` | SchemaInferenceError | — | 不满足（save fail） |
| `from_list([], features=Features({}))` | SchemaInferenceError | — | 不满足（save fail） |
| `from_dict({"text": []})` | OK | `["text"]` | **不满足**（多出 text 列） |
| sonnet 手写空目录 | OK | `[]` | **满足** |

**结论**：sonnet 的实现不是过度工程，而是**满足 AC-3 严格断言 `column_names == []` 的唯一可行路径**。design.md 风险 3 给出的 `from_dict({"text": []})` 回退方案如果直接照搬，会导致 `column_names == ["text"]` 违反 AC-3。sonnet 在实施时自行升级了方案，且在 implementation.md DEV-1 明确记录、保留了 `_write_empty_dataset_dir` 函数级 docstring 说明原因。ACCEPT。

### DEV-2：pyarrow 顶层 import — **ACCEPT**

pyarrow 是 `datasets` 库的**强制运行时依赖**（datasets 内部顶层 `import pyarrow`），uv 通过 datasets 安装时必带入。`hf_datasets.py` 直接 `import pyarrow as pa` 不需在 pyproject.toml 额外 pin（design.md § 决策 3 也未要求显式 pin）。ACCEPT。

## 9. 真 `load_from_disk` 端到端 roundtrip（超越 stub）

verify 临时脚本：5 行非空 + 空 snapshot 两条路径分别 export → `datasets.load_from_disk` → 验证内容。

```
result.row_count: 5
result.column_names: ['text', 'images', 'source_ref', 'stats', 'lineage_ops']
result.total_bytes: 3065
dataset_info exists: True
ds len: 5
ds[0]: {'text': 'row 0', 'images': [], 'source_ref': {'blob_sha': 'aaaa...', 'loader': 'test', 'loader_version': '0'}, 'stats': {}, 'lineage_ops': []}
ds[4]: {'text': 'row 4', 'images': [], 'source_ref': {...}, ...}
---empty---
empty.row_count: 0
empty.column_names: []
empty.total_bytes: 362
empty ds len: 0
empty ds column_names: []
```

两条路径都通过真实 `datasets.load_from_disk`。SilverRow 5 字段（text/images/source_ref/stats/lineage_ops）在 HF Dataset 中以列形式呈现，与训练侧消费习惯一致。

## 10. 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

1. **NICE-1：`_write_empty_dataset_dir` 的 `_fingerprint` 是硬编码字符串 `"empty_silver_snapshot"`**。HF datasets 内部把 fingerprint 用于缓存键；多个空快照导出到不同 target_path 会共享同一 fingerprint，理论上未来若有"加载后做 transform 并缓存"流程可能产生缓存命中冲突。当前 W3-7 只 export+load 读，不做 transform，无影响。后续若用空 dataset 做 `.map(...)` 等操作，建议改为 `hashlib.sha256(str(target).encode()).hexdigest()[:16]` 或类似的目录指纹。followup 即可，不阻塞本 change。

2. **NICE-2：`split` 参数完全未用**（包括不写入 metadata）。design.md § 决策 10 已说明是"为 follow-up 留签名"，verify 接受。但当前函数体连 `_ = split` 都没有，pyright/ruff 严格模式下可能告警未使用参数；不影响功能。follow-up `gold-exporter-hf-multi-split-*` 时一并处理。

## 11. 永不做清单完整核查

- branch / merge / cherry-pick / rollback ：无
- row-level diff / record-level changeset ：无
- blob 派生图 / Asset / manifest.yaml / dataset-card.yaml ：无
- silver 文件树 / bronze 强 schema ：无（exporter 只读 silver blob，不强制 schema）

合规 D-1。

## Verdict

**APPROVED**

`gold-loader-hf-datasets-20260520` 无阻塞 issue，可 merge。两个 NICE TO HAVE 已记，留 follow-up 即可。

Wave 3 七个 change 至此全部 verify_approved，可推进至 merge → Wave 4 启动。

## 后续指引

- application-owner 把本 change merge 到 main，close 此 change；
- 在 `wiki/` 或 .harness 状态文件回填 Wave 3 完成；
- 启动 Wave 4（UI + 工程化），按 v3 mini-design 流程逐 change 推进。
- NICE-1 / NICE-2 不必单独开 follow-up change，未来 `gold-exporter-hf-multi-split-*` 时一并处理。
