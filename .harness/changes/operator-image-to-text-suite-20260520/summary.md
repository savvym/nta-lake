---
change_id: operator-image-to-text-suite-20260520
title: image-to-text Operator suite (W2-3)
owner: application-owner-agent
started_at: 2026-05-20T23:40:00Z
phase: design
status: approved
last_updated: 2026-05-20T23:40:00Z
related_changes:
  - operator-protocol-20260520 (W1-2, Operator Protocol)
  - loader-refactor-pdf-mineru-20260520 (W1-4, images schema 来源)
  - operator-suite-mvp-20260520 (W2-1, auto-register + lineage 模式)
  - operator-chunker-20260520 (W2-2, row.model_copy 模板)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。

## 一句话目标

落 2 个多模态 Operator（image_strip / image_caption_stub），建立 SilverRow.images → 文本注入的算子模式（1→1）。

## 范围摘要

- **In scope**：image_strip.py + image_caption_stub.py 实现 + __init__.py 加 2 个注册 + pytest 4 个 behavioral 用例
- **Out of scope**：不调真 LLM caption / OCR / VQA；不读图片 blob 字节；不动 W2-1/W2-2 Operator；不接 worker

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | _待填_ | [design.md](design.md) |
| Phase 2 Implementation | sonnet | pending | — | _待填_ | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | pending | — | _待填_ | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-20 23:40 | 2 个 Operator 一并落地不拆 change | 同款属性 + run() 模板；W2-1 三合一同模式 | design.md § 决策 1 |
| 2026-05-20 23:40 | LLM 调用全留 follow-up | 与 W2-1 ScoreOperator 不调 LLM 同模式 | design.md § 决策 2 |
| 2026-05-20 23:40 | caption_stub 用 filename + blob_sha 占位符 | 演示 image metadata → text 模式 | design.md § 决策 3 |
| 2026-05-20 23:40 | strip / caption 解耦 | 两种正交意图；caller 可串 caption→strip | design.md § 决策 4 |
| 2026-05-20 23:40 | images=[] 时仍追加 lineage_ops | 保 lineage 完整性 | design.md § 决策 5 |

## 交付（merge 时回填）

- Branch：`change/operator-image-to-text-suite-20260520`
- Merge commit：_待填_
- 关闭时间：_待填_
