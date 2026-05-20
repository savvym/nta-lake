---
change_id: gold-loader-hf-datasets-20260520
title: gold loader HF datasets (W3-7)
owner: application-owner-agent
started_at: 2026-05-21T07:00:00Z
phase: verify
status: verify_approved
last_updated: 2026-05-21T09:00:00Z
related_changes:
  - dataset-export-engine-20260520 (W2-6, 上游 silver snapshot 写入方)
  - loader-jsonl-20260520 (W3-6, 类似 jsonl 解析但 fail-fast 语义不同)
  - operator-protocol-20260520 (W1-2, SilverRow schema)
  - loader-refactor-pdf-mineru-20260520 (W1-4, BlobStore Protocol)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。Wave 3 收官 change；packages/core 第二批业务依赖（datasets>=2.14,<4，继 W3-5 的 python-docx/pptx 之后）。

## 一句话目标

新增 `exporters/hf_datasets.py`：`async export_to_hf_datasets(silver_blob_sha, target_path, store)` → 从 W2-6 写出的 silver JSONL blob 反序列化 + `Dataset.save_to_disk(...)` → 落 HF datasets 兼容目录（dataset_info.json + Arrow shards），供 SFT/CPT 训练直接 `load_from_disk`。

## 范围摘要

- **In scope**：exporters/__init__.py + exporters/hf_datasets.py（HfDatasetExportResult + export_to_hf_datasets）+ pyproject.toml 加 datasets>=2.14,<4 + 4 个 behavioral pytest（happy + fields + empty + malformed）
- **Out of scope**：不接 apps/api；不做多 split / push-to-hub / 强制 parquet；不擦 target_path；不改 W2-6 dataset.py / W3-1..6 任何产物；不做 manifest.yaml（D-1）

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | c076eeb | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | n/a | 8cfdfe1 + 7eebd19 | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | _待回填_ | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 07:00 | 新建 exporters/ 目录 | 与 adapters/loaders/operators/ 同层；gold 派生分离 | design.md § 决策 1 |
| 2026-05-21 07:00 | 消费 silver_blob_sha 而非 rows | 保留 CAS 不可变血缘 | design.md § 决策 2 |
| 2026-05-21 07:00 | 引入 datasets>=2.14,<4 | HF 训练侧标准入口 | design.md § 决策 3 |
| 2026-05-21 07:00 | 默认 Arrow 而非 parquet | save_to_disk 默认；load_from_disk 原生支持 | design.md § 决策 4 |
| 2026-05-21 07:00 | save_to_disk 同步直接调不嵌 executor | 粗粒度操作；datasets 库内部已优化 | design.md § 决策 5 |
| 2026-05-21 07:00 | 坏行 fail-fast vs W3-6 skip | silver 是 CAS 内部产物，坏行表示故障 | design.md § 决策 6 |
| 2026-05-21 07:00 | split 参数占位不实际使用 | 给 follow-up 留签名 | design.md § 决策 10 |
| 2026-05-21 07:00 | 不做 dataset-card.yaml | D-1 永不做清单 | design.md § 决策 9 |

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up (design) | apps/api routes | `gold-exporter-hf-route-*` |
| follow-up (design) | 多 split 拆分 | `gold-exporter-hf-multi-split-*` |
| follow-up (design) | push 到 HuggingFace Hub | `gold-exporter-hf-push-*` |
| follow-up (design) | 纯 parquet shards | `gold-exporter-parquet-*` |
| follow-up (design) | silver 流式导出 | `silver-snapshot-streaming-export-*` |

## 交付（merge 时回填）

- Branch：`change/gold-loader-hf-datasets-20260520`
- Merge commit：`09aa977`
- 关闭时间：2026-05-21T09:15:00Z
