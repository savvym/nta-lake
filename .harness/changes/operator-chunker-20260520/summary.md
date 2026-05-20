---
change_id: operator-chunker-20260520
title: ChunkerOperator 1→N 切分语义 (W2-2)
owner: application-owner-agent
started_at: 2026-05-20T22:05:00Z
phase: verify
status: approved
last_updated: 2026-05-20T23:30:00Z
related_changes:
  - operator-protocol-20260520 (W1-2)
  - operator-suite-mvp-20260520 (W2-1, auto-register 模式参考)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。

## 一句话目标

落 `ChunkerOperator`，按 max_chars 切 1 个 SilverRow 成 N 个新 row（演示 1→N 语义）。

## 范围摘要

- **In scope**：chunker.py 实现按字符数硬切 + __init__.py 加注册 + pytest 4 个 behavioral 用例
- **Out of scope**：不做句子/token/overlap 边界切分；不动 W2-1 Operator；不接 worker；v1 不做 grapheme-aware 计数

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | 614b9dc | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | 9a6803f | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | (review only) | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-20 22:05 | v1 按字符硬切；不做句子/token/overlap | 1→N 标杆；smart chunker 留 follow-up | design.md § 决策 1 |
| 2026-05-20 22:05 | 空 text 返 [] (drop empty) | 与 filter 1→0 呼应 | design.md § 决策 2 |
| 2026-05-20 22:05 | chunk_index/chunk_total 进 stats | 不引新 SilverRow 字段；保 schema 稳定 | design.md § 决策 3 |
| 2026-05-20 22:05 | 切片共享 source_ref / images | 仍指向同一 bronze blob | design.md § 决策 4 |
| 2026-05-20 22:05 | max_chars 必填 (jsonschema required) | 强制 caller 显式选粒度 | design.md § 决策 6 |

## 交付（merge 时回填）

- Branch：`change/operator-chunker-20260520`
- Merge commit：_待填_
- 关闭时间：_待填_
