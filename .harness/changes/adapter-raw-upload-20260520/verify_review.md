---
change_id: adapter-raw-upload-20260520
phase: verify
status: approved
reviewer: opus-verify-agent
model_used: opus
authored_at: 2026-05-20T20:30:00Z
reviewed_at: 2026-05-20T20:30:00Z
head_commit: ea72428
verdict: APPROVED
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（v3 mini-design，115 行）+ implementation.md（sonnet 端到端）+ `git diff main...change/adapter-raw-upload-20260520` 验 PR。

## 输入

- **Design**：`.harness/changes/adapter-raw-upload-20260520/design.md`（115 行，v3 mini-design；application-owner 自写，不 spawn Phase 1 reviewer，符合 D-13）
- **Implementation**：`.harness/changes/adapter-raw-upload-20260520/implementation.md`（sonnet 端到端；声明 0 偏离 / 4/4 AC PASS / 66/66 全套 / pyright 0/0/0）
- **Branch**：`change/adapter-raw-upload-20260520`
- **Commits**：`e57f1e0` (design) → `1332034` (feat impl+test) → `ea72428` (chore head_commit 回填)
- **PR**：n/a（gh PAT 缺 pr:write；本地 branch 合并）

## AC 对照表

reviewer 真跑 4 条 AC + 全量 pytest + diff 扫 + pyright + 永不做清单 grep：

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL |
|---|---|---|---|---|
| AC-1 | behavioral | `cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_adapter_registry_round_trip -x -q` | `1 passed in 0.10s` | PASS |
| AC-2 | behavioral | `cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_raw_upload_auto_registered -x -q` | `1 passed in 0.10s` | PASS |
| AC-3 | behavioral | `cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_raw_upload_ingest_happy -x -q` | `1 passed in 0.10s` | PASS |
| AC-4 | behavioral | `cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_raw_upload_ingest_duplicate_path_raises -x -q` | `1 passed in 0.10s` | PASS |
| 全量回归 | behavioral | `cd packages/core && uv run pytest -x -q` | `66 passed in 0.29s` | PASS（W1-1..W2-6 共 62 + W3-1 新增 4，0 regression）|

## 机械化检查日志

### 4 个 AC 命令完整输出

```text
$ cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_adapter_registry_round_trip -x -q
.                                                                        [100%]
1 passed in 0.10s

$ cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_raw_upload_auto_registered -x -q
.                                                                        [100%]
1 passed in 0.10s

$ cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_raw_upload_ingest_happy -x -q
.                                                                        [100%]
1 passed in 0.10s

$ cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_raw_upload_ingest_duplicate_path_raises -x -q
.                                                                        [100%]
1 passed in 0.10s
```

### 全量 pytest 尾段

```text
$ cd packages/core && uv run pytest -x -q
..................................................................       [100%]
66 passed in 0.29s
```

基线 62（W1-1..W2-6 累计）+ 本 change 新增 4 = 66 ✓。无任何 regression。

### Pyright cd-into-module spot check

```text
$ cd packages/core && uv run pyright src/dataplat_core/adapters/ tests/test_adapter_raw_upload.py
0 errors, 0 warnings, 0 informations
```

adapters/ + test_adapter_raw_upload.py 静态检查 0/0/0 ✓。

### diff 范围扫描

```text
$ git diff main...HEAD --name-only
.harness/changes/adapter-raw-upload-20260520/design.md
.harness/changes/adapter-raw-upload-20260520/design_review.md
.harness/changes/adapter-raw-upload-20260520/implementation.md
.harness/changes/adapter-raw-upload-20260520/summary.md
.harness/changes/adapter-raw-upload-20260520/verify_review.md
packages/core/src/dataplat_core/adapters/__init__.py
packages/core/src/dataplat_core/adapters/raw_upload.py
packages/core/src/dataplat_core/adapters/registry.py
packages/core/tests/test_adapter_raw_upload.py

$ git diff main...HEAD --stat
 .../adapter-raw-upload-20260520/design.md          | 114 +++++++++++++++++++++
 .../adapter-raw-upload-20260520/design_review.md   |  58 +++++++++++
 .../adapter-raw-upload-20260520/implementation.md  |  86 ++++++++++++++++
 .../changes/adapter-raw-upload-20260520/summary.md |  60 +++++++++++
 .../adapter-raw-upload-20260520/verify_review.md   | (本文件)
 .../core/src/dataplat_core/adapters/__init__.py    |  16 +++
 .../core/src/dataplat_core/adapters/raw_upload.py  |  93 +++++++++++++++++
 .../core/src/dataplat_core/adapters/registry.py    |  36 +++++++
 packages/core/tests/test_adapter_raw_upload.py     |  72 +++++++++++++
```

