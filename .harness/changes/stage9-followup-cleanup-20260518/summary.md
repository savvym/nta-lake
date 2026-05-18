---
change_id: stage9-followup-cleanup-20260518
title: stage 9 余波合并修复：pipeline_cache FK CASCADE + test fixture 撞 commit hash 隔离
owner: application-owner-agent
started_at: 2026-05-18T10:40:00Z
stage: done
status: closed
last_updated: 2026-05-18T12:15:00Z
related_changes:
  - pipeline-orchestrator-mvp-20260518
  - harness-ac-behavioral-tier-20260518
---

# Summary

> 这是本变更的 Single Source of Truth。任何阶段开始 / 通过 / 失败都必须同步更新这里。

## 一句话目标

修两个 `pipeline-orchestrator-mvp-20260518` stage 9 暴露的真 bug：
(1) `pipeline_cache.output_commit_hash` FK `ondelete=RESTRICT` → 删 repo/commit 触发 FK violation 500；
(2) `test_pipeline_orchestrator._seed_bronze` 用 hardcoded `b"x\n"` / `b"hello\r\nworld\r\n"` 等固定 content 创建 commit，**全局 sha256 commit hash 不带 repo_id**，与 stage 9 demo 跑过的同 content 撞 unique constraint → 本机 dev 跑 demo 后必撞，CI clean DB 不显问题但脆弱。

## 范围摘要

- **In scope**：
  - AC-1：`pipeline_cache.output_commit_hash` FK 改 `ondelete=CASCADE`（model + alembic 0005 migration）；删 commit 时自动删 cache 行（cache_key 指向无效 commit 无意义）
  - AC-2：`apps/api/tests/test_pipeline_orchestrator.py::_seed_bronze` 内部给 content 前缀 uuid hex 让全局 hash 唯一；保留外部 `content: bytes` 参数语义（测试不依赖原 content 字串，断言只检查 metadata 字段）
  - AC-3：真跑 `test_pipeline_orchestrator.py` 全部测试 PASS（特别是 test_cache_hit_*，stage 9 后曾 FAIL 三测试）
  - AC-4：真跑 `DELETE /repos/<owner>/<name>` 删带有 pipeline_cache 引用的 repo → 不再 FK violation 500
  - AC-5：dogfood 新规约——本 spec 至少 1 条 behavioral AC（AC-3 + AC-4 都是 L2 ASGITransport / pytest 集成 behavioral）

- **Out of scope**：
  - `_seed_bronze` 之外的其他测试 fixture 普查 → follow-up `test-fixture-isolation-other-files-*`（如有累积才做；stage 9 实证仅 test_pipeline_orchestrator 撞）
  - 历史 alembic migration 改写（0004） → 单独 0005 升级 migration，不改 0004
  - `harness-lint-ac-yaml-load-test-*`（demo recipe 真跑校验）→ 部分被 change #1 AC-4 behavioral fixture pattern 解决；独立的"yaml 加载校验"留 follow-up
  - pipeline UI / lineage 可视化（属 change #3 / #4）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done | v3 | — | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | done | v3 | APPROVED | v1: [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) ; v2: [spec_review_v2.md](request_analysis/review/spec_review_v2.md) · [tasks_review_v2.md](request_analysis/review/tasks_review_v2.md) ; v3: [spec_review_v3.md](request_analysis/review/spec_review_v3.md) · [tasks_review_v3.md](request_analysis/review/tasks_review_v3.md) |
| 3 编码实现 | done | v1 | — | [coding_report_v1.md](coding/coding_report_v1.md) — 4/4 AC PASS（含 cache_hit 3 全 PASS）；全仓 self_check **252/252 FAIL=0**（项目史上首次）；stage 3 偏离：扩展 `_delete_repo_cascade` 加跨 repo refs 清理（accept 作 fixture-isolation 扩展） |
| 4 编码评审 | pending | — | — | code_review_v1.md |
| 5 单测编写 | done | v1 | — | [test_report_v1.md](unit_test/test_report_v1.md) — 4 AC ↔ 测试映射 + 真跑证据 + 5 类覆盖维度 |
| 6 单测评审 | done | v1 | APPROVED | [test_review_v1.md](unit_test/review/test_review_v1.md) — 0 MUST FIX；reviewer 独立真跑 cache_hit 2 测试 + 残留场景手工构造验证 cleanup 不静默 |
| 7 代码推送 | done | v1 | — | main 直接 commit（无 remote） |
| 8 CI 验证 | self-attest | — | — | 项目无 remote 长期未决（同 change #1） |
| 9 部署验证 | done | v1 | PASS | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) — alembic 0005 已 apply 到 dev PG（delete_rule=CASCADE 验证）；pytest 10/10 PASS；全仓 self_check 252/252 FAIL=0 |
| 10 用户确认 | done | v1 | PASS via 授权 | zhhdzhang @ 2026-05-18T08:13:00Z 显式授权"按 1,2,3,4 你自行启动"——本 change #2 在授权范围 |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 |
|---|---|---|
| 2026-05-18 | FK 选 `ondelete=CASCADE` 而非 `SET NULL` | **(a) 技术硬约束**：`PipelineCacheORM.output_commit_hash` 当前 `nullable=False`（model 第 86-90 行），SET NULL 物理违反 NOT NULL，**必须先改 nullable=True 才能用 SET NULL，超出本 change scope**；**(b) 语义**：cache_key 指向无效 commit 无意义；CASCADE 让删 commit 自动失效 cache，语义清 |
| 2026-05-18 | 新建 alembic 0005 migration 而非改写 0004 | 0004 已 close + 部署到 dev，不允许重写历史；0005 ALTER FK constraint 干净（用高层 API `op.drop_constraint` + `op.create_foreign_key`） |
| 2026-05-18 | `_seed_bronze` 内部加 uuid 前缀而非每个调用点改 | 集中修复，所有 6 个调用点自动受益；测试断言依赖 `_seed_bronze` 返回的 commit_hash，content 只在 seed 期被 hashed，不被任何 assertion 读取（v1 reviewer 已实读 6 处 callsite 确认）|
| 2026-05-18 | 选择前缀而非后缀加 uuid | 加在 content 开头，避免影响以换行结尾的内容（markdown 经常以 \n 结尾） |

## 当前阻塞

无（stage 1 in_progress）。

## Deferred 项

> 关闭时填写。

## 交付

> 关闭本变更时填写。

- Branch：main（无 remote）
- PR：N/A
- Merge commit：本 commit（model + 0005 migration + test fixture + self_check block + 完整产物链）
- 部署版本：dev 本机 PG（alembic 0005 已 apply，delete_rule=CASCADE 验证）
- 用户确认：zhhdzhang @ 2026-05-18 显式授权"按 1,2,3,4 你自行启动"
- 关闭时间：2026-05-18T12:15:00Z

## 复盘

> 关闭时填写。
