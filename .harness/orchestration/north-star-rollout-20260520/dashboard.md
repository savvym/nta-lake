---
rollout_id: north-star-rollout-20260520
last_updated: 2026-05-21T13:30:00Z
---

# Dashboard：北极星 rollout 进度

> application-owner 每完成一个 change 阶段就回写本表。Phase 列填 design / impl / verify / merged / blocked；Verdict 列填 APPROVED / SMALL / BIG / MINOR / MAJOR / —。

## Wave 状态总览

| Wave | 主题 | 数量 | 状态 | Checkpoint |
|---|---|---|---|---|
| 0 | 编排准备 | 3 docs | **done** | 3 文档落地 + 代码扫描完成 |
| 1 | 地基 | 4 | **done** (4/4) | end-to-end PDF demo 跑通新模型（W2-5 接 Loader 后真跑） |
| 2 | 核心算子链 | 6 | **done** (6/6) | 完整 recipe v2 跑通 + silver snapshot 持久化 |
| 3 | 源覆盖 + 训练对接 | 7 | **done** (7/7) | 4 种格式跑通 + HF 导出 ✅ |
| 4 | UI + 工程化 | 10 | **in_progress** (6/10; W4-7 next) | 用户完整 UI 流程跑通 |

## change 级状态

| ID | Wave | Phase | Verdict | Branch | PR / merge | Blocker |
|---|---|---|---|---|---|---|
| api-snapshot-rename-20260520 | W1-1 | **merged** | APPROVED | change/api-snapshot-rename-20260520 | a51a126 | — |
| operator-protocol-20260520 | W1-2 | **merged** | APPROVED | change/operator-protocol-20260520 | af8a7d5 | — |
| silver-schema-enforce-20260520 | W1-3 | **merged** | APPROVED | change/silver-schema-enforce-20260520 | 13abd0d | — |
| loader-refactor-pdf-mineru-20260520 | W1-4 | **merged** | APPROVED | change/loader-refactor-pdf-mineru-20260520 | 999ca82 | — |
| operator-suite-mvp-20260520 | W2-1 | **merged** | APPROVED | change/operator-suite-mvp-20260520 | 5d0ed99 | — |
| operator-chunker-20260520 | W2-2 | **merged** | APPROVED | change/operator-chunker-20260520 | 0f8f6ba | — |
| operator-image-to-text-suite-20260520 | W2-3 | **merged** | APPROVED | change/operator-image-to-text-suite-20260520 | c288082 | — |
| operator-snapshot-mixer-20260520 | W2-4 | **merged** | APPROVED | change/operator-snapshot-mixer-20260520 | 4dd1d3e | — |
| recipe-yaml-v2-20260520 | W2-5 | **merged** | APPROVED | change/recipe-yaml-v2-20260520 | 153c2c9 | — |
| dataset-export-engine-20260520 | W2-6 | **merged** | APPROVED | change/dataset-export-engine-20260520 | ac82567 | — |
| adapter-raw-upload-20260520 | W3-1 | **merged** | APPROVED | change/adapter-raw-upload-20260520 | 4d11055 | — |
| adapter-folder-md-assets-20260520 | W3-2 | **merged** | APPROVED | change/adapter-folder-md-assets-20260520 | f2ee022 | — |
| adapter-jsonl-import-20260520 | W3-3 | **merged** | APPROVED | change/adapter-jsonl-import-20260520 | 95d2e74 | — |
| loader-html-md-20260520 | W3-4 | **merged** | APPROVED | change/loader-html-md-20260520 | fb76736 | — |
| loader-docx-pptx-20260520 | W3-5 | **merged** | APPROVED | change/loader-docx-pptx-20260520 | 57185f5 | — |
| loader-jsonl-20260520 | W3-6 | **merged** | APPROVED | change/loader-jsonl-20260520 | 0878c35 | — |
| gold-loader-hf-datasets-20260520 | W3-7 | **merged** | APPROVED | change/gold-loader-hf-datasets-20260520 | 09aa977 | — |
| web-pdf-mineru-ui-v2-20260520 | W4-1 | **merged** | APPROVED | change/web-pdf-mineru-ui-v2-20260520 | e3dc25f | — |
| web-row-preview-20260520 | W4-2 | **merged** | APPROVED | change/web-row-preview-20260520 | 4dea85a | — |
| web-operator-chain-builder-20260520 | W4-3 | **merged** | APPROVED | change/web-operator-chain-builder-20260520 | 9a92134 | — |
| web-snapshot-export-ui-20260520 | W4-4 | **merged** | APPROVED | change/web-snapshot-export-ui-20260520 | 95f55e7 | — |
| cost-budget-system-20260520 | W4-5 | **merged** | APPROVED | change/cost-budget-system-20260520 | 9c73af6 | — |
| integration-test-framework-20260520 | W4-6 | **merged** | APPROVED | change/integration-test-framework-20260520 | f8068fa | — |
| observability-mvp-20260520 | W4-7 | pending | — | — | — | depends W2-5 |
| operator-eval-gen-20260520 | W4-8 | pending | — | — | — | depends W2-5 |
| operator-dpo-pair-gen-20260520 | W4-9 | pending | — | — | — | depends W4-8 |
| backup-restore-20260520 | W4-10 | pending | — | — | — | depends W3 done |

## 当前活动