新增 production 文件 3 个（registry.py + raw_upload.py + __init__.py）+ test 1 个 + harness 文档 5 个。范围严格符合 design.md In scope。

### Invariant 文件 0 改动核对（design.md "应当不动"清单）

```text
$ git diff main...HEAD -- apps/api/ | wc -l
0

$ git diff main...HEAD -- packages/core/src/dataplat_core/protocols/ | wc -l
0
```

- `apps/api/*` 全树（含 `apps/api/dataplat_api/adapters/raw_upload.py` 私有副本与 `apps/api/dataplat_api/runner/registry.py`）真实 0 改动 ✓
- `packages/core/src/dataplat_core/protocols/*`（SourceAdapter Protocol / IngestFileRef / IngestResult / RunContext）真实 0 改动 ✓
- W1-* / W2-* 所有产物（loaders/ / operators/ / recipe.py / dataset.py）真实 0 改动 ✓
- 本 change 仅新增 3 个 production 模块 + 1 个 test 模块，无任何修改既有文件

### Schema / 关键不变量检查

#### AdapterRegistry（packages/core/src/dataplat_core/adapters/registry.py）

| 不变量 | 期望（design.md） | 实际（registry.py） | 结论 |
|---|---|---|---|
| 存 SourceAdapter 实例（非 class）| 必须；design § 决策 3 显式声明不对称 | line 15 `self._registry: dict[str, SourceAdapter] = {}` ✓ | PASS |
| `register(adapter)` 入参是 adapter 实例 | 必须 | line 17 `register(self, adapter: SourceAdapter) -> None` ✓ | PASS |
| `register` 重复 name → ValueError("already registered") | 必须 | line 19-20 `raise ValueError(f"adapter '{name}' already registered")` ✓ | PASS |
| `get(name)` 缺失 → KeyError(name) | 必须 | line 23-25 `raise KeyError(name)` ✓ | PASS |
| `list_names() -> list[str]` sorted | 必须 | line 28-29 `return sorted(self._registry.keys())` ✓ | PASS |
| `_default = AdapterRegistry()` module-level singleton | 必须 | line 32 ✓ | PASS |
| `get_default() -> AdapterRegistry` 函数 | 必须 | line 35-36 ✓ | PASS |

#### RawFileUploadAdapter（packages/core/src/dataplat_core/adapters/raw_upload.py）

| 不变量 | 期望（design.md） | 实际 | 结论 |
|---|---|---|---|
| `name: str = "raw-file-upload"` | 必须 | line 62 ✓ | PASS |
| `version: str = "0.1"` | 必须 | line 63 ✓ | PASS |
| `input_schema: dict[str, Any]` 字段存在 | 必须 | line 64 ✓ | PASS |
| `output_subtype: str = "generic"` | 必须 | line 65 ✓ | PASS |
| `ingest(spec, workspace, ctx) -> IngestResult` 签名 | 必须 | line 67-72 ✓（workspace/ctx 类型放宽到 `\| None` 便于单元测试，与 apps/api 副本一致） | PASS |
| spec 校验失败 → ValueError | 必须 | line 74-77 try/except + raise ValueError ✓ | PASS |
| 重复 path → ValueError 含 "重复 path" | 必须（AC-4）| line 84-85 `raise ValueError(f"RawFileUpload spec.files 含重复 path: ...")` ✓ | PASS |
| asset_id 存在 → `asset_count=1` 否则 0 | 必须（AC-3）| line 90 `asset_count=1 if parsed.asset_id else 0` ✓ | PASS |
| import 走 `dataplat_core.protocols.adapter`（不走 apps/api）| 必须 | line 13-14 ✓ | PASS |

#### __init__.py auto-register（packages/core/src/dataplat_core/adapters/__init__.py）

