---
change_id: recipe-yaml-v2-20260520
phase: design
status: approved
authored_at: 2026-05-21T00:50:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：Recipe YAML v2 解析器 + 执行器 (W2-5，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。本 change 范围比 W2-1..W2-4 大（新 schema + parser + executor），但仍坚持 v3 单文件落地原则。

## 一句话目标

落 `packages/core/src/dataplat_core/recipe.py`：v2 schema (`loader + operators`) + `load_recipe_v2()` 解析器 + `run_recipe_v2()` in-process 执行器，把 Loader 与 Operator 链起来端到端跑 Bronze blob → Silver rows。

## 背景

W1-2 / W1-4 / W2-1..W2-4 已落 Operator Protocol + Loader Protocol + 9 个 Operator + 1 个 Loader（pdf-mineru）。北极星 §recipe-v2 明确"Recipe = 1 Loader + N Operators"——这是 silver 层算子链的**核心编排抽象**，区别于 v1 DAG-based pipeline（`apps/api/dataplat_api/schemas/pipeline.py::Recipe` 是 processor-DAG 风格）。

v2 与 v1 的本质差异：
- **v1**: DAG of arbitrary processors with input/output refs；通用但重度
- **v2**: 单 loader + 线性 operator 链；专为"训练数据 silver 层"优化；与 W1-4 PdfMineruLoader + W2-* Operator 直接对齐

本 change **不替换** v1 Recipe 模型（v1 在 `apps/api/dataplat_api/schemas/pipeline.py`，仍服务现有 pipeline router）；v1→v2 API 层迁移留单独 follow-up change（`recipe-api-v2-routes-*`）。本 change 专注 **core engine**，把 v2 解析+执行做成 self-contained 函数，下游 API / worker 后续接入。

## 范围

In scope：

- `packages/core/src/dataplat_core/recipe.py`（新）：
  - **schemas**：
    - `RecipeLoaderSpec(BaseModel)`：`name: str`、`config: dict = {}`、`input: dict` (含 `blob_sha: str` required；其他 key v1 不约束)
    - `RecipeOperatorSpec(BaseModel)`：`name: str`、`config: dict = {}`
    - `RecipeV2(BaseModel)`：`name: str (min_length=1)`、`version: Literal[2]`、`loader: RecipeLoaderSpec`、`operators: list[RecipeOperatorSpec] = []`
    - 全部 `model_config = ConfigDict(extra="forbid")`
  - **parser**：`load_recipe_v2(data: str | dict) -> RecipeV2`
    - str → `yaml.safe_load` → 顶层必须是 mapping
    - 检查 `version` 字段：
      - 缺失 / != 2 → `raise ValueError("recipe v1 deprecated; please use v2 (version: 2)")`
      - == 2 → `RecipeV2.model_validate(data)`
  - **executor**：`run_recipe_v2(recipe: RecipeV2, ctx: RunContext) -> RecipeRunResult`
    - 1) `loader_cls = LoaderRegistry.get(recipe.loader.name)`
    - 2) `loader = loader_cls()`
    - 3) `blob_sha = recipe.loader.input["blob_sha"]`（缺 → KeyError）
    - 4) `load_result = loader.load(blob_sha, recipe.loader.config, ctx)`
    - 5) `rows = list(load_result.rows)`、`total_input = len(rows)`
    - 6) 逐个 operator：
       ```python
       for op_spec in recipe.operators:
           op_cls = OperatorRegistry.get(op_spec.name)
           op = op_cls()
           new_rows: list[SilverRow] = []
           for row in rows:
               new_rows.extend(op.run(row, op_spec.config, ctx))
           rows = new_rows
       ```
    - 7) 返 `RecipeRunResult(rows=rows, total_input=total_input, total_output=len(rows), loader_notes=load_result.notes)`
  - **RecipeRunResult**：`rows: list[SilverRow]`、`total_input: int`、`total_output: int`、`loader_notes: str | None = None`
- `packages/core/src/dataplat_core/__init__.py`（如有 `__all__` 则导出 `RecipeV2 / load_recipe_v2 / run_recipe_v2`；若尚未有 root export，则跳过本步——保持当前模块边界）
- `packages/core/tests/test_recipe_v2.py`（新）：4 个 behavioral 用例

Out of scope：