- **active change**: 无（W4-6 merged f8068fa；准备启动 W4-7）
- **next action**: 启动 W4-7 `observability-mvp-*`（metrics / structured logs / health probe 扩展；前置：W2-5 / W4-5 已落）→ application-owner 自写 mini-design → sonnet 端到端 → opus verify
- **Wave 1 + Wave 2 + Wave 3 Checkpoint 状态**：全部 done（17/17）；W4-1..W4-6 已 merged（snapshot row endpoint + PDF→silver row UI v2 / 通用 row 预览 + react-virtual / Recipe v2 chain builder UI / HF datasets export endpoint + UI / LLM cost budget + 402 + per-scope ledger + admin router / **integration test framework — bash orchestrator (up / run / down / all) + env-gated smoke test**）。
- **UI 测试边界**：W4-1/W4-2/W4-3/W4-4 仅组件级 RTL+vi.mock，UI 真跑由 user final acceptance + W4-6 integration_test.sh 真跑（env 就位时 ~129 SKIP 转 PASS）联合验。W4-6 已落 backend orchestrator；playwright UI e2e 延 `integration-playwright-e2e-*` follow-up。

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

- Changes done: **23 / 27**（W1-1 a51a126, W1-2 af8a7d5, W1-3 13abd0d, W1-4 999ca82, W2-1 5d0ed99, W2-2 0f8f6ba, W2-3 c288082, W2-4 4dd1d3e, W2-5 153c2c9, W2-6 ac82567, W3-1 4d11055, W3-2 f2ee022, W3-3 95d2e74, W3-4 fb76736, W3-5 57185f5, W3-6 0878c35, W3-7 09aa977, W4-1 e3dc25f, W4-2 4dea85a, W4-3 9a92134, W4-4 95f55e7, W4-5 9c73af6, W4-6 f8068fa）
- Wave 1 全部 done（4/4）；Wave 2 全部 done（6/6）；Wave 3 全部 done（7/7 ✅）；Wave 4 进度 6/10
- Phase 1 reviewer cycles: 1（W1-1；W1-2 起 v3 不再跑）
- Phase 3 reviewer cycles: 23（W1-1..W4-6 全部 APPROVED）
- v3 mini-design 实测：design 56-160 行 / 3-4 AC；application-owner + sonnet + opus 各 1 次 spawn，verify ~2-9 min（W4-6 纯 bash + 1 smoke test < 3 min）
- 0-issue APPROVED 连续 20 次（W1-4 / W2-1..W2-6 / W3-1..W3-7 / W4-1 / W4-2 / W4-3 / W4-4 / W4-5 / W4-6）；W4-6 含 2 DEVIATION ACCEPT（DEV-1 smoke test 用 `/healthz`（main.py 实际路由）而非 design 笔误 `/health` / DEV-2 usage 改 heredoc 函数避免 `grep '^#'` 打印全部注释行）+ 0 NICE TO HAVE 阻塞（helpers.sh 双空格 + cmd_run tail 截断仅记 follow-up）
- packages/core 测试：97/97 PASS（W4-6 不动 core）
- apps/web 测试：60/60 PASS（W4-6 不动 web）
- apps/api 测试：51 passed + 129 skipped（W4-6 +1 env-gated SKIP：test_integration_smoke，与 W4-1 同模式；零回归）
- Wave 3 新增第三方依赖：python-docx>=1.1,<2 / python-pptx>=0.6,<2（W3-5）；datasets>=2.14,<4（W3-7，~100MB transitive）；Wave 4 W4-2 引入 @tanstack/react-virtual@^3；Wave 4 W4-3 引入 @dnd-kit/core@^6 + @dnd-kit/sortable@^8 + @dnd-kit/utilities@^3 + js-yaml@^4 + @types/js-yaml@^4 devDep；**W4-4 / W4-5 / W4-6 零新依赖**（W4-4 `tarfile`/`io` stdlib；W4-5 asyncio + pydantic 既有；W4-6 bash + 既有 httpx）
- Wave 4 UI 测试边界：W4-1/W4-2/W4-3/W4-4 仅组件级 RTL+vi.mock；UI 真跑由 user final acceptance + W4-6 integration_test.sh 真跑（playwright UI e2e 延 follow-up）联合验
- BIG REWRITE 次数: 0
- MAJOR ISSUE 次数: 0
- 用户介入次数（非验收）: 2（efficiency pivot → v3；self_check 取消）

## Follow-up backlog

- `api-snapshot-rename-cleanup-*`：W2 末删 308 redirect 端点
- `harness-v3-process-docs-*`：写 development-process.md v3 / application-owner.md v3 / harness_new_change.sh 模板精简 / 移除 design_review.md 默认生成（D-13 落地为 harness meta change）
- `harness-registry-count-assert-style-*`：W2-4 暴露：dataplat Registry 测试用 `len == N` 总数断言会被每个新 change 加 Operator 触发 regression；统一改 `name in names` 或 `>= N`（W2-4 verify_review NICE TO HAVE）
- `operator-chunker-smart-*`：W2-2 关联：句子/token 边界 + overlap window 的高级 chunker
- `operator-image-caption-llm-*`、`operator-image-ocr-*`、`operator-image-vqa-*`：W2-3 关联，依赖 LLM Gateway 形式化

## 异常 / 阻塞日志

（空）
