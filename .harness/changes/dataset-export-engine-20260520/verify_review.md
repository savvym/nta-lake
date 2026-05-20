---
change_id: dataset-export-engine-20260520
phase: verify
status: approved
reviewer: opus-verify-agent
model_used: opus
authored_at: 2026-05-20T20:10:00Z
reviewed_at: 2026-05-20T20:10:00Z
head_commit: f4ea4a0
verdict: APPROVED
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（v3 mini-design，108 行）+ implementation.md（sonnet 端到端）+ `git diff main...change/dataset-export-engine-20260520` 验 PR。

## 输入

- **Design**：`.harness/changes/dataset-export-engine-20260520/design.md`（108 行，v3 mini-design）
- **Implementation**：`.harness/changes/dataset-export-engine-20260520/implementation.md`（sonnet 端到端，head_commit=44df71c → f4ea4a0 回填）
- **Branch**：`change/dataset-export-engine-20260520`
- **Commits**：`2865aee` (design) → `44df71c` (feat impl+test) → `f4ea4a0` (chore head_commit 回填)
- **PR**：n/a（gh PAT 缺 pr:write；本地 branch 合并）

## AC 对照表

reviewer 真跑 4 条 AC + 全量 pytest + diff 扫：

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL |
|---|---|---|---|---|
| AC-1 | behavioral | `cd packages/core && uv run pytest tests/test_dataset_export.py::test_serialize_rows_to_jsonl -x -q` | `1 passed in 0.09s` | PASS |
| AC-2 | behavioral | `cd packages/core && uv run pytest tests/test_dataset_export.py::test_export_silver_snapshot_writes_blob -x -q` | `1 passed in 0.09s` | PASS |
| AC-3 | behavioral | `cd packages/core && uv run pytest tests/test_dataset_export.py::test_export_silver_snapshot_sha256_matches -x -q` | `1 passed in 0.09s` | PASS |
| AC-4 | behavioral | `cd packages/core && uv run pytest tests/test_dataset_export.py::test_export_silver_snapshot_empty -x -q` | `1 passed in 0.09s` | PASS |
| 全量回归 | behavioral | `cd packages/core && uv run pytest -x -q` | `62 passed in 0.28s` | PASS（W1-1..W2-5 共 58 + W2-6 新增 4，0 regression）|

## 机械化检查日志

### 4 个 AC 命令完整输出

```text
$ cd packages/core && uv run pytest tests/test_dataset_export.py::test_serialize_rows_to_jsonl -x -q
.                                                                        [100%]
1 passed in 0.09s

$ cd packages/core && uv run pytest tests/test_dataset_export.py::test_export_silver_snapshot_writes_blob -x -q
.                                                                        [100%]
1 passed in 0.09s

$ cd packages/core && uv run pytest tests/test_dataset_export.py::test_export_silver_snapshot_sha256_matches -x -q
.                                                                        [100%]
1 passed in 0.09s

$ cd packages/core && uv run pytest tests/test_dataset_export.py::test_export_silver_snapshot_empty -x -q
.                                                                        [100%]
1 passed in 0.09s
```

### 全量 pytest 尾段

```text
$ cd packages/core && uv run pytest -x -q
..............................................................           [100%]
62 passed in 0.28s
```

基线 58（W1-1..W2-5 累计）+ 本 change 新增 4 = 62 ✓。无任何 regression。

### Pyright cd-into-module spot check

```text
$ cd packages/core && uv run pyright src/dataplat_core/dataset.py tests/test_dataset_export.py
0 errors, 0 warnings, 0 informations
```

dataset.py + test_dataset_export.py 静态检查 0/0/0 ✓。

### diff 范围扫描（reviewer 跑 `git diff main...HEAD --stat / --name-only`）

```text
$ git diff main...HEAD --name-only
.harness/changes/dataset-export-engine-20260520/design.md
.harness/changes/dataset-export-engine-20260520/design_review.md
.harness/changes/dataset-export-engine-20260520/implementation.md
.harness/changes/dataset-export-engine-20260520/summary.md
.harness/changes/dataset-export-engine-20260520/verify_review.md
packages/core/src/dataplat_core/dataset.py
packages/core/tests/test_dataset_export.py

$ git diff main...HEAD --stat
 .../dataset-export-engine-20260520/design.md       | 108 +++++++++++++
 .../design_review.md                               |  58 +++++++
 .../implementation.md                              | 100 ++++++++++++
 .../dataset-export-engine-20260520/summary.md      |  60 ++++++++
 .../verify_review.md                               |  81 ++++++++++
 packages/core/src/dataplat_core/dataset.py         |  66 ++++++++
 packages/core/tests/test_dataset_export.py         | 167 +++++++++++++++++++++
 7 files changed, 640 insertions(+)
```

