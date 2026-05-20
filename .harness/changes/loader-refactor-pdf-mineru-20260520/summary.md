---
change_id: loader-refactor-pdf-mineru-20260520
title: PdfMineruLoader 实现 Loader Protocol + LoaderRegistry (W1-4)
owner: application-owner-agent
started_at: 2026-05-20T20:45:00Z
phase: design
status: approved
last_updated: 2026-05-20T20:45:00Z
related_changes:
  - operator-protocol-20260520 (W1-2, Loader Protocol 来源)
  - silver-schema-enforce-20260520 (W1-3, silver-text-v1 schema 来源)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。

## 一句话目标

把 `PdfMineruProcessor` 重构为 `PdfMineruLoader`（实现 Loader Protocol，输出 list[SilverRow]）+ 落 LoaderRegistry 骨架；老 Processor 保留不撤。

## 范围摘要

- **In scope**：LoaderRegistry (packages/core) + PdfMineruLoader (apps/api，复用 _mineru_client) + auto-register + pytest 3 个 behavioral 用例
- **Out of scope**：不撤老 PdfMineruProcessor；不改 worker / API recipe 调度；不实施 row schema 校验；不支持批量；不生成 content_list.json 附产物

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | _待填_ | [design.md](design.md) |
| Phase 2 Implementation | sonnet | pending | — | _待填_ | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | pending | — | _待填_ | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-20 20:45 | Loader 实现放 apps/api/loaders/ 不放 plugins/ | core 只定 Protocol；plugins/ 当前空且无 entrypoint；apps/api 是唯一能 import MinerUClient + blob_store 的地方 | design.md § 决策 3 |
| 2026-05-20 20:45 | 一 PDF blob → 一 SilverRow | 拆分是 Operator (chunker, W2-2) 职责；Loader 保持"一份原料一行"最简模型 | design.md § 决策 4 |
| 2026-05-20 20:45 | images 写 blob_store 后 row 只存 sha | CAS dedup；snapshot 序列化 size 受控 | design.md § 决策 5 |
| 2026-05-20 20:45 | 保留老 Processor 不撤 | recipe v2 (W2-5) 切换调度后另起 cleanup | design.md § 决策 1 |

## 交付（merge 时回填）

- Branch：`change/loader-refactor-pdf-mineru-20260520`
- Merge commit：_待填_
- 关闭时间：_待填_
