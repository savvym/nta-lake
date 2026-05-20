---
change_id: adapter-raw-upload-20260520
title: raw-upload adapter port + AdapterRegistry (W3-1)
owner: application-owner-agent
started_at: 2026-05-21T02:30:00Z
phase: verify
status: approved
last_updated: 2026-05-21T02:50:00Z
related_changes:
  - operator-protocol-20260520 (W1-2, SourceAdapter Protocol)
  - adapter-framework-20260517 (apps/api raw_upload 原版本)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。含 roadmap drift correction：drop dataset-card.yaml AC（违反 D-1 永不做清单）。

## 一句话目标

把 RawFileUploadAdapter 从 apps/api port 到 packages/core/src/dataplat_core/adapters/，新增 AdapterRegistry（与 LoaderRegistry / OperatorRegistry 同模式）。

## 范围摘要

- **In scope**：adapters/registry.py + adapters/raw_upload.py + adapters/__init__.py + 4 个 behavioral pytest
- **Out of scope**：不改 apps/api（私有副本短期保留）；不做 dataset-card.yaml（D-1 永不做清单）；不做新 adapter（W3-2/W3-3）；不做 e2e PDF/DOCX 测试

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | e57f1e0 | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | 1332034 + ea72428 | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | ca0f01c | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 02:30 | core port 而非 in-place evolution | 与 W1-4 PdfMineruLoader 同模式 | design.md § 决策 1 |
| 2026-05-21 02:30 | apps/api 私有副本保留不动 | backward-compat；切换留 follow-up | design.md § 决策 2 |
| 2026-05-21 02:30 | AdapterRegistry 存实例非类 | 与 apps/api/runner/registry.py 既有约定一致 | design.md § 决策 3 |
| 2026-05-21 02:30 | drop "dataset-card.yaml 自动生成" AC | 违反 D-1 永不做清单 manifest.yaml | design.md § 决策 7（drift correction） |

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| NICE TO HAVE (verify) | apps/api 切换到 core registry，删 apps/api 私有副本 | follow-up `adapter-raw-upload-api-bridge-*`（W3-2 前高优） |
| NICE TO HAVE (verify) | "永不做清单" 自动 grep lint | follow-up `harness-data-not-code-grep-lint-*`（W3-2 前高优） |
| NICE TO HAVE (verify) | 真二进制 PDF/DOCX/PPT/XLSX fixture e2e | follow-up `adapter-raw-upload-binary-e2e-*` |
| NICE TO HAVE (verify) | firecrawl_url adapter 同步 port | follow-up `adapter-firecrawl-port-*` |

## 交付（merge 时回填）

- Branch：`change/adapter-raw-upload-20260520`
- Merge commit：_待 merge 后填_
- 关闭时间：_待填_
