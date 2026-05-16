---
change_id: core-domain-model-20260516
title: Pydantic 领域模型 + SQLAlchemy ORM + Alembic 首迁移：Repository / Commit / Tree / Blob / Ref
owner: zhhdzhang
started_at: 2026-05-17T00:00:00Z
stage: coding
status: in_progress
last_updated: 2026-05-17T01:00:00Z
related_changes:
  - bootstrap-monorepo-20260516
---

# Summary

## 一句话目标

按 [.harness/design.md](../../design.md) §2 / §4.4 落地 dataplat 的核心领域模型：在 `packages/core/src/dataplat_core/domain/` 与 `protocols/` 下定义 Pydantic 模型与协议；在 `apps/api/dataplat_api/models/` 下定义 SQLAlchemy 2.0 async ORM；用 Alembic 生成首个 migration，让 `make migrate` 在 docker-compose dev 起的 Postgres 上跑通。

## 范围摘要

- **In scope**：
  - `packages/core/src/dataplat_core/domain/`：Repository / Layer / Subtype / Visibility / Commit / Tree / TreeEntry / BlobRef / Ref / Lineage / ProducedBy Pydantic 模型
  - `packages/core/src/dataplat_core/protocols/`：SourceAdapter / Processor / RunContext / IngestResult / ProcessResult / RepoView / RepoSelector / RepoSpec 协议
  - `apps/api/dataplat_api/models/`：SQLAlchemy DeclarativeBase + repositories / commits / trees / tree_entries / refs / blobs 表
  - `apps/api/alembic/`：env.py（async） + alembic.ini + `versions/0001_initial_schema.py`
  - `packages/core/tests/`：Pydantic 序列化 / sha256 计算 / Lineage 嵌入 commit 等单元测试
  - `apps/api/tests/test_models.py`：ORM CRUD smoke（依赖 docker-compose Postgres）
  - apps/api/pyproject.toml 增加依赖：sqlalchemy>=2.0 / alembic / asyncpg
  - apps/api/dataplat_api/db.py：async engine + session factory
- **Out of scope**：
  - CAS BlobStore 实际实现（留给 `cas-storage-<yyyymmdd>`）
  - Repository / Commit CRUD HTTP 路由（留给 `repo-api-mvp-<yyyymmdd>`）
  - users 表与认证（留给 `auth-scaffold-<yyyymmdd>`）
  - Lineage 图查询服务（留给后续）
  - Schema Registry（Silver/Gold 层 schema）（留给独立变更）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done（v1→v2→v3 三轮就地修：MUST FIX 5 + SHOULD FIX 6 全消化）| v3 | — | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | **done** | v3 | **APPROVED**（MUST FIX=0；spec v1: 4→0、v2: 1→0、v3: 0；tasks v1: 2→0、v2/v3: 0；4 次实证"AC 命令未实跑校验"已纳入 [[project-followup-harness-lint]]）| [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [spec_review_v2.md](request_analysis/review/spec_review_v2.md) · [spec_review_v3.md](request_analysis/review/spec_review_v3.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) · [tasks_review_v2.md](request_analysis/review/tasks_review_v2.md) |
| 3 编码实现 | pending | — | — | — |
| 4 编码评审 | pending | — | — | — |
| 5 单测编写 | pending | — | — | — |
| 6 单测评审 | pending | — | — | — |
| 7 代码推送 | pending | — | — | — |
| 8 CI 验证 | 本地等价 | — | — | — |
| 9 部署验证 | skipped: 无部署面（schema 迁移在 stage 5 实跑 docker-compose Postgres 已视作充分） | — | — | — |
| 10 用户确认 | 用户会话级授权 Generator 自我确认 | — | — | — |

## 关键决策

| 时间 | 决策 | 理由 |
|---|---|---|
| 2026-05-17 | Pydantic 模型放 `packages/core/`，ORM 放 `apps/api/dataplat_api/models/` | design.md §11.3：core 是后端 / SDK / worker 共用；ORM 是后端私有 |
| 2026-05-17 | 从 day 1 用 async SQLAlchemy + asyncpg | design.md §11.7 第 1 条：同步模式迁移成本极高 |
| 2026-05-17 | Alembic env.py 兼容 sync + async（用 run_sync 包装）| Alembic 本身 sync；async engine 用 `connection.run_sync(...)` |
| 2026-05-17 | ORM 表用 UUID 主键（design.md §2 / §4.4 commits/blobs 用 sha256 即天然 PK 候选）| 简化外键 + 与 §4.4 一致 |
| 2026-05-17 | Lineage 用 JSONB 嵌在 commit 行（design.md §4.4 lineage 字段 + §8 决策表"血缘 (a) PG 表起步"）| 一行查到 commit + lineage；后期可加 `lineage_edges` 衍生表用于图查询 |

## 当前阻塞

- Stage 1 进行中。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX（spec review v1 沿留 #1）| `make up` 失败时 Postgres 不可用 → AC-13/15 失败语义不清晰 | 已在 v3 修：`pg_isready` 探针 + SKIP 通道；T-12 加 SKIP 实施（见下）|
| SHOULD FIX（spec review v1 沿留 #2 后半）| ORM `created_at`/`updated_at` 触发器 vs 应用层时间戳 | follow-up：`repo-api-mvp` 引入业务路由时根据写入路径决定；本变更 ORM 用 `onupdate=func.now()` 应用层简方案 |
| SHOULD FIX（spec review v1 沿留 #6）| `git commit -a` 包括 `__pycache__` —— Generator 应用 .gitignore（已含），需 stage 7 实跑前再 `git status` 复检 | stage 7 行内复检；不开 follow-up |
| SHOULD FIX（spec review v3 #1）| AC-16 §范围描述 vs 验证方式收窄不同步 | follow-up：下次 spec 模板修订时把"范围描述↔验证方式"同步纳入"全仓 grep 同模式"规则 |
| SHOULD FIX（spec review v3 #2）| T-12 description 当前未写"加 SKIP 通道" | **stage 3 编码前补一句**（见下方 T-12 更新） |
| NICE TO HAVE（v1 沿留 + v3 沿留）| Lineage 拆 lineage_edges 衍生表（图查询效率）/ ProducedBy.config 完整序列化 vs 仅 hash | follow-up：`lineage-query-graph-<yyyymmdd>` 或 Phase 2+ 图数据库迁移 |
