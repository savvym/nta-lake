---
change_id: platform-north-star-pivot-20260520
title: 北极星 pivot —— "数据加工厂"取代"data 上加 git"（design.md 重写 + 永不做清单 + 三层算子草图）
owner: application-owner-agent
started_at: 2026-05-20T15:00:00Z
stage: coding
status: in_progress
last_updated: 2026-05-20T15:35:00Z
related_changes:
  - harness-bootstrap-20260516       # design.md 原始来源
  - bootstrap-monorepo-20260516       # design.md §11.3 引用方
  - core-domain-model-20260516        # 实现了 git-like CAS（被本 change 部分 deprecate）
  - rq-worker-skeleton-20260517       # Processor 接口实现（被本 change 拆分为 Loader/Operator）
---

# Summary

> 纯文档 / 治理 change。重写 design.md 落地新北极星：data prep 工厂 + 三层算子 Adapter+Loader+Operator + stats-first + row-level lineage + 永不做清单（branch/merge/cherry-pick/blob-blob lineage/Asset/manifest.yaml）。

## 一句话目标

把 design.md 从"data 上加 git"（lakeFS/Pachyderm 路线）pivot 到"LLM 训练数据工厂"（data-juicer + The Stack 路线），并在 harness rules 里加硬约束防止后续 change 漂回旧方向。

## 范围摘要

- **In scope**：design.md 重写（≥ 6 个新章节 + 老章节标 deprecated） / `.harness/rules/data-not-code-pivot.md` 新文件 / CLAUDE.md 指针更新 / scripts/lint/check_design_north_star.sh 新文件 / self_check 新 block（10 AC）
- **Out of scope**：任何业务代码改动 / API/UI rename / Schema 强制化 / pdf-mineru 重写 / Operator Protocol 实现 / 回写 21 个已闭环 change

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 阶段 commit | 产物 / 报告 |
|---|---|---|---|---|---|
| 1 需求分析 | done | v2 | — | 57bb1a4 | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | done | v2 | APPROVED | — | [spec_review_v2.md](request_analysis/review/spec_review_v2.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) (APPROVED v1) |
| 3 编码实现 | done | v1 | — | TBD | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | waiting_review | — | — | — | [code_review_v1.md](coding/review/code_review_v1.md) |
| 5 单测编写 | done | v1 | — | TBD | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | waiting_review | — | — | — | [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | | | | | _branch / push ref_ |
| 8 CI 验证 | | | | | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | | | | | n/a (doc-only) |
| 10 用户确认 | | | | | _确认人 / 时间_ |

## 关键决策（4 轮对话沉淀）

| 时间 | 决策 | 理由 / 取舍 | 关联 |
|---|---|---|---|
| 2026-05-20 14:30 | process 粒度应"指向文件" | 用户提出；触发 asset vs blob-lineage vs per-file 三框架分析 | spec § 决策日志 |
| 2026-05-20 14:45 | 撤回 BlobDerivation 表（"file→file 派生图"）方案 | 业界（The Stack / Dolma）用 row-embedded provenance，不做 blob 级图 | spec § 决策日志 |
| 2026-05-20 14:55 | 砍 branch / merge / cherry-pick / rollback / row-diff | "data 是流不是代码"；lakeFS/Pachyderm 商业证伪 | spec § 决策日志 + 永不做清单 |
| 2026-05-20 15:00 | 三层算子 Adapter / Loader / Operator + stats-first | data-juicer 模式套北极星天然合拍 | spec § 三层算子模型 |

## 当前阻塞

- 等 stage 2 reviewer

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| 非范围 | API/UI rename Commit→Snapshot | `api-snapshot-rename-*` |
| 非范围 | Operator Protocol 真正落到 packages/core | `operator-protocol-*` |
| 非范围 | silver/gold 强制 schema + source_ref + stats 必填 | `silver-schema-enforce-*` |
| 非范围 | pdf-mineru 重写为 Loader | `loader-refactor-pdf-mineru-*` |
| 非范围 | 3-5 个标杆 Operator（lang-id / perplexity / minhash-dedup） | `operator-suite-mvp-*` |
| 非范围 | Recipe YAML 支持新形态 | `recipe-yaml-v2-*` |
| 非范围 | PDF→MD UI（用户最初的诉求） | `web-pdf-mineru-ui-*`（依赖本 change） |

## 交付

- Branch：`change/platform-north-star-pivot-20260520`
- PR：直 merge（gh PAT 缺 pr:write）
- Merge commit：TBD
- 部署版本：n/a
- 用户确认：TBD
- 关闭时间：TBD