| 不变量 | 期望 | 实际 | 结论 |
|---|---|---|---|
| import 时调 `_default.register(RawFileUploadAdapter())` | 必须 | line 11-14 ✓ | PASS |
| try/except ValueError 包裹（idempotent，与 operators/__init__.py 同模式） | 必须 | line 11-14 ✓ | PASS |
| `__all__` 含 `AdapterRegistry`, `RawFileUploadAdapter`, `get_default` | 必须 | line 16 ✓ | PASS |

### apps/api 私有副本未被改且与 core 副本 byte 级一致

```text
$ diff apps/api/dataplat_api/adapters/raw_upload.py packages/core/src/dataplat_core/adapters/raw_upload.py
# (无输出，exit 0)
```

apps/api 私有副本（`apps/api/dataplat_api/adapters/raw_upload.py`）与 packages/core 新副本 **byte 级完全一致**，符合 implementation.md § 偏离 "import 路径本已是 dataplat_core，所以 port 几乎无需改动" 的声明。两份代码短期共存的漂移风险由 follow-up `adapter-raw-upload-api-bridge-*` 桥接（design.md § 关联 follow-up 已列）。

### 永不做清单扫描（`.harness/rules/data-not-code-pivot.md`）

```text
$ grep -rn "dataset-card\|dataset_card\|manifest.yaml" \
    packages/core/src/dataplat_core/adapters/ \
    packages/core/tests/test_adapter_raw_upload.py
# (无输出，exit 1)
```

本 change 不触碰 dataset-card / dataset_card / manifest.yaml 任何一项 ✓。同时人工核对 source：`raw_upload.py` 仅做 (path → blob sha256) refs 转 `IngestResult.files`，不生成任何 yaml/json 元数据文件；不挂 silver/owner/name@ref；不触碰 branch / merge / cherry-pick / rollback / row-diff / blob 派生图 / Asset 任何概念。

### test_adapter_raw_upload.py 精读

- `_StubAdapter`（line 10-18）：name="test-adapter-w3-1"（与 raw-file-upload 不碰撞）/ version="0.1" / input_schema / output_subtype="test" / ingest 实现完整 ✓
- AC-1（test_adapter_registry_round_trip, line 21-29）：
  - `reg = AdapterRegistry()` 新实例（不污染全局 `_default`）✓
  - `reg.register(stub)` → `reg.get("test-adapter-w3-1") is stub`（identity 检查）✓
  - 重复 register 同 name → `pytest.raises(ValueError, match="already registered")` ✓
  - `list_names()` 含该 name ✓
- AC-2（test_raw_upload_auto_registered, line 32-37）：
  - `reg = get_default()`（用 module-level singleton）✓
  - `"raw-file-upload" in reg.list_names()` 验 `__init__.py` 自动注册成功 ✓
  - `adapter.name == "raw-file-upload"` 验 instance 完整 ✓
- AC-3（test_raw_upload_ingest_happy, line 40-58）：
  - spec={"files":[{"path":"doc.md","sha256":sha_a},{"path":"img.png","sha256":sha_b}],"asset_id":"a1"}
  - `adapter.ingest(spec, None, None)`（workspace/ctx 用 None，design.md decisions 决议）✓
  - `result.file_count == 2 / asset_count == 1`（asset_id 存在）✓
  - `result.files[0].path == "doc.md" / .sha256 == sha_a` ✓
  - `result.files[1].path == "img.png" / .sha256 == sha_b`（顺序保持）✓
- AC-4（test_raw_upload_ingest_duplicate_path_raises, line 61-72）：
  - spec.files 两条 path="x.txt"
  - `pytest.raises(ValueError, match="重复 path")` ✓

## drift correction 评审段（design.md § 决策 7）

**决策内容**：roadmap.md `W3-1 核心 AC` 含 "dataset-card.yaml 自动生成"——design.md § 决策 7 显式 **drop 此 AC**，理由是 "违反 `.harness/rules/data-not-code-pivot.md` 永不做清单 'manifest.yaml 强制'"。

**reviewer 评审意见：drift correction 已合理（同意 drop）**。

理由：