新增文件 2 个（dataset.py + test_dataset_export.py） + harness 文档 5 个。范围严格符合 design.md In scope。

### Invariant 文件 0 改动核对（design.md "应当不动"清单）

```text
$ git diff main...HEAD -- \
    apps/api/ \
    packages/core/src/dataplat_core/recipe.py \
    packages/core/src/dataplat_core/operators/ \
    packages/core/src/dataplat_core/loaders/ \
    packages/core/src/dataplat_core/protocols/
(空输出 = 0 改动) ✓
```

- `apps/api/*`（含 MinioBlobStore）真实 0 改动 ✓
- W1-* / W2-1..W2-5 所有文件 0 改动（含 `recipe.py` / 各 Operator 实现 / `loaders/registry.py` / `protocols/*`）✓
- `operators/__init__.py` + `loaders/registry.py` 0 改动 ✓
- 本 change 仅新增 1 个 production 模块 (`dataset.py`) + 1 个 test 模块，无任何修改既有文件

### Schema / 关键不变量检查

```text
$ grep -E "extra=|Field\(|sha256|size_bytes|row_count|dataset_name|deduplicated|notes" \
    packages/core/src/dataplat_core/dataset.py
    model_config = ConfigDict(extra="forbid")
    sha256: SHA256
    size_bytes: int = Field(ge=0)
    row_count: int = Field(ge=0)
    dataset_name: str = Field(min_length=1)
    deduplicated: bool
    notes: str | None = None
    dataset_name: str,
    notes: str | None = None,
        sha256=put_result.sha256,
        size_bytes=put_result.size,
        row_count=len(rows),
        dataset_name=dataset_name,
        deduplicated=put_result.deduplicated,
        notes=notes,
```

| 不变量 | 期望（design.md） | 实际（dataset.py / test_dataset_export.py） | 结论 |
|---|---|---|---|
| `SnapshotExportResult` extra="forbid" | 必须 | dataset.py line 19 ✓ | PASS |
| `SnapshotExportResult.sha256` 类型 SHA256 | 必须 | line 21 ✓ | PASS |
| `SnapshotExportResult.size_bytes` Field(ge=0) | 必须 | line 22 ✓ | PASS |
| `SnapshotExportResult.row_count` Field(ge=0) | 必须 | line 23 ✓ | PASS |
| `SnapshotExportResult.dataset_name` Field(min_length=1) | 必须 | line 24 ✓ | PASS |
| `SnapshotExportResult.deduplicated` bool | 必须 | line 25 ✓ | PASS |
| `SnapshotExportResult.notes` str \| None = None | 必须 | line 26 ✓ | PASS |
| `serialize_rows_to_jsonl` 空 list → b"" | 必须 | line 36-37（`if not rows: return b""`）✓ | PASS |
| `serialize_rows_to_jsonl` 非空 = "".join(model_dump_json + "\n").encode("utf-8") | 必须 | line 38 ✓ | PASS |
| `export_silver_snapshot` 严格 4 步（serialize → BytesIO → store.put → SnapshotExportResult） | 必须 | line 52-66 严格按顺序 ✓ | PASS |
| `export_silver_snapshot` 是 async | 必须 | line 41 `async def` ✓ | PASS |
| `BlobStore.put` 调用传 `declared_size=len(payload)` | 必须 | line 57 ✓ | PASS |
| test stub `InMemoryBlobStore` 实现完整 BlobStore Protocol（5 个 async） | 必须 | test 文件 line 28-61：put/get/exists/get_size/delete 全 5 个 async ✓ | PASS |
| test 文件含 `isinstance(InMemoryBlobStore(), BlobStore)` runtime check | 必须 | line 65 ✓ | PASS |

### 永不做清单扫描（`.harness/rules/data-not-code-pivot.md`）

