---
change_id: silver-schema-enforce-20260520
phase: design
status: approved
authored_at: 2026-05-20T19:35:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：silver/gold repo 创建强制 schema_id + row_format (W1-3，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。Phase 2 sonnet 端到端；Phase 3 opus 跑 pytest 验收。

## 一句话目标

silver/gold repo 创建强制必带 `schema_id`（已注册）+ `row_format ∈ {parquet, jsonl}`；bronze 必不带。

## 背景

`data-not-code-pivot.md` § 旧→新术语表 把 "Silver/Gold 推荐 Parquet" 升级为"**强制** Parquet/JSONL + schema 注册"。W1-2 已在 `packages/core/src/dataplat_core/protocols/loader.py` 定义 `SilverRow` Pydantic（含 source_ref/stats/lineage_ops/text/images）。本 change 加 `SchemaRegistry` + 在 API 层强制：silver/gold repo 创建必须声明已注册的 schema_id + row_format；bronze 创建必不带（继续文件树）。DB 层加 2 个 nullable 列 + alembic migration。这是 Wave 1 地基里"对外定义数据形态"的最后一步。

## 范围

In scope：

- `packages/core/src/dataplat_core/schemas/__init__.py` + `schemas/registry.py`（新）：`SchemaRegistry` 模块单例（`register(schema_id: str, row_cls: type[BaseModel], layer: Layer) -> None` / `get(schema_id) -> SchemaEntry` / `list_ids() -> list[str]` / `is_registered(schema_id) -> bool`）；`SchemaEntry` Pydantic 含 `schema_id` + `row_cls` + `layer`
- `packages/core/src/dataplat_core/schemas/_builtin.py`（新）：预注册 `silver-text-v1` → SilverRow (layer="silver")；`gold-sft-v1` → 一个新的 GoldSFTRow Pydantic（含字段 `prompt: str` + `completion: str` + 复用 `source_ref` / `stats` / `lineage_ops`；用 layer="gold"）。**仅注册这 2 个标杆**，其他 schema 留给后续 change
- `packages/core/src/dataplat_core/schemas/silver_row.py`（新）：把 W1-2 已存在的 SilverRow 从 `protocols/loader.py` re-export 到 `schemas/silver_row.py`（不复制，从 loader import 后 `__all__` 导出），方便 schema_id 注册时 import 路径稳定
- `packages/core/src/dataplat_core/schemas/gold_row.py`（新）：`GoldSFTRow` Pydantic
- `apps/api/dataplat_api/models/repository.py`：`RepositoryORM` 加 2 个 nullable 列 `schema_id: str | None` + `row_format: str | None`
- `apps/api/alembic/versions/<next>_add_schema_id_row_format.py`（新）：单条 migration，加 2 列（nullable=True；老 row 保持 NULL）
- `apps/api/dataplat_api/schemas/repo.py`：`RepositoryCreate` 加 2 个 Optional 字段 `schema_id: str | None = None` + `row_format: Literal["parquet", "jsonl"] | None = None`；`RepositoryRead` 同步加（响应包含）
- `apps/api/dataplat_api/services/repo.py`：`RepoService.create` 加 422 enforcement：
  1. `layer in ("silver", "gold")` → `schema_id` 必填 + `row_format` 必填 + `SchemaRegistry.is_registered(schema_id)` 必 True + `SchemaRegistry.get(schema_id).layer == layer`（schema 不能跨层）
  2. `layer == "bronze"` → 两字段都必须 None（不能传）
  3. 上述任一 fail → `HTTPException(422, detail=...)`
- `apps/api/tests/test_repo_schema_enforcement.py`（新）：4 个 behavioral 用例

Out of scope：

- **不**强制老 silver/gold repo 迁移（老数据 schema_id NULL，保留兼容；后续 change 处理）
- **不**改 commit/snapshot 写入路径校验行 schema（snapshot 写入校验是 W2-5 recipe v2 时再做）
- **不**实现 row 校验（仅注册 schema；用 schema 校验 row 是后续 change）
- **不**改 web UI（W4-1+ 处理）
- **不**改 SDK CLI（W2-5 recipe v2 时一并升级）
- **不**改 Loader / Operator Protocol（W1-2 已落定）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | SchemaRegistry import + `silver-text-v1` / `gold-sft-v1` 默认已注册 + 跨层注册抛 ValueError | `cd packages/core && uv run pytest tests/test_schema_registry.py -x -q` | 1+ passed |
| AC-2 | behavioral | POST /repos layer=silver 缺 schema_id → 422；缺 row_format → 422；schema_id="unknown" → 422；schema_id 是 gold 的但 layer=silver → 422 | `cd apps/api && uv run pytest tests/test_repo_schema_enforcement.py::test_silver_create_422 -x -q` | 1 passed |
| AC-3 | behavioral | POST /repos layer=silver schema_id="silver-text-v1" row_format="parquet" → 201 + GET 响应含两字段；layer=bronze 传 schema_id → 422 | `cd apps/api && uv run pytest tests/test_repo_schema_enforcement.py::test_silver_create_201_and_bronze_reject -x -q` | 1 passed |

## 决策

1. **DB schema 改动是必须的**：本 change 与 W1-1 不同——不是改名而是新加字段；用最小 alembic migration 加 2 个 nullable 列（向后兼容）。
2. **schema_id 注册预填 2 个**（silver-text-v1 / gold-sft-v1）：覆盖 silver + gold 各一个标杆；其他 schema（如 dialog / dpo-pair）留给 W2-* / W4-* 时按需增加。
3. **bronze 必不带 schema_id**：bronze 的"文件树"语义不需要 schema（pivot 永不做清单中"不撤 bronze 强 schema"指的是不强制；这里反向也禁止）；422 兜底而非默默接收 None。
4. **422 而非 400**：FastAPI 默认对 Pydantic 校验 fail 返 422；本 change 自己 raise 时也用 422 保持一致。
5. **schema 跨层禁止**：silver schema 不能注册到 gold repo（避免误用）；`SchemaRegistry.get(schema_id).layer == repo.layer` 是硬约束。

## 风险

| 风险 | 缓解 |
|---|---|
| alembic migration 序列号冲突 | sonnet 生成时跑 `alembic revision --autogenerate` 让 sqlalchemy 自动选 down_revision；不手填 |
| 既有测试创建 silver/gold repo 无 schema_id → 全部 422 fail | 既有测试主要用 bronze（W1-1 全用 bronze）；如有少量 silver/gold 测试，sonnet 修测试加 schema_id="silver-text-v1" + row_format="parquet"（属合理回归） |
| W1-4 loader-refactor-pdf-mineru 时 silver schema 真要写 row → 现在没 row 校验 | Out of scope 已声明；W1-4 写 SilverRow 后由 Pydantic 自身校验；schema_id 强 row schema 是 W2-5 的事 |
