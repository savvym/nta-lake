---
change_id: silver-schema-enforce-20260520
title: silver/gold repo 创建强制 schema_id + row_format (W1-3)
owner: application-owner-agent
started_at: 2026-05-20T19:35:00Z
phase: design
status: in_progress
last_updated: 2026-05-20T19:35:00Z
related_changes:
  - api-snapshot-rename-20260520 (W1-1, merged a51a126)
  - operator-protocol-20260520 (W1-2, merged af8a7d5)
  - loader-refactor-pdf-mineru-20260520 (W1-4, downstream)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。

## 一句话目标

silver/gold repo 创建强制必带已注册 schema_id + row_format ∈ {parquet, jsonl}；bronze 必不带；DB 加 2 nullable 列 + alembic 单 migration。

## 范围摘要

- **In scope**：SchemaRegistry (packages/core) + 2 个 builtin schema 注册 + Repository ORM/Pydantic 加字段 + alembic migration + RepoService.create 422 enforcement + pytest 3 个 behavioral 用例
- **Out of scope**：不改 commit/snapshot 写入校验；不实现 row 校验；不动 web/SDK；不强制老 repo 迁移

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | _待填_ | [design.md](design.md) |
| Phase 2 Implementation | sonnet | pending | — | _待填_ | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | pending | — | _待填_ | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-20 19:35 | 加 DB 2 列 + alembic migration | schema_id/row_format 必须持久化；nullable=True 老 row 兼容 | design.md § 决策 1 |
| 2026-05-20 19:35 | 仅预注册 silver-text-v1 + gold-sft-v1 | 标杆覆盖；其他 schema 按需 | design.md § 决策 2 |
| 2026-05-20 19:35 | bronze 必不带 schema_id | 文件树语义；422 兜底 | design.md § 决策 3 |

## 交付（merge 时回填）

- Branch：`change/silver-schema-enforce-20260520`
- Merge commit：_待填_
- 关闭时间：_待填_