```text
$ grep -nE "branch|merge|cherry-?pick|rollback|row.?diff|Asset|manifest\.yaml" \
    packages/core/src/dataplat_core/dataset.py \
    packages/core/tests/test_dataset_export.py
(空输出 = 0 命中) ✓
```

本 change 不触碰 branch / merge / cherry-pick / rollback / row-diff / blob 派生图 / Asset / manifest.yaml / silver 文件树 / bronze 强 schema 任何一项 ✓。`export_silver_snapshot` 是纯的"行流 → CAS blob"原语，**不**做 silver/owner/name@ref 挂载（design.md 显式划入 W3 / W4），符合 design.md § Out of scope 与"永不做清单"双约束。

### 序列化与 4 步语义精读（design.md §serializer + §exporter vs dataset.py line 29-66）

| design 步骤 | dataset.py 行 | 结论 |
|---|---|---|
| serialize: 空 list → b"" | line 36-37 `if not rows: return b""` | ✓ |
| serialize: 非空 = 每行 model_dump_json + "\n"，join 后 encode("utf-8") | line 38 一行表达 ✓ | ✓ |
| serialize: 确定性（pydantic v2 model_dump_json 字段顺序稳定） | 隐式 ✓；AC-1 显式断言两次调用 bytes 严格相等 | ✓ |
| exporter step 1: `payload = serialize_rows_to_jsonl(rows)` | line 53 | ✓ |
| exporter step 2: `stream = io.BytesIO(payload)` | line 55 | ✓ |
| exporter step 3: `put_result = await store.put(stream, declared_size=len(payload))` | line 57 | ✓ |
| exporter step 4: 构造 `SnapshotExportResult(sha256=put_result.sha256, size_bytes=put_result.size, row_count=len(rows), dataset_name=dataset_name, deduplicated=put_result.deduplicated, notes=notes)` | line 59-66 | ✓ |

无任何步骤丢失 / 顺序错乱 / 额外步骤插入。

### test_dataset_export.py 精读

- `InMemoryBlobStore` stub（line 28-61）：
  - `put`：stream.read → sha256 → dedup 检查 → 返 BlobPutResult{sha256, size, storage_key, deduplicated}（完整模拟生产 CAS 语义）✓
  - `get` / `exists` / `get_size` / `delete`：5 个 async 全实现，符合 Protocol runtime check ✓
- `isinstance(InMemoryBlobStore(), BlobStore)` 守卫（line 65）：runtime_checkable Protocol 兜底，防 stub 漂移 ✓
- `_make_row` 辅助（line 73-80）：构造合规 SilverRow（含 source_ref / images=[] / stats={} / lineage_ops=[]）✓
- AC-1（line 88-108）：
  - 空 list → b"" ✓
  - 3 行 → split("\n") 后 4 元素，最后元素 "" 验 trailing newline ✓
  - 每行 json.loads == row.model_dump() ✓
  - 同输入两次调用 bytes 严格相等（确定性）✓
- AC-2（line 116-131）：
  - InMemoryBlobStore + 3 行 → 返 SnapshotExportResult
  - sha256 长度 64 + 全为 lowercase hex 字符 ✓
  - size_bytes > 0 / row_count == 3 / dataset_name == "silver-test" / deduplicated is False ✓
  - `await store.exists(result.sha256) is True`（blob 确实落到 store）✓
- AC-3（line 139-149）：
  - 本地计算 `hashlib.sha256(serialize_rows_to_jsonl(rows)).hexdigest()` == result.sha256 ✓
  - `result.size_bytes == len(serialized)` ✓
- AC-4（line 157-167）：
  - 空 rows → result.sha256 == `"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"`（sha256(b"")）✓
  - size_bytes == 0 / row_count == 0 ✓
  - `await store.exists(...) is True`（空 blob 仍写入）✓

## 隐式偏离审计

> reviewer 对照 design.md vs implementation.md vs git diff，列出 implementation.md § 偏离 没声明但实际发生的偏离。**隐式偏离 = MUST FIX**。

