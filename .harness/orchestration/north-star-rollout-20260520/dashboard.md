---
rollout_id: north-star-rollout-20260520
last_updated: 2026-05-20T22:00:00Z
---

# Dashboard：北极星 rollout 进度

> application-owner 每完成一个 change 阶段就回写本表。Phase 列填 design / impl / verify / merged / blocked；Verdict 列填 APPROVED / SMALL / BIG / MINOR / MAJOR / —。

## Wave 状态总览

| Wave | 主题 | 数量 | 状态 | Checkpoint |
|---|---|---|---|---|
| 0 | 编排准备 | 3 docs | **done** | 3 文档落地 + 代码扫描完成 |
| 1 | 地基 | 4 | **done** (4/4) | end-to-end PDF demo 跑通新模型（W2-5 接 Loader 后真跑） |
| 2 | 核心算子链 | 6 | **in_progress** (1/6; W2-2 next) | 完整 recipe v2 跑通 |
| 3 | 源覆盖 + 训练对接 | 7 | pending | 4 种格式跑通 + HF 导出 |
| 4 | UI + 工程化 | 10 | pending | 用户完整 UI 流程跑通 |

## change 级状态

| ID | Wave | Phase | Verdict | Branch | PR / merge | Blocker |
|---|---|---|---|---|---|---|
| api-snapshot-rename-20260520 | W1-1 | **merged** | APPROVED | change/api-snapshot-rename-20260520 | a51a126 | — |
| operator-protocol-20260520 | W1-2 | **merged** | APPROVED | change/operator-protocol-20260520 | af8a7d5 | — |
| silver-schema-enforce-20260520 | W1-3 | **merged** | APPROVED | change/silver-schema-enforce-20260520 | 13abd0d | — |
| loader-refactor-pdf-mineru-20260520 | W1-4 | **merged** | APPROVED | change/loader-refactor-pdf-mineru-20260520 | 999ca82 | — |
| operator-suite-mvp-20260520 | W2-1 | **merged** | APPROVED | change/operator-suite-mvp-20260520 | 5d0ed99 | — |
| operator-chunker-20260520 | W2-2 | **design** | — | — | — | — |
| operator-image-to-text-suite-20260520 | W2-3 | pending | — | — | — | depends W2-1 |
| operator-snapshot-mixer-20260520 | W2-4 | pending | — | — | — | depends W2-1 |
| recipe-yaml-v2-20260520 | W2-5 | pending | — | — | — | depends W2-1..4 |
| dataset-export-engine-20260520 | W2-6 | pending | — | — | — | depends W2-5 |
| adapter-raw-upload-20260520 | W3-1 | pending | — | — | — | depends W2-5 |
| adapter-folder-md-assets-20260520 | W3-2 | pending | — | — | — | depends W2-5 |
| adapter-jsonl-import-20260520 | W3-3 | pending | — | — | — | depends W2-5 |
| loader-html-md-20260520 | W3-4 | pending | — | — | — | depends W2-5 |
| loader-docx-pptx-20260520 | W3-5 | pending | — | — | — | depends W2-5 |
| loader-jsonl-20260520 | W3-6 | pending | — | — | — | depends W3-3 |
| gold-loader-hf-datasets-20260520 | W3-7 | pending | — | — | — | depends W2-6 |
| web-pdf-mineru-ui-v2-20260520 | W4-1 | pending | — | — | — | depends W3 done |
| web-row-preview-20260520 | W4-2 | pending | — | — | — | depends W4-1 |
| web-operator-chain-builder-20260520 | W4-3 | pending | — | — | — | depends W4-2 |
| web-snapshot-export-ui-20260520 | W4-4 | pending | — | — | — | depends W4-3 |
| cost-budget-system-20260520 | W4-5 | pending | — | — | — | depends W2-3 |
| integration-test-framework-20260520 | W4-6 | pending | — | — | — | depends W3 done |
| observability-mvp-20260520 | W4-7 | pending | — | — | — | depends W2-5 |
| operator-eval-gen-20260520 | W4-8 | pending | — | — | — | depends W2-5 |
| operator-dpo-pair-gen-20260520 | W4-9 | pending | — | — | — | depends W4-8 |
| backup-restore-20260520 | W4-10 | pending | — | — | — | depends W3 done |

