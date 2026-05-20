---
change_id: adapter-raw-upload-20260520
phase: design
status: approved
authored_at: 2026-05-21T02:30:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：raw-upload adapter port to packages/core + AdapterRegistry (W3-1，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

把 `RawFileUploadAdapter` 从 `apps/api/dataplat_api/adapters/` port 到 `packages/core/src/dataplat_core/adapters/`，并新增 `AdapterRegistry`（与 LoaderRegistry / OperatorRegistry 同模式），把"通用 binary → Bronze"adapter 抽象沉到 core 层。

## 背景

W1-2 / W1-4 / W2-1..W2-6 已把 Operator / Loader / Recipe / DatasetExport 全部沉到 packages/core；W3 启动后，Adapter 是最后一类未沉的算子。当前状态：

- ✅ `SourceAdapter` Protocol 已在 `packages/core/src/dataplat_core/protocols/adapter.py`（W1-2 留下）
- ✅ `RawFileUploadAdapter` 已在 `apps/api/dataplat_api/adapters/raw_upload.py`（adapter-framework-20260517 留下）
- ✅ `POST /repos/{owner}/{name}/blobs` multipart upload endpoint 已在 `apps/api/dataplat_api/routers/snapshots.py`（W1-1 已稳）
- ✅ AdapterRegistry 在 `apps/api/dataplat_api/runner/registry.py`（apps/api 私有）
- ⏳ 缺：core 层 AdapterRegistry + 内置 raw-file-upload 注册（与 LoaderRegistry / OperatorRegistry 对称）
- ⏳ 缺：packages/core 单元测试覆盖（apps/api 已有 e2e，但 packages/core 内 0 测试）

本 change 把 raw-upload core 化，让未来 Wave 3 其他 adapter（folder-md-assets / jsonl-import）按同模板落地。

**Roadmap drift correction（D-1 永不做清单）**：roadmap.md `W3-1 核心 AC` 含 "dataset-card.yaml 自动生成"——这与 `.harness/rules/data-not-code-pivot.md` "永不做 manifest.yaml 强制" 直接冲突；本 change 显式 **drop 此 AC**，由 application-owner 决策入 design.md（决策 7）。

## 范围

In scope：

- `packages/core/src/dataplat_core/adapters/registry.py`（新）：
  - `class AdapterRegistry`：模块级 singleton 模式
    - `_registry: dict[str, SourceAdapter] = {}`（实例存储，与 apps/api/runner/registry.py 一致——adapter 用实例不用 class，因 apps/api 已用此模式）
    - `register(adapter: SourceAdapter) -> None`：name 已存在 → raise `ValueError(f"adapter '{name}' already registered")`
    - `get(name: str) -> SourceAdapter`：缺失 → raise `KeyError(name)`
    - `list_names() -> list[str]`：sorted names
  - 模块底加 `_default = AdapterRegistry()` + `get_default()` 函数（与 OperatorRegistry / LoaderRegistry 同模式）
- `packages/core/src/dataplat_core/adapters/raw_upload.py`（新）：
  - 把 `apps/api/dataplat_api/adapters/raw_upload.py` 完整 copy 过来（删除 `from dataplat_api...` import，全部走 `from dataplat_core.protocols.adapter import IngestFileRef, IngestResult` 等）
  - class `RawFileUploadAdapter`：保留 name="raw-file-upload" / version="0.1" / input_schema / output_subtype 字段；保留 ingest 方法签名 + 校验逻辑
- `packages/core/src/dataplat_core/adapters/__init__.py`（新）：
  - import `RawFileUploadAdapter`、`get_default()`
  - 模块加载时 try/except ValueError 注册 `raw-file-upload`（与 OperatorRegistry/LoaderRegistry 同 idempotent 模式）
  - export `RawFileUploadAdapter`、`AdapterRegistry`、`get_default`
- `packages/core/tests/test_adapter_raw_upload.py`（新）：4 个 behavioral 用例
- **不动**：`apps/api/dataplat_api/adapters/raw_upload.py`（保留 apps/api 私有副本，避免破坏 apps/api e2e 测试 + apps/api/runner/registry 既有注册路径——backward-compat 第一）

Out of scope：

- **不**改 apps/api/raw_upload.py / apps/api/runner/registry.py / apps/api/routers/*：apps/api 接入 packages/core 注册留 follow-up `adapter-raw-upload-api-bridge-*`
- **不**做 dataset-card.yaml：**违反 D-1 永不做清单（manifest.yaml 强制）**；roadmap drift correction
- **不**实现新 adapter（folder-md-assets / jsonl-import）：W3-2 / W3-3
- **不**做 apps/api e2e PDF/DOCX/PPT/XLSX 测试：apps/api 已有 e2e；packages/core 仅做 unit 级
- **不**做 apps/web 上传组件：W4 范围
- **不**改 SourceAdapter Protocol（W1-2 已稳）
- **不**强 jsonschema 校验 spec（adapter 内 try/except + ValueError 已做；不引入 fastjsonschema 等依赖）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | AdapterRegistry 基础 round-trip：register stub adapter → get(name) 返实例；重复 register 同 name 抛 ValueError；list_names() 含该 name | `cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_adapter_registry_round_trip -x -q` | 1 passed |
| AC-2 | behavioral | import dataplat_core.adapters 后 get_default().list_names() 含 "raw-file-upload" | `cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_raw_upload_auto_registered -x -q` | 1 passed |
| AC-3 | behavioral | RawFileUploadAdapter.ingest happy path：spec={"files":[{"path":"doc.md","sha256":"<64hex>"},{"path":"img.png","sha256":"<64hex>"}],"asset_id":"a1"} → IngestResult.file_count==2, asset_count==1, files[0].path=="doc.md", files[1].sha256 一致 | `cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_raw_upload_ingest_happy -x -q` | 1 passed |
| AC-4 | behavioral | RawFileUploadAdapter.ingest 重复 path → raise ValueError 含 "重复 path" 子串 | `cd packages/core && uv run pytest tests/test_adapter_raw_upload.py::test_raw_upload_ingest_duplicate_path_raises -x -q` | 1 passed |

## 决策

1. **core port 而非 in-place evolution**：与 W1-4 PdfMineruLoader 同模式；让 packages/core 持有"内置 adapter 集合"成为 Wave 3 其他 adapter 的模板。
2. **保留 apps/api 私有副本不动**：避免破坏 apps/api/runner/registry 与现有 e2e 测试；apps/api 切换到 packages/core 注册留 follow-up。
3. **AdapterRegistry 存实例非类**：与 apps/api/runner/registry.py 现有约定一致（adapter 是无状态服务对象；不像 Operator/Loader 每次实例化）；这是个**有意的不对称**——Adapter 注册是 instance-based，Operator/Loader 是 class-based。
4. **module-level singleton + get_default()**：与 OperatorRegistry / LoaderRegistry 完全同模板；caller 用 `from dataplat_core.adapters import get_default; reg = get_default()`。
5. **auto-register 用 try/except ValueError**：idempotent 注册；多次 import / pytest 反复加载不破裂；与 W2-* operators 完全同模式。
6. **不引入 AsyncAdapter**：W3-* adapter 都是同步 ingest；async 留 follow-up（若未来 firecrawl 等需要 async I/O）。
7. **roadmap drift correction：drop "dataset-card.yaml 自动生成" AC**：违反 D-1 永不做清单 "manifest.yaml 强制"；application-owner 决策；W3-1 不需 dataset-card.yaml 也能完整满足"通用 binary → Bronze"目标；commit 时人类可读元数据由 commit message + IngestResult.notes 承载即可。

## 风险

| 风险 | 缓解 |
|---|---|
| apps/api 私有 RawFileUploadAdapter 与 packages/core 副本漂移（两份代码） | follow-up `adapter-raw-upload-api-bridge-*` 把 apps/api 切到 packages/core 进口；本 change 显式接受短期重复 |
| AdapterRegistry 与 apps/api/runner/registry.py 命名冲突 | 模块路径完全不同（packages/core/.../adapters/registry.py vs apps/api/.../runner/registry.py）；import 不冲突；caller 显式选 |
| pytest 全套回归：apps/api 测试用 apps/api 的 registry，packages/core 测试用 packages/core 的 registry，互不影响 | 单元测试隔离；不跨模块；无 fixture 共享 |
| 永不做清单 drift correction 未被 reviewer 看见 → 后续 W3-2 又复活 dataset-card.yaml | 本 design.md 决策 7 显式记录；reviewer Phase 3 必查决策日志；新 change 模板在 follow-up harness meta change 中加 "永不做清单 grep" lint |
| stub adapter for AC-1 命名碰撞 production "raw-file-upload" | stub name 用唯一前缀 "test-adapter-w3-1"；与 W2-* test fixture 同模式 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/adapter.py`（SourceAdapter Protocol / IngestFileRef / IngestResult）
  - `packages/core/src/dataplat_core/protocols/runcontext.py`（RunContext）
  - `apps/api/dataplat_api/adapters/raw_upload.py`（**参考但不动**，作为 source of truth）
  - `packages/core/src/dataplat_core/operators/__init__.py`（auto-register 模板参考）
  - `packages/core/src/dataplat_core/loaders/registry.py`（singleton + get_default 模板参考）
- 应当不动：
  - `apps/api/*`（全部不动，含 routers / runner / adapters / services）
  - W1-* / W2-* 所有产物
  - `packages/core/src/dataplat_core/protocols/*`
- 引用的其他 change：W1-2（Adapter Protocol）、adapter-framework-20260517（apps/api raw_upload 原版本）

## 关联 follow-up

- `adapter-raw-upload-api-bridge-*`：apps/api/runner/registry.py 切到 `from dataplat_core.adapters import get_default`；删除 apps/api 私有副本
- `adapter-raw-upload-binary-e2e-*`：packages/core 测试加 PDF/DOCX/PPT/XLSX 真二进制 fixture（小样本）
- `adapter-firecrawl-port-*`：把 firecrawl_url adapter port 到 packages/core
- `harness-data-not-code-grep-lint-*`：新 change 模板加"永不做清单"自动 grep 提醒（防 dataset-card.yaml 复活）
- W3-2 / W3-3：folder-md-assets / jsonl-import adapter（按本 change 模板落）
