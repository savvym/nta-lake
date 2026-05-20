---
change_id: loader-refactor-pdf-mineru-20260520
phase: design
status: approved
authored_at: 2026-05-20T20:45:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：PdfMineruLoader 实现 Loader Protocol + LoaderRegistry (W1-4，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。Phase 2 sonnet 端到端；Phase 3 opus 跑 pytest 验收。

## 一句话目标

把 `PdfMineruProcessor` 重构为 `PdfMineruLoader`（实现 Loader Protocol，输出 list[SilverRow]）+ 落 LoaderRegistry 骨架；老 Processor 保留不撤。

## 背景

W1-2 已落地 `Loader` Protocol + `SilverRow` Pydantic（`packages/core/src/dataplat_core/protocols/loader.py`）。当前 `apps/api/dataplat_api/processors/pdf_mineru.py` 是 first-gen Processor（输入 RepoView，输出 IngestFileRef 文件树），需在保留老 Processor 不撤的前提下，新增一个 **`PdfMineruLoader`**（输入 bronze blob sha，输出 `LoadResult{ rows: list[SilverRow] }`），作为北极星模型的首个真实 Loader 实现 + 标杆。同时落地 `LoaderRegistry`（结构与 `OperatorRegistry` 完全对齐）。

Wave 1 末尾的 checkpoint 是"end-to-end PDF demo 跑通新模型"，本 change 是该 demo 的关键一环（Loader 侧）；recipe v2（W2-5）才把 Loader+Operator 串成 pipeline，本 change 不动调度。

## 范围

In scope：

- `packages/core/src/dataplat_core/loaders/__init__.py` + `registry.py`（新）：`LoaderRegistry` 模块单例（结构对齐 `operators/registry.py`：staticmethod `register(name, cls)` / `get(name)` / `list_names()`；重复注册 ValueError；未注册 KeyError）
- `packages/core/src/dataplat_core/loaders/__init__.py` 同时 export `LoaderRegistry`
- `apps/api/dataplat_api/loaders/__init__.py` + `pdf_mineru.py`（新）：`PdfMineruLoader` 实现 Loader Protocol：
  - 属性：`name = "pdf-mineru"`、`version = "0.1"`、`input_subtype = "pdf"`（bronze subtype 约定）、`output_schema_id = "silver-text-v1"`
  - `load(bronze_blob_sha: SHA256, config: dict, ctx: RunContext) -> LoadResult`：
    - 从 `ctx.blob_store.get(bronze_blob_sha)` 读 PDF bytes（`ctx` 必须有 `blob_store`，无则 ValueError）
    - 用 `MinerUClient`（复用现有 `apps/api/dataplat_api/processors/_mineru_client.py`）调 MinerU API，poll 到 succeeded，fetch 完整结果
    - 产出 **1 个 SilverRow**：
      - `text` = MinerU 返回的 markdown
      - `images` = `[{"filename": <fn>, "blob_sha": <sha>} for fn, bytes in full.images]`（每张图先 `blob_store.put`，再把 sha 写进 row；CAS dedup）
      - `source_ref` = `{"blob_sha": bronze_blob_sha, "loader": "pdf-mineru", "loader_version": "0.1"}`
      - `stats` = `{"text_chars": len(markdown), "image_count": len(images)}`
      - `lineage_ops` = `[]`（Loader 不属于 lineage_ops；后续 Operator 链才追加）
    - 返 `LoadResult(rows=[row], total_count=1, notes=f"pdf-mineru via {api_url}")`
  - env 约束沿用：`MINERU_API_URL` 必需缺则 ValueError；`MINERU_API_TOKEN` 可选
- `apps/api/dataplat_api/loaders/__init__.py`：在 import 时调 `LoaderRegistry.register("pdf-mineru", PdfMineruLoader)`（与 processors `__init__.py` 自动注册模式对齐）
- `packages/core/tests/test_loader_registry.py`（新）：1 个 behavioral 用例（register / get / list_names / 重复 ValueError / 缺失 KeyError）
- `apps/api/tests/test_pdf_mineru_loader.py`（新）：2 个 behavioral 用例
  - 用例 1：MinerUClient 全 mock，伪造 succeeded + markdown + 2 images → 调 `loader.load(...)` → 返 1 row，text == 假 markdown，images.len == 2 + 每项有 blob_sha，source_ref/loader == "pdf-mineru"，stats 字段齐
  - 用例 2：缺 `MINERU_API_URL` env → ValueError

Out of scope：

- **不**改 / 不撤老 `PdfMineruProcessor`（first-gen 在 W2-5 recipe v2 落地后另起 cleanup change 撤）
- **不**实现 worker / API 调 Loader 的入口（recipe v2 W2-5 才接 Loader）
- **不**改 commit / snapshot 写入路径（W2-5 处理）
- **不**实施 row 校验（与 schema_id 真校验 → W2-5）
- **不**支持多 PDF 批量（一 row per blob；批处理由 caller 多次调 load 实现）
- **不**生成 content_list.json 附产物（与 first-gen Processor 行为对齐：Loader 关心 row 而非文件树）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | LoaderRegistry：register + get + list_names + 重复 ValueError + 缺失 KeyError 全覆盖 | `cd packages/core && uv run pytest tests/test_loader_registry.py -x -q` | 1 passed |
| AC-2 | behavioral | PdfMineruLoader 用 mock MinerUClient 调 load → 返 LoadResult.rows == 1 + row.text/images/source_ref/stats 字段语义正确（具体见 In scope SilverRow 描述） | `cd apps/api && uv run pytest tests/test_pdf_mineru_loader.py::test_load_returns_single_silver_row -x -q` | 1 passed |
| AC-3 | behavioral | 缺 `MINERU_API_URL` env → `load()` raise ValueError 含 "MINERU_API_URL" 字样 | `cd apps/api && uv run pytest tests/test_pdf_mineru_loader.py::test_load_missing_env_raises -x -q` | 1 passed |

## 决策

1. **保留老 Processor 不撤**：W1-2 already declared "Processor 老类保留不撤"；本 change 沿用。recipe v2（W2-5）切换调度后再起 cleanup change 撤 first-gen。
2. **复用 `_mineru_client.py`**：MinerU HTTP 协议没变，复用 client 是最小修改路径；不去 packages/core/ 包装（client 是 api 侧实现细节，core 只定 Protocol）。
3. **Loader 实现放 apps/api/dataplat_api/loaders/**（不是 packages/core 也不是 plugins/）：
   - core 只定 Protocol 与 Registry 骨架（无外部依赖：httpx、blob_store 都在 api 侧）
   - plugins/ 目录目前为空且无 entrypoint loader 机制（W4 才考虑插件化）
   - apps/api 是当前能 import MinerUClient + blob_store 的唯一地方
4. **一个 PDF blob → 一个 SilverRow**（不按页拆分）：拆分语义属于 Operator (chunker) 的职责（W2-2）；Loader 保持"一份原料一行 silver"的最简模型。
5. **images 写 blob_store 后只在 row 里存 sha**（不直接塞 bytes）：与平台 CAS 设计一致；row 在 silver snapshot 里序列化为 parquet/jsonl 时 size 受控。
6. **`output_schema_id = "silver-text-v1"`**：与 W1-3 注册的 builtin schema_id 对齐；未来 PDF 专属 schema（如含表格结构）可再注册。
7. **不引入 LoaderContext**：用 `ctx: RunContext`（W1-2 已定）；ctx.blob_store 是 attached attribute，与 Processor 一致。
8. **不在本 change 接 worker 调度**：worker 仍调 first-gen Processor；Loader 仅供 W2-5 recipe v2 切换；本 change 仅 unit-test Loader 类。

## 风险

| 风险 | 缓解 |
|---|---|
| MinerUClient 在 unit test 里需要 mock | sonnet 用 `unittest.mock.patch` mock `MinerUClient.submit/poll/fetch_full_result`；或在 conftest 注入 stub client；不需要真 MinerU 服务起来 |
| blob_store 在 unit test 里 mock | 用 fake blob_store（in-memory dict）；只需 `put(stream, declared_size)` 返 `BlobPutResult{sha256, size}`、`get(sha)` 返 bytes |
| ctx 接口可能不全 | RunContext Protocol 定义了 logger/metrics/secrets/cancel_event/llm，没定义 blob_store；当前 Processor 用 `getattr(ctx, "blob_store", None)` 兜底——Loader 沿用同模式；blob_store 形式化进 RunContext 是 W2-5 的事 |
| 与 plugins/ 未来的关系 | 现在 plugins/ 空；本 change 把 PdfMineruLoader 落在 apps/api/loaders/ 是过渡安排，W4-* 插件化时再迁；Loader Protocol 在 core 不受影响 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：`packages/core/src/dataplat_core/protocols/loader.py`（W1-2 落地，本 change 不动）
- 应当不动：
  - `apps/api/dataplat_api/processors/pdf_mineru.py`（老 Processor 保留）
  - `apps/api/dataplat_api/processors/__init__.py`（老 Processor 注册保留）
  - `packages/core/src/dataplat_core/operators/*`（Operator 与 Loader 分离）
  - `packages/core/src/dataplat_core/schemas/*`（W1-3 已固化）
- 引用的其他 change：W1-2（Loader Protocol）、W1-3（silver-text-v1 schema 注册）