- **不**改 `apps/api/dataplat_api/schemas/pipeline.py`（v1 Recipe）：留 follow-up `recipe-api-v2-routes-*`；v1 仍服务现有 pipeline router
- **不**改 apps/api pipeline router / orchestrator / worker：core engine 独立可测；API 接入是分离的关注点
- **不**实现 cycle / topo sort：v2 是**线性**链，无需 DAG
- **不**支持 v2 中 `input` 用 repo ref (`@<name>`)：v1 仅支持 `blob_sha` 直传；repo-ref resolve 留 W3 / api 接入 change
- **不**接 worker 调度：`run_recipe_v2` 是 in-process **同步**函数；async loader 内部用 `asyncio.run`（PdfMineruLoader 已是该模式）
- **不**写入 silver snapshot 到 CAS：v1 仅返 rows in memory；持久化是 W2-6 dataset-export-engine 的事
- **不**强 jsonschema 校验 operator config（依赖 W2-* operator 内部 config_schema 自检；本 change 仅做 schema-level Pydantic 校验）
- **不**给 v1 Recipe 加 deprecation warning：v1 模型不动；v2 parser 仅拒绝**接收**v1 yaml

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | load_recipe_v2 接受合规 v2 yaml str (含 1 loader + 3 operators)，返 RecipeV2 对象；name/version/loader.name/operators 字段正确 | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_load_recipe_v2_valid -x -q` | 1 passed |
| AC-2 | behavioral | load_recipe_v2 拒绝缺 version 或 version != 2 的 yaml；抛 ValueError 含 "v1 deprecated" / "version: 2" | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_load_recipe_v2_rejects_v1 -x -q` | 1 passed |
| AC-3 | behavioral | run_recipe_v2 端到端：用 stub TestLoader（test 内注册）+ chain [filter, chunker, snapshot_tag] 跑，断言 total_input/output + 每行 lineage_ops 含完整 3 个 op 记录 | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_end_to_end -x -q` | 1 passed |
| AC-4 | behavioral | run_recipe_v2 空 operators 列表：rows 即 loader 输出原样；total_input == total_output；lineage_ops 不被追加 | `cd packages/core && uv run pytest tests/test_recipe_v2.py::test_run_recipe_v2_empty_operators -x -q` | 1 passed |

## 决策

1. **core-only 范围，API 层留 follow-up**：v1 Recipe 是 apps/api 的 schema，与 v2 core engine 解耦；本 change 不动 v1；follow-up `recipe-api-v2-routes-*` 接入。
2. **v2 yaml 顶层必含 `version: 2`**：显式 versioning；parser 通过 version 字段路由（v1 字段 `nodes` 不在 v2 schema 故 extra="forbid" 也会拒）。
3. **executor 同步 + in-process**：与 PdfMineruLoader 内部 `asyncio.run` 模式对齐；不引入 async API surface 到 recipe 层。
4. **operators 是线性链非 DAG**：v2 设计前提；如未来需要并行/分支再分单独 change。
5. **input 仅支持 `blob_sha` 直传**：repo-ref resolve（如 `bronze/owner/name@ref`）需要 repo 服务，跨模块；留 W3 / api change。
6. **RecipeRunResult 不写入 CAS**：核心引擎职责单一——把 chain 跑通；持久化是 W2-6。
7. **不强校验 operator config 内容**：jsonschema 在 operator 自身 spec 里声明；run 时 config 通过 dict 透传；caller 守约；W2-* 各 operator 已在 design 中声明 KeyError 兜底。
8. **stub TestLoader 在 test 文件内 inline 定义并注册**：避免污染 production LoaderRegistry；测试 fixture 用 try/except ValueError 注册（与 W2-1..W2-3 auto-register 同模式）。

## 风险

| 风险 | 缓解 |
|---|---|
| stub TestLoader 注册污染单例（影响 W1-4 / 别 test） | 用 `try: LoaderRegistry.register(...) except ValueError: pass` 容错；test name 用唯一前缀如 "test-loader-recipe-v2"；与 W1-2 test_operator_protocol 同模式 |
| RecipeV2 + RecipeLoaderSpec + RecipeOperatorSpec 与 v1 同名冲突 | v1 在 `apps/api/.../schemas/pipeline.py`；v2 在 `packages/core/.../recipe.py`；模块完全分离；不冲突 |
| executor `loader.load()` 抛错（如 blob_sha 不存在）未被本 change 包装 | v1 不加 try/except；让异常透出；caller / pipeline 层后续封装；测试用 stub 不会抛 |
| 链中 Operator 抛 KeyError（缺必填 config）破坏整链 | 期望行为：caller 在 design / recipe 时守约；W2-* 各 operator KeyError 是 expected v1 behavior；test AC-3 用合规 config 验证 happy path |
| pydantic Literal[2] 在 v1 yaml `version: 1` 时报错信息不够友好 | parser 在 model_validate 前**先查** version 字段并显式抛 "v1 deprecated"；pydantic 兜底信息次要 |
| 总注册 operator 数 >= 9（W2-4 后 9 个内置 + 测试污染）影响 AC-3 中 OperatorRegistry.get | AC-3 用具体 operator 名 (filter/chunker/snapshot_tag) 而非 count；不依赖总数 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/loader.py`（SilverRow / LoadResult / Loader Protocol）
  - `packages/core/src/dataplat_core/protocols/operator.py`（Operator Protocol）
  - `packages/core/src/dataplat_core/loaders/registry.py`（LoaderRegistry）
  - `packages/core/src/dataplat_core/operators/__init__.py`（OperatorRegistry + 9 内置）
  - `apps/api/dataplat_api/schemas/pipeline.py`（v1 Recipe，参考但不动）
  - `apps/api/dataplat_api/loaders/pdf_mineru.py`（参考 asyncio.run 模式）
- 应当不动：
  - `apps/api/*`（v1 Recipe / pipeline router / orchestrator 全部不动）
  - 所有 W2-1..W2-4 Operator (filter/dedup/score/chunker/image_strip/image_caption_stub/snapshot_tag/snapshot_sample/identity)
  - `packages/core/src/dataplat_core/protocols/*`
- 引用的其他 change：W1-2（Operator Protocol）、W1-4（Loader Protocol + asyncio.run 模式）、W2-1..W2-4（9 内置 Operator）

## 关联 follow-up

- `recipe-api-v2-routes-*`：apps/api 接入 v2，POST /recipes/v2/runs 走新 engine；v1 Recipe 加 deprecation warning
- `recipe-yaml-v2-repo-ref-input-*`：支持 `input.snapshot: bronze/owner/name@ref` 解析
- `recipe-yaml-v2-cache-*`：基于 (recipe_hash, blob_sha) 的结果缓存
- W2-6 dataset-export-engine：把 RecipeRunResult.rows 持久化进 silver snapshot