- **无隐式偏离**。implementation.md § 偏离 明确写"无偏离。严格按 design.md In scope 落地"，reviewer 全量 diff + 不变量精读后**确认**：
  - In scope 2 个 production/test 文件全部落地，无超范围
  - design.md "应当不动"清单（apps/api / W1-* / W2-1..W2-5 / recipe.py / Operator / Loader / Protocol）真实 0 改动（diff stat 验证）
  - schema / 不变量 14 项全部 PASS
  - exporter 4 步严格按 design 顺序，0 偏差
  - serializer 3 项要点（空 list → b""、JSONL+trailing \n、encode utf-8）全部到位
  - stub InMemoryBlobStore 实现完整 5 个 async 方法，符合 design.md § 决策 8 + § 风险 2 的"runtime_checkable + 最小子集"要求
- design.md § 决策 5 关于 caller 在 sync 上下文用 `asyncio.run(...)` 调用——本 change 不涉及 caller，无需在本 change 验证；W3 接入时再观察。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

> 完全可选；记入 follow-up change，不阻塞 merge。

- **`SnapshotExportResult` 缺 `created_at` 时间戳**：当前仅含 CAS 元数据（sha256/size_bytes/row_count/dataset_name/deduplicated/notes），无创建时间。W3 接入 silver-owner-name-ref tree entry 时可能需要时间戳支撑 list / sort 操作。design.md 未要求；可在 `silver-snapshot-repo-binding-*` follow-up 内一并处理（tree entry 自带 server-side `created_at`）。
- **`serialize_rows_to_jsonl` 大 dataset OOM 风险**：design.md § 风险 4 已显式 accept "v1 接受；follow-up `silver-snapshot-streaming-export-*` 改为 generator + 多 part upload"。当前 3 行小 dataset 测试 PASS；W3 接入真实百万行级 silver snapshot 时再切到 streaming 实现。
- **`export_silver_snapshot` 缺 schema fingerprint**：design.md § 关联 follow-up 已列 `silver-snapshot-schema-fingerprint-*`；SilverRow 字段集合演化时下游消费方需要识别 snapshot schema 版本。当前 SnapshotExportResult 不带 fingerprint，与 design 一致；W3-7 `gold-loader-hf-datasets-*` 消费前应补。

## Verdict

**APPROVED**

- 4 条 AC reviewer 真跑全 PASS（1 passed each）
- 全量回归 62/62 PASS（W1-1..W2-5 共 58 条 + W2-6 新 4 条；0 regression）
- pyright cd-into-module 0/0/0（dataset.py + test_dataset_export.py）
- diff 范围严格符合 design.md In scope：仅新增 `dataset.py` + `test_dataset_export.py` + 5 个 harness 文档；Invariant 文件（apps/api / W1-* / W2-1..W2-5 recipe.py / Operator / Loader / Protocol）真实 0 改动
- Schema / 不变量 14 项全部 PASS（extra="forbid" / SHA256 / Field(ge=0) ×2 / Field(min_length=1) / 字段齐全 / serialize 空 list 处理 / serialize join+encode / exporter 4 步顺序 / async / declared_size 透传 / stub 5 个 async / runtime_checkable 守卫）
- 永不做清单 0 触碰；exporter 是纯"行流 → CAS blob"原语，不挂 silver/owner/name@ref（W3 / W4 范围），与 W2-5 recipe.run_recipe_v2 职责分界清晰
- 隐式偏离 0；声明偏离 0；NICE TO HAVE 3 项全部非阻塞 follow-up

## 后续指引

1. **Application Owner 合并**：
   - `git checkout main && git merge --no-ff change/dataset-export-engine-20260520`
   - 把 verdict APPROVED 回填到 `summary.md`，归档 close
   - close TaskList #35 W2-6 Phase 3
2. **Wave 2 收官**：W2-1..W2-6 全部 APPROVED → Wave 2 核心算子链完成；可启 Wave 3（源覆盖 + 训练对接，#4）
3. **NICE TO HAVE 转 follow-up**：
   - `silver-snapshot-repo-binding-*`（W3 必做）：SnapshotExportResult.sha256 挂到 silver/owner/name@ref tree entry；同时补 `created_at`
   - `silver-snapshot-streaming-export-*`：generator + chunked upload；大 dataset 优化
   - `silver-snapshot-schema-fingerprint-*`：SilverRow 字段集合 hash → SnapshotExportResult 透传
4. **预告下游 / follow-up**（design.md § 关联 follow-up 已列）：
   - `gold-loader-hf-datasets-*`（W3-7）：消费 SnapshotExportResult.sha256 → HF datasets 格式
   - `silver-snapshot-parquet-*`：列存格式 + columnar predicate pushdown
