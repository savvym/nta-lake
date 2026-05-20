---
change_id: silver-schema-enforce-20260520
phase: implementation
status: done
authored_at: 2026-05-20T18:10:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/silver-schema-enforce-20260520
base_commit: e058174
head_commit: 4580a9d
pr_url: n/a
---

# Implementation

## 做了什么

新增 SchemaRegistry + 2 builtin schemas；API 层强制 silver/gold repo 创建带合法 schema_id+row_format，bronze 不允许带。DB 加 2 个 nullable 列 + alembic migration。

## 改动文件清单

| 路径 | 类型 | 说明 |
|---|---|---|
| `packages/core/src/dataplat_core/schemas/__init__.py` | new | SchemaRegistry 公开 API + 触发 _builtin 注册 |
| `packages/core/src/dataplat_core/schemas/registry.py` | new | SchemaRegistry + SchemaEntry 实现 |
| `packages/core/src/dataplat_core/schemas/silver_row.py` | new | SilverRow re-export（从 protocols.loader） |
| `packages/core/src/dataplat_core/schemas/gold_row.py` | new | GoldSFTRow Pydantic |
| `packages/core/src/dataplat_core/schemas/_builtin.py` | new | 预注册 silver-text-v1 + gold-sft-v1 |
| `packages/core/tests/test_schema_registry.py` | new | AC-1 单元测试 |
| `apps/api/dataplat_api/models/repository.py` | edit | 加 schema_id / row_format nullable 列 |
| `apps/api/dataplat_api/schemas/repo.py` | edit | RepositoryCreate/Read/ListItem 加两字段 |
| `apps/api/dataplat_api/services/repo.py` | edit | create 加 schema_id+row_format enforcement + SchemaRegistry 引入 |
| `apps/api/dataplat_api/routers/repos.py` | edit | _to_read / _to_list_item 同步取两字段 |
| `apps/api/alembic/versions/3cc849b1c472_add_schema_id_row_format_to_repositories.py` | new | add schema_id row_format to repositories (nullable) |
| `apps/api/tests/test_repo_schema_enforcement.py` | new | AC-2 + AC-3 集成测试 |
| `apps/api/tests/test_repos.py` | edit | test_d / test_n silver repo 创建加 schema_id+row_format（合理回归） |
| `apps/api/tests/test_pipeline_e2e.py` | edit | _create_silver_repo helper 加 schema_id+row_format |
| `apps/api/tests/test_pipeline_orchestrator.py` | edit | _create_silver_repo helper 加 schema_id+row_format |

## 测试通过证据

### packages/core 单元测试

```
$ cd packages/core && uv run pytest tests/test_schema_registry.py -x -q
1 passed in 0.09s

$ uv run pytest tests/ -q
37 passed in 0.24s
```

### apps/api 集成测试

```
$ cd apps/api && uv run pytest tests/test_repo_schema_enforcement.py -x -q
2 passed in 1.55s

$ uv run pytest tests/test_repos.py tests/test_snapshots_api.py tests/test_repo_schema_enforcement.py -q
18 passed in 8.63s
```

### pyright

```
$ cd apps/api && uv run pyright dataplat_api/ tests/test_repo_schema_enforcement.py 2>&1 | tail -5
0 errors, 0 warnings, 0 informations

$ cd packages/core && uv run pyright src/ tests/test_schema_registry.py 2>&1 | tail -5
0 errors, 0 warnings, 0 informations
```

### alembic migration

revision: `3cc849b1c472`，down_revision: `0005`，
`op.add_column("repositories", sa.Column("schema_id", sa.String(), nullable=True))`
`op.add_column("repositories", sa.Column("row_format", sa.String(), nullable=True))`，
升级已成功 `0005 -> 3cc849b1c472`。

## 偏离 design.md

| # | 偏离点 | 原因 |
|---|---|---|
| D-1 | alembic autogenerate 同时生成了 jobs/pipeline_node_runs/pipeline_runs 的 TEXT→String type change | autogenerate noise（实际无 schema 变化）；3 个 alter_column 无副作用，不影响业务 |

## 老测试改动声明（合理回归）

| 文件 | 改动 | 说明 |
|---|---|---|
| `apps/api/tests/test_repos.py` | test_d + test_n silver repo 加 `schema_id`+`row_format` | 新强制校验生效；加字段是合理回归 |
| `apps/api/tests/test_pipeline_e2e.py` | `_create_silver_repo` helper 加两字段 | 同上 |
| `apps/api/tests/test_pipeline_orchestrator.py` | `_create_silver_repo` helper 加两字段 | 同上 |

注：全量 apps/api 测试套件有 42 个预存失败（308 redirect / ingest KeyError / pipeline 相关），均为 W1-1 前就有或其他 change 遗留问题，与本 change 无关（git stash 验证确认）。

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 PR。
