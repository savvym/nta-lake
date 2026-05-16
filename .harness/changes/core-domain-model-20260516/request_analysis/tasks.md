---
change_id: core-domain-model-20260516
version: 1
authored_at: 2026-05-17T00:10:00Z
---

# Tasks

## 任务清单

```yaml
tasks:
  - id: T-1
    title: packages/core domain - Repository / Layer / Visibility / Subtype Pydantic
    description: Layer Literal["bronze","silver","gold"]；Visibility Literal["private","internal","public"]；Subtype Literal 拆 Bronze/Silver/Gold；Repository BaseModel 字段（id/owner/name/layer/subtype/visibility/card_path?/created_at/updated_at）
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1, AC-2]
    status: pending

  - id: T-2
    title: packages/core domain - Commit / Tree / TreeEntry / BlobRef / Ref / Lineage Pydantic
    description: SHA256 类型别名；BlobRef(sha256, size>=0, storage_key)；TreeEntry/Tree；Commit(hash, repo_id, tree_hash, parents, author_id, created_at, message, lineage?)；Lineage(produced_by, inputs, run_id, env)；ProducedBy(kind, name, version, config_hash)；InputRef(repo, commit)；Ref(repo_id, name, commit_hash)
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-1, AC-3, AC-4, AC-5, AC-6, AC-7]
    status: pending

  - id: T-3
    title: packages/core protocols - SourceAdapter / Processor / RunContext / IngestResult / ProcessResult / RepoView / RepoSelector / RepoSpec
    description: typing.Protocol；按 design.md §4.1 / §4.2 字段签名；RunContext 暴露 llm / logger / metrics / secrets / cancel 占位 attribute
    depends_on: [T-2]
    estimated_stage: coding
    covers_ac: [AC-1, AC-8]
    status: pending

  - id: T-4
    title: apps/api/pyproject.toml +3 依赖
    description: sqlalchemy>=2.0,<3 / alembic>=1.13 / asyncpg>=0.29
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-12]
    status: pending

  - id: T-5
    title: apps/api/dataplat_api/db.py
    description: create_async_engine + async_sessionmaker；engine 从 DATAPLAT_DATABASE_URL 读取
    depends_on: [T-4]
    estimated_stage: coding
    covers_ac: [AC-10]
    status: pending

  - id: T-6
    title: apps/api/dataplat_api/models/base.py
    description: DeclarativeBase + TimestampMixin
    depends_on: [T-4]
    estimated_stage: coding
    covers_ac: [AC-9]
    status: pending

  - id: T-7
    title: apps/api ORM 表 - repositories / commits / trees / tree_entries / refs / blobs
    description: Mapped[]/mapped_column() 风格；commits.lineage_json JSONB；blobs 主键 sha256 hex；其余 UUID 主键
    depends_on: [T-6]
    estimated_stage: coding
    covers_ac: [AC-9]
    status: pending

  - id: T-8
    title: apps/api/alembic.ini + env.py（async pattern）
    description: env.py 用 asyncio.run + connection.run_sync(do_migrations)；target_metadata = Base.metadata
    depends_on: [T-7]
    estimated_stage: coding
    covers_ac: [AC-11]
    status: pending

  - id: T-9
    title: alembic versions/0001_initial_schema.py
    description: 手写（不用 autogen，更可控）；6 张表 + 索引 + 外键约束
    depends_on: [T-7, T-8]
    estimated_stage: coding
    covers_ac: [AC-11, AC-13]
    status: pending

  - id: T-10
    title: packages/core 单测（≥6）
    description: test_repository / test_commit / test_blob / test_tree / test_lineage / test_layer_literal
    depends_on: [T-2]
    estimated_stage: unit_test
    covers_ac: [AC-14]
    status: pending

  - id: T-11
    title: apps/api/tests/test_models.py（ORM smoke ≥ 2）
    description: test_repositories_crud / test_commit_with_lineage_jsonb；docker-compose Postgres
    depends_on: [T-9]
    estimated_stage: unit_test
    covers_ac: [AC-15]
    status: pending

  - id: T-12
    title: scripts/_self_check.sh 追加 core-domain-model block
    description: 17 AC 自检；FILTER 接受 core-domain-model。**含 SKIP 通道**（spec review v3 SHOULD FIX #2）：AC-13/15 在 `pg_isready` 探针失败时输出 `SKIP` 而非 `FAIL`；脚本汇总段需统计 `PASS / FAIL / SKIP` 三类；exit 0 当且仅当 FAIL=0（SKIP 不阻塞）
    depends_on: [T-10, T-11]
    estimated_stage: unit_test
    covers_ac: [AC-17]
    status: pending
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: pending
  - id: P-code-review
    estimated_stage: coding_review
    status: pending
  - id: P-test-review
    estimated_stage: unit_test_review
    status: pending
  - id: P-push
    estimated_stage: push
    status: pending
    reason: 本地 commit
  - id: P-ci
    estimated_stage: ci_result
    status: pending
    reason: 本地等价 scripts/_self_check.sh + alembic 实跑 + pytest
  - id: P-deploy
    estimated_stage: deployment
    status: skipped
    reason: schema 迁移实跑视作充分；无运行时部署面
  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
    reason: 用户会话级授权由 Generator 自我确认
```

## DAG 健全性

- T-2 → T-1（types 共用）
- T-3 → T-2（protocol 引用 domain）
- T-5/T-6 → T-4（依赖 sqlalchemy 安装）
- T-7 → T-6
- T-8/T-9 → T-7
- T-10 → T-2
- T-11 → T-9
- T-12 → T-10, T-11

无循环。

## 验收覆盖矩阵

| AC | 关联任务 |
|---|---|
| AC-1 | T-1, T-2, T-3 |
| AC-2 | T-1 |
| AC-3 | T-2 |
| AC-4 | T-2 |
| AC-5 | T-2 |
| AC-6 | T-2 |
| AC-7 | T-2 |
| AC-8 | T-3 |
| AC-9 | T-6, T-7 |
| AC-10 | T-5 |
| AC-11 | T-8, T-9 |
| AC-12 | T-4 |
| AC-13 | T-9 |
| AC-14 | T-10 |
| AC-15 | T-11 |
| AC-16 | 全部 |
| AC-17 | T-12 |