1. **直接命中永不做清单**：`data-not-code-pivot.md` D-1 明确列 "manifest.yaml 强制" 为永不做项；"dataset-card.yaml 自动生成" 与之同形（adapter 产出强制 yaml 元数据文件），属同类违规。
2. **替代方案完整**：design.md § 决策 7 已列 "commit message + IngestResult.notes" 作为人类可读元数据替代——前者承载 commit-level 信息（who/when/why）；后者由 adapter 主动写入（runner 已写到 commit log）；两者足以覆盖 "dataset-card.yaml 的元数据描述" 用途，无信息丢失。
3. **W3-1 目标完整性不受影响**："通用 binary → Bronze adapter" 的核心契约是 (spec.files → IngestResult.files)，dataset-card.yaml 与该契约正交；drop 后 W3-1 仍能完整满足 "通用 binary → Bronze" 目标。
4. **reviewer 实现核查**：grep `dataset-card / dataset_card / manifest.yaml` 在 packages/core/src/dataplat_core/adapters/ 与 tests/test_adapter_raw_upload.py 0 命中（见上节）；实现真没生成 dataset-card.yaml 相关代码 ✓。
5. **防复发机制**：design.md § 关联 follow-up 已列 `harness-data-not-code-grep-lint-*`，将在新 change 模板内自动 grep 永不做清单关键词，防 W3-2 / W3-3 复活该违规。

**结论**：drift correction 合理且实现合规；roadmap.md 中 "dataset-card.yaml" 既违规又非必要，drop 是正确决策。

## Schema 不对称性确认（design.md § 决策 3）

design.md § 决策 3 显式声明：**AdapterRegistry 存实例非类**——与 LoaderRegistry / OperatorRegistry 存 class 形成有意的不对称。

reviewer 核对：

- `packages/core/.../loaders/registry.py`：`_REGISTRY: dict[str, type]` + `@staticmethod`（存 class，无 `__init__`）
- `packages/core/.../operators/registry.py`：`_REGISTRY: dict[str, type]` + `@staticmethod`（存 class，无 `__init__`）
- `packages/core/.../adapters/registry.py`（本 change）：`_registry: dict[str, SourceAdapter]` + 实例方法 + `_default = AdapterRegistry()` + `get_default()`（存实例）
- `apps/api/.../runner/registry.py`：`_adapters: dict[tuple[str, str], SourceAdapter]` + 实例方法 + `_registry = AdapterRegistry()` + `get_registry()`（存实例，但 key 是 (name, version)）

apps/api 副本与 packages/core 新副本在 "存实例" 这一点上对齐 ✓；packages/core 新副本简化为 key=name（去 version 维度，与 LoaderRegistry/OperatorRegistry 的 key 形态一致），且重复 register 改为 raise ValueError（apps/api 是 warn skip）——这两处差异 design.md § 决策 3-5 均显式声明，**是有意决策，reviewer 同意**。

## 隐式偏离审计

> reviewer 对照 design.md vs implementation.md vs git diff，列出 implementation.md § 偏离 没声明但实际发生的偏离。**隐式偏离 = MUST FIX**。

- **无隐式偏离**。implementation.md § 偏离 明确写"无偏离。严格按 design.md In scope 落地。apps/api 副本 import 路径本已是 dataplat_core（非 dataplat_api），所以 raw_upload.py port 几乎无需改动——与 design.md 决策 1 描述一致"，reviewer 全量 diff + 不变量精读后**确认**：
  - In scope 4 个文件（registry.py / raw_upload.py / __init__.py / test_adapter_raw_upload.py）全部落地，无超范围
  - design.md "应当不动"清单（apps/api / W1-* / W2-* / protocols/）真实 0 改动（diff 验证）
  - AdapterRegistry schema / 不变量 7 项全部 PASS
  - RawFileUploadAdapter schema / 不变量 9 项全部 PASS
  - __init__.py auto-register 3 项全部 PASS
  - apps/api 与 packages/core 两份 raw_upload.py byte 级一致，符合 implementation.md 声明
  - 永不做清单 grep 0 命中，drift correction 实现合规
  - AdapterRegistry 与 LoaderRegistry/OperatorRegistry 的"实例 vs 类"不对称是 design.md § 决策 3 有意决策

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

> 完全可选；记入 follow-up change，不阻塞 merge。

