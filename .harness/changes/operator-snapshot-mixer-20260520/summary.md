---
change_id: operator-snapshot-mixer-20260520
title: snapshot mixer Operator suite (W2-4)
owner: application-owner-agent
started_at: 2026-05-21T00:05:00Z
phase: design
status: approved
last_updated: 2026-05-21T00:05:00Z
related_changes:
  - operator-protocol-20260520 (W1-2, Operator Protocol)
  - operator-suite-mvp-20260520 (W2-1, sha256 哈希 + drop 模式 + stats 写入)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。

## 一句话目标

落 2 个 row 级 Operator（snapshot_tag / snapshot_sample），为 W2-5 recipe v2 跨 snapshot mixing 提供基础原语。

## 范围摘要

- **In scope**：snapshot_tag.py + snapshot_sample.py 实现 + __init__.py 加 2 个注册 + pytest 4 个 behavioral 用例
- **Out of scope**：不实现多流 union（留 W2-5 recipe v2 编排）；不扩 Operator Protocol；不动 W1-* / W2-1..3 Operator；不接 worker；不用随机数

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | _待填_ | [design.md](design.md) |
| Phase 2 Implementation | sonnet | pending | — | _待填_ | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | pending | — | _待填_ | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 00:05 | 2 Operator 一并落，不拆 change | W2-1/W2-3 同模式 | design.md § 决策 1 |
| 2026-05-21 00:05 | 多流 union 留 recipe v2，不扩 Protocol | 保持 row-level 单流抽象 | design.md § 决策 2 |
| 2026-05-21 00:05 | snapshot_sample 用 sha256 确定性哈希 | 训练数据 reproducibility；与 W2-1 dedup 同模式 | design.md § 决策 3 |
| 2026-05-21 00:05 | 不加 statistical AC | 非确定性测试风险高；mid-weight 留 W2-5 集成测 | design.md § 决策 7 |

## 交付（merge 时回填）

- Branch：`change/operator-snapshot-mixer-20260520`
- Merge commit：_待填_
- 关闭时间：_待填_
