---
change_id: operator-suite-mvp-20260520
title: filter / dedup / score 三个 MVP Operator (W2-1)
owner: application-owner-agent
started_at: 2026-05-20T21:30:00Z
phase: verify
status: approved
last_updated: 2026-05-20T21:50:00Z
related_changes:
  - operator-protocol-20260520 (W1-2, Operator Protocol + IdentityOperator 标杆)
  - loader-refactor-pdf-mineru-20260520 (W1-4, auto-register 模式参考)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。

## 一句话目标

落 3 个 MVP Operator（filter / dedup / score），实现 Operator Protocol，注册进 OperatorRegistry，作为 Operator 层第一批实用算子。

## 范围摘要

- **In scope**：3 个新 Operator 类 (filter / dedup / score) + operators/__init__.py 自动注册 4 个 (含 identity) + pytest 4 个 behavioral 用例
- **Out of scope**：不实现 chunker / image-to-text / snapshot-mixer / recipe v2；不接 worker 调度；不正式扩 RunContext Protocol；不做 LLM 评分

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | 614ce13 | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | a4e5779 | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | (review only) | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-20 21:30 | 3 个 Operator 一并落地不拆 change | 同款属性 + run() 模板；粒度等同 W1-3 一次落 SchemaRegistry + 2 builtin | design.md § 决策 1 |
| 2026-05-20 21:30 | dedup state 暂用 ctx attribute hack | RunContext 形式化扩展是 W2-5 范围 | design.md § 决策 2 |
| 2026-05-20 21:30 | score 仅本地确定性算法（text_chars / alpha_ratio） | LLM 打分是 W4-8；本 change 演示 stats 写入 + 行级血缘 | design.md § 决策 3 |
| 2026-05-20 21:30 | operators/__init__.py 一并加 identity 自动注册 | 与 loaders 模式对齐；W1-2 test 用唯一 key 不冲突 | design.md § In scope |

## 交付（merge 时回填）

- Branch：`change/operator-suite-mvp-20260520`
- Merge commit：_待填_
- 关闭时间：_待填_
