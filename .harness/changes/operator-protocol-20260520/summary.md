---
change_id: operator-protocol-20260520
title: Operator Protocol + Registry + identity Operator (W1-2)
owner: application-owner-agent
started_at: 2026-05-20T19:00:00Z
phase: design
status: in_progress
last_updated: 2026-05-20T19:00:00Z
related_changes:
  - api-snapshot-rename-20260520 (W1-1, merged a51a126)
  - silver-schema-enforce-20260520 (W1-3, downstream)
  - loader-refactor-pdf-mineru-20260520 (W1-4, downstream)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）：application-owner 自写 design；不 spawn Phase 1 reviewer；Phase 2 sonnet 端到端；Phase 3 opus 跑 pytest 验收。

## 一句话目标

落 Operator Protocol（row→row）+ OperatorRegistry + identity 标杆 Operator；Loader Protocol + SilverRow 一并落地占位。

## 范围摘要

- **In scope**：3 新 protocol 文件 (loader.py / operator.py / operators/registry.py) + identity Operator + test_operator_protocol.py（3 个 behavioral 用例）
- **Out of scope**：不写真正 Loader / Filter / Dedup Operator；不动 Processor / Adapter；不动 plugins / worker

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | _待填_ | [design.md](design.md) |
| Phase 2 Implementation | sonnet | pending | — | _待填_ | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | pending | — | _待填_ | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-20 19:00 | 应用 v3 mini-design 流程 | D-13 授权，效率优先 | decisions.md D-13 |
| 2026-05-20 19:00 | Loader Protocol + SilverRow 一起落地 | W1-3/W1-4 强依赖 SilverRow 定型 | design.md § 决策 1 |
| 2026-05-20 19:00 | Operator.run 返 `list[SilverRow]`（不返 row \| None） | 覆盖 1→0/1→1/1→N | design.md § 决策 2 |

## 交付（merge 时回填）

- Branch：`change/operator-protocol-20260520`
- Merge commit：_待填_
- 关闭时间：_待填_