## 当前活动

- **active change**: `operator-chunker-20260520` (W2-2)
- **next action**: application-owner 自写 mini-design（ChunkerOperator 演示 1→N，按 max_chars 切 row.text 成多个新 row）→ sonnet 端到端 → opus verify
- **Wave 1 Checkpoint 状态**：4/4 changes done。end-to-end PDF demo 待 W2-5 recipe v2 真接 Loader 后跑通。

## 代码扫描快照（2026-05-20 Wave 0）

> W1-1 涉及的 commit→snapshot 改名工作量量化：

- **API routers**: `apps/api/dataplat_api/routers/commits.py` (8 endpoints, prefix `/repos`, tag `commits`)，另在 `routers/ingest.py` / `pipelines.py` / `main.py` 有零散引用
- **API models**: `models/commit.py`（核心 ORM）+ `models/refs.py`（branch/tag refs，要确认 branch 这个 v1 概念是否也要清理）+ `models/pipeline.py` / `models/base.py` 引用
- **api-types**: `packages/api-types/src/generated.ts` — **27 处** `commit` / `Commit`（生成代码，需追溯生成器）
- **sdk-py**: `packages/sdk-py/src/dataplat_sdk/client.py` (5 处) + `cli.py` 命令名
- **web routes**: flat-dot `commits.$owner.$name.$hash.tsx` + 测试；`blob.$owner.$name.$hash.tsx` 也是 commit-hash 风格 URL
- **web hooks**: `apps/web/src/lib/api/queries.ts` (containing commit-related queries) + 多处 .test.tsx
- **plugins/ 目录实际为空**（只有 README.md）；老 processors 在 `apps/api/dataplat_api/processors/` 5 个：pdf_mineru / llm_qa_gen / llm_summarize / markdown_normalize / _mineru_client
- **老 adapters** 在 `apps/api/dataplat_api/adapters/`：firecrawl_url / raw_upload / _image_extract
- **self_check**: dispatcher 结构稳定（`run_<change>` + case 路由 + full 链）；W1-1 加 `run_api_snapshot_rename` 块
- **alembic**: `apps/api/alembic/versions/` 含历史迁移；DB schema 内部仍可保留 `commit`，对外重命名只动 API 层（D-1 已决策"DB schema 不动"，需 W1-1 design 明确）

## 累计 metrics

- Changes done: **5 / 27**（W1-1 a51a126, W1-2 af8a7d5, W1-3 13abd0d, W1-4 999ca82, W2-1 5d0ed99）
- Wave 1 全部 done（4/4）；Wave 2 进度 1/6
- Phase 1 reviewer cycles: 1（W1-1；W1-2 起 v3 不再跑）
- Phase 3 reviewer cycles: 5（W1-1, W1-2, W1-3, W1-4, W2-1）
- v3 mini-design 实测：W1-2..W2-1 design 56-107 行 / 3-4 AC；application-owner + sonnet + opus 各 1 次 spawn，verify ~2-7 min
- W1-4 / W2-1 都是 0-issue APPROVED（设计 + 实现一次过的稳定区）
- BIG REWRITE 次数: 0
- MAJOR ISSUE 次数: 0
- 用户介入次数（非验收）: 2（efficiency pivot → v3；self_check 取消）

## Follow-up backlog

- `api-snapshot-rename-cleanup-*`：W2 末删 308 redirect 端点
- `harness-v3-process-docs-*`：写 development-process.md v3 / application-owner.md v3 / harness_new_change.sh 模板精简 / 移除 design_review.md 默认生成（D-13 落地为 harness meta change）

## 异常 / 阻塞日志

（空）
