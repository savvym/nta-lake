---
change_id: recipe-yaml-v2-20260520
title: Recipe YAML v2 解析器 + 执行器 (W2-5)
owner: application-owner-agent
started_at: 2026-05-21T00:50:00Z
phase: design
status: approved
last_updated: 2026-05-21T00:50:00Z
related_changes:
  - operator-protocol-20260520 (W1-2, Operator Protocol)
  - loader-refactor-pdf-mineru-20260520 (W1-4, Loader Protocol)
  - operator-suite-mvp-20260520 (W2-1)
  - operator-chunker-20260520 (W2-2)
  - operator-image-to-text-suite-20260520 (W2-3)
  - operator-snapshot-mixer-20260520 (W2-4)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。本 change 范围比 W2-1..W2-4 大（新 schema + parser + executor）。

## 一句话目标

落 packages/core/recipe.py：v2 schema (loader + operators) + load_recipe_v2 解析器 + run_recipe_v2 in-process 执行器，把 Loader 与 Operator 端到端链起来。

## 范围摘要

- **In scope**：packages/core/recipe.py 新增 RecipeV2/load_recipe_v2/run_recipe_v2 + pytest 4 个 behavioral 用例
- **Out of scope**：不动 apps/api v1 Recipe；不接 worker；不写 silver snapshot 持久化（W2-6）；不支持 input repo-ref；不强校验 operator config 内容

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | _待填_ | [design.md](design.md) |
| Phase 2 Implementation | sonnet | pending | — | _待填_ | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | pending | — | _待填_ | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 00:50 | core-only 范围，API 接入留 follow-up | v1 Recipe 与 v2 engine 解耦；本 change 不动 apps/api | design.md § 决策 1 |
| 2026-05-21 00:50 | v2 yaml 顶层必含 version: 2 | 显式 versioning；parser 通过版本字段路由 | design.md § 决策 2 |
| 2026-05-21 00:50 | executor 同步 + in-process | 与 PdfMineruLoader 内部 asyncio.run 模式对齐 | design.md § 决策 3 |
| 2026-05-21 00:50 | operators 是线性链非 DAG | v2 设计前提；并行/分支留单独 change | design.md § 决策 4 |
| 2026-05-21 00:50 | input 仅支持 blob_sha 直传 | repo-ref resolve 跨模块；留 W3 / api change | design.md § 决策 5 |
| 2026-05-21 00:50 | RecipeRunResult 不写 CAS | 引擎职责单一；持久化是 W2-6 | design.md § 决策 6 |

## 交付（merge 时回填）

- Branch：`change/recipe-yaml-v2-20260520`
- Merge commit：_待填_
- 关闭时间：_待填_
