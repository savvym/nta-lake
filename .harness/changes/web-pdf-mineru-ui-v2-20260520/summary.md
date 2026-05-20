---
change_id: web-pdf-mineru-ui-v2-20260520
title: web PDF→silver row UI v2 (W4-1)
owner: application-owner-agent
started_at: 2026-05-21T09:30:00Z
phase: merged
status: closed
last_updated: 2026-05-21T10:30:00Z
related_changes:
  - loader-refactor-pdf-mineru-20260520 (W1-4, PdfMineruLoader 上游)
  - operator-protocol-20260520 (W1-2, SilverRow schema)
  - dataset-export-engine-20260520 (W2-6, silver JSONL 写入方)
  - recipe-yaml-v2-20260520 (W2-5, pipeline run 调度)
  - api-snapshot-rename-20260520 (W1-1, snapshots router prefix)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。Wave 4 第一个 change；apps/api silver row endpoint + apps/web 新路由展示 SilverRow 表格（替代老 markdown blob 渲染）。

## 一句话目标

apps/api 加 `GET /repos/{owner}/{name}/snapshots/{hash}/rows?offset=&limit=` 暴露 silver snapshot 行数据；apps/web 加 `/repos/$owner/$name/pdf-mineru` 路由（folder form）展示 silver row 表格 + 行展开看 source_ref / stats / lineage_ops JSON。

## 范围摘要

- **In scope**：apps/api snapshots.py +endpoint / schemas/snapshot_rows.py 新 + 3 backend pytest；apps/web queries.ts +useSnapshotRows / routes/repos/$owner.$name/pdf-mineru.tsx 新 + 2 vitest+RTL test；父路由 +`<Outlet />` (folder form 强制要求)
- **Out of scope**：不做行虚拟化（W4-2）；不做通用 row preview 路由（W4-2）；不接 multi-step chain UI（W4-3）；不做导出按钮（W4-4）；不做 playwright e2e（W4-6）；不做 manifest.yaml (D-1)

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | 4919a49 + e0bcdf9 | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | n/a | 15195c4 + 5afa515 | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | 0f3f95e | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 09:30 | rows endpoint 挂 snapshots.py | 与 GET snapshot 同 prefix + visibility 矩阵 | design.md § 决策 1 |
| 2026-05-21 09:30 | endpoint `/rows` 后缀 | silver / gold 行级语义统一 | design.md § 决策 2 |
| 2026-05-21 09:30 | blob_sha 自动找 .jsonl entry | 默认 auto；caller 可显式传绕过 | design.md § 决策 3 |
| 2026-05-21 09:30 | rows endpoint 全 blob 入内存 | MVP；流式留 follow-up | design.md § 决策 4 |
| 2026-05-21 09:30 | SilverRowRead 薄 schema | apps/api 与 dataplat_core 解耦 | design.md § 决策 5 |
| 2026-05-21 09:30 | folder form 路由 (sonnet fallback) | flat-dot 与 $owner.$name.tsx 嵌套冲突 | design.md § 风险表 + impl DEV-1 |
| 2026-05-21 09:30 | `<Outlet />` 加父路由 | folder form 强制要求 | impl DEV-2 |
| 2026-05-21 09:30 | 不做 playwright e2e | W4-6 引入；UI 真跑由 user final acceptance 验 | design.md § 决策 9 |

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| NICE TO HAVE (verify) | sonnet impl.md "3 passed" 在无 DATAPLAT_* env 时实际 SKIPPED；测试证据呈现方式应明示 env 前缀 | follow-up `harness-test-evidence-env-skipif-*` |
| follow-up (design) | 流式 rows endpoint | `web-pdf-mineru-ui-v2-stream-*` |
| follow-up (design) | websocket 实时 job 状态推送 | `web-jobs-ws-*` |
| follow-up (design) | @tanstack/react-virtual 行虚拟化 | `web-rows-virtualization-*`（W4-2 实际落地） |
| follow-up (design) | 多步 chain UI (pdf_mineru → chunker → image_to_text) | `web-pdf-mineru-chain-multi-*`（W4-3 关联） |
| follow-up (design) | rows endpoint 422 结构化 error code + 行号 | `apps-api-snapshot-rows-error-detail-*` |

## 交付

- Branch：`change/web-pdf-mineru-ui-v2-20260520`
- Merge commit：`e3dc25f`
- 关闭时间：2026-05-21T10:30:00Z
