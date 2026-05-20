---
change_id: api-snapshot-rename-20260520
title: API / SDK / UI Commit→Snapshot rename
owner: application-owner-agent
started_at: 2026-05-20T08:37:00Z
phase: design
status: in_progress
last_updated: 2026-05-20T16:45:00Z
related_changes:
  - platform-north-star-pivot-20260520
  - operator-protocol-20260520
---

# Summary

> 三阶段简化流程下，本文件是 SoT。每阶段开始 / 通过 / 失败都同步这里。

## 一句话目标

API / SDK / UI 把 Commit 改成 Snapshot；parents 列表退化为 parent 单链。

## 范围摘要

- **In scope**：
  - `apps/api` routers (`commits.py` → `snapshots.py`) + schemas (`commit.py` → `snapshot.py`) + `main.py` import + `RefRead.commit_hash` → `snapshot_hash`
  - 端点路径 `/repos/{o}/{n}/commits[/{hash}]` → `/repos/{o}/{n}/snapshots[/{hash}]`；老路径加 308 redirect 兼容
  - 字段 `parents: list[SHA256]` → `parent: SHA256 \| None`
  - `packages/api-types/openapi.json` + `generated.ts` 重新生成
  - `packages/sdk-py` client `create_commit` → `create_snapshot` + `--parent` flag；cli 子命令组 `commit` → `snapshot`
  - `apps/web` 路由 flat-dot 改 folder：`routes/snapshots/$owner.$name.$hash.tsx`；`queries.ts` 内 `CommitRead` / `useCommit` → `SnapshotRead` / `useSnapshot`；所有 `<Link to="/commits/...">` 改 `/snapshots/...`
  - `scripts/_self_check.sh` 新增 `run_api_snapshot_rename` block + case 派发
- **Out of scope**：DB schema 不动（ORM / alembic / `commits` 表 / `RefORM.commit_hash` 列保留）；`models/refs.py` 不清理；processors / adapters / lineage / pipeline 字段不动；v1 闭环 change self_check 块不回写

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus | reviewing | — | — | [design.md](design.md) · design_review.md (pending) |
| Phase 2 Implementation | sonnet | pending | — | — | implementation.md (pending) |
| Phase 3 Verify | opus | pending | — | — | verify_review.md (pending) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-20 16:30 | DB schema 不动；只动 API / SDK / UI 三层 | v1 commit-api-mvp 已闭环 + alembic 迁移代价 >> 改名收益 | design.md § 决策日志 + decisions.md D-1 |
| 2026-05-20 16:31 | 路径风格 `/snapshots/{hash}` 复数 + 单数 hash | 与 `/blobs/{sha}` / `/trees/{tree_hash}` REST 习惯一致 | design.md § 决策日志 |
| 2026-05-20 16:32 | 兼容期 308 redirect，不做并行响应 | method-preserving + 无 schema 维护翻倍 | design.md § 决策日志 |
| 2026-05-20 16:33 | `parents: list[str]` → `parent: str \| None` 仅 API 层；DB 列保留 list | data-not-code-pivot.md 旧→新术语表 | design.md § 决策日志 |
| 2026-05-20 16:34 | api-types 27 处不手改，跑生成器重生 | `scripts/export_openapi.py` + pnpm generate 已就绪 | design.md § 决策日志 |
| 2026-05-20 16:35 | web 路由 flat-dot 改 folder 形式 | MEMORY feedback_tanstack_routing_folder_form 偏好 + 为后续 list 页让路 | design.md § 决策日志 |
| 2026-05-20 16:36 | `models/refs.py` 不清理：实际无 `/branches` 复数 API | grep 证实 routes 无 `/branches/` 字面值；不超 scope | design.md § 决策日志 |

## 当前阻塞

无。等待 Phase 1 opus reviewer。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up | 删 308 redirect 端点 | `api-snapshot-rename-cleanup-*`（W2 结束前） |
| follow-up | 可选 DB 列改名（commits → snapshots） | `db-snapshot-rename-*`（按需） |
| follow-up | pipeline / lineage 字段词汇统一 | W2-5 `recipe-yaml-v2-20260520` |

## 交付（merge 时回填）

- Branch：`change/api-snapshot-rename-20260520`
- PR：<链接>
- Merge commit：`<sha>`
- 用户确认（如适用）：<人 / 时间>
- 关闭时间：<YYYY-MM-DDTHH:MM:SSZ>

## 复盘（可选）

- 哪些顺利
- 哪些踩坑：根因 + 防复发（落到 .harness/rules/ 或 .harness/skills/）
