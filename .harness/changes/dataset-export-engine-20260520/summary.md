---
change_id: dataset-export-engine-20260520
title: dataset export engine (W2-6)
owner: application-owner-agent
started_at: 2026-05-21T01:50:00Z
phase: verify
status: approved
last_updated: 2026-05-21T02:10:00Z
related_changes:
  - recipe-yaml-v2-20260520 (W2-5, RecipeRunResult 上游)
  - loader-refactor-pdf-mineru-20260520 (W1-4, BlobStore Protocol)
  - operator-protocol-20260520 (W1-2, SilverRow)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。

## 一句话目标

落 packages/core/dataset.py：serialize_rows_to_jsonl + async export_silver_snapshot，把 RecipeRunResult.rows 序列化为 JSONL 字节并 PUT 进 BlobStore。

## 范围摘要

- **In scope**：dataset.py 新增 SnapshotExportResult + serialize_rows_to_jsonl + export_silver_snapshot + 4 个 behavioral pytest
- **Out of scope**：不接 repo refs（silver/owner/name@ref 挂载留 follow-up）；不接 apps/api；不接 worker；不实现 schema fingerprint；不做 chunked / streaming upload；不做 Parquet 列存

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | 2865aee | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | 44df71c + f4ea4a0 | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | ebe402d | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 01:50 | core-only，不接 repo / API | 与 W2-5 同模式；silver-owner-name-ref 跨模块 | design.md § 决策 1 |
| 2026-05-21 01:50 | JSONL 而非 Parquet/Arrow | 训练数据通用；HF datasets 直接消费；schema-free 兼容演化 | design.md § 决策 2 |
| 2026-05-21 01:50 | BlobStore Protocol 抽象，不直调 Minio | core 不依赖 apps/api；测试 stub | design.md § 决策 4 |
| 2026-05-21 01:50 | async exporter | BlobStore.put 是 async；I/O 性质自然 | design.md § 决策 5 |
| 2026-05-21 01:50 | 空 dataset 仍写空 blob | 视为 feature；caller 显式表达"导出空集" | design.md § 决策 + AC-4 |

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| NICE TO HAVE (verify) | silver/owner/name@ref tree entry 挂载 | follow-up `silver-snapshot-repo-binding-*` |
| NICE TO HAVE (verify) | generator + 多 part 流式 export | follow-up `silver-snapshot-streaming-export-*` |
| NICE TO HAVE (verify) | dataset metadata 加 schema 指纹 | follow-up `silver-snapshot-schema-fingerprint-*` |

## 交付（merge 时回填）

- Branch：`change/dataset-export-engine-20260520`
- Merge commit：_待 merge 后填_
- 关闭时间：_待填_