- **apps/api 副本与 packages/core 副本的漂移**：当前两份 raw_upload.py byte 级完全一致，但短期内任何一方 bug fix 都需同步双改。design.md § 关联 follow-up 已列 `adapter-raw-upload-api-bridge-*` 桥接（apps/api/runner/registry.py 切到 `from dataplat_core.adapters import get_default`，删 apps/api 私有副本），建议作为 W3-2 之前的高优先 follow-up 推进，防漂移窗口拉长。
- **packages/core 缺真二进制 e2e 覆盖**：当前 4 条 AC 都是 spec 字符串校验级 unit test；apps/api e2e 已有 PDF/DOCX/PPT/XLSX 真二进制案例。design.md § 关联 follow-up 已列 `adapter-raw-upload-binary-e2e-*`，建议补 fixtures 后 W3 后期入。
- **AsyncAdapter 缺失**：design.md § 决策 6 显式声明 W3-* adapter 都是同步 ingest；firecrawl_url / 其他 I/O bound adapter 入场时再补 async Protocol，无紧迫性。
- **drift correction lint 机制还未落地**：design.md § 关联 follow-up `harness-data-not-code-grep-lint-*` 尚未实施；本 change 靠 reviewer 人工 grep 验证。建议作为 harness meta change 在 W3-2 前补，自动化防复发。

## Verdict

**APPROVED**

- 4 条 AC reviewer 真跑全 PASS（1 passed each, 0.10s）
- 全量回归 66/66 PASS（W1-1..W2-6 共 62 条 + W3-1 新 4 条；0 regression）
- pyright cd-into-module 0/0/0（src/dataplat_core/adapters/ + tests/test_adapter_raw_upload.py）
- diff 范围严格符合 design.md In scope：仅新增 3 个 production 模块 + 1 个 test + 5 个 harness 文档；Invariant 文件（apps/api / W1-* / W2-* / protocols/）真实 0 改动
- AdapterRegistry schema / 不变量 7 项全部 PASS（实例存储 / register raise ValueError / get raise KeyError / list_names sorted / _default singleton / get_default 函数 / SourceAdapter 类型注解）
- RawFileUploadAdapter schema / 不变量 9 项全部 PASS（name / version / input_schema / output_subtype / ingest 签名 / spec 校验 / 重复 path raise / asset_count 语义 / import 路径）
- __init__.py auto-register 3 项全部 PASS（idempotent try/except ValueError / __all__ 三项导出 / 与 operators/__init__.py 同模式）
- apps/api 与 packages/core 两份 raw_upload.py byte 级一致，符合 implementation.md 声明，0 隐式漂移
- **drift correction（drop dataset-card.yaml AC）合理**且实现合规：grep `dataset-card / dataset_card / manifest.yaml` 0 命中；替代方案（commit message + IngestResult.notes）完整；W3-1 目标完整性不受影响
- AdapterRegistry "存实例 vs LoaderRegistry/OperatorRegistry 存 class" 的不对称是 design.md § 决策 3 有意决策，reviewer 同意
- 隐式偏离 0；声明偏离 0；NICE TO HAVE 4 项全部非阻塞 follow-up

## 后续指引

1. **Application Owner 合并**：
   - 把 verify_review.md commit 到 `change/adapter-raw-upload-20260520`（建议 message: `docs(harness): adapter-raw-upload verify APPROVED (W3-1)`）
   - `git checkout main && git merge --no-ff change/adapter-raw-upload-20260520`
   - 把 verdict APPROVED 回填到 `summary.md`，归档 close
   - close TaskList #38 W3-1 Phase 3 verify
2. **Wave 3 推进**：W3-1 收官；W3-2（folder-md-assets adapter）/ W3-3（jsonl-import adapter）可按本 change 模板落
3. **NICE TO HAVE 优先级**：
   - 高优：`adapter-raw-upload-api-bridge-*`（W3-2 前）防漂移窗口拉长
   - 高优：`harness-data-not-code-grep-lint-*`（W3-2 前）自动化防 dataset-card.yaml 复活
   - 中优：`adapter-raw-upload-binary-e2e-*`（W3 后期）补真二进制 fixtures
   - 低优：`adapter-firecrawl-port-*`（按 W3 roadmap 调度）
