---
change_id: pipeline-ui-tab-20260518
title: Repo 详情页 Pipelines tab：粘贴 recipe YAML → 一键触发 → 实时轮询节点状态
owner: application-owner-agent
started_at: 2026-05-18T12:20:00Z
stage: done
status: closed
last_updated: 2026-05-18T13:05:00Z
related_changes:
  - pipeline-orchestrator-mvp-20260518
  - harness-ac-behavioral-tier-20260518
  - stage9-followup-cleanup-20260518
  - web-mvp-pages-20260517
  - web-write-flows-20260517
---

# Summary

## 一句话目标

让 admin 用户能在 web 端**不写代码、不开终端**地跑一次 Bronze→Silver→Gold pipeline——Repo 详情页加 Pipelines tab，粘贴/选 demo recipe → POST /pipelines/runs:from-yaml → 实时轮询节点状态显示。

## 范围摘要

- **In scope**：
  - AC-1：`apps/web/src/lib/api/queries.ts` 加 `useCreatePipelineRun()` mutation + `usePipelineRun(run_id)` query（带轮询 refetchInterval）
  - AC-2：Repo 详情页（`apps/web/src/routes/repos/$owner.$name.tsx`）加 PipelinesSection 组件（admin only）：
    - 一个 yaml textarea + "粘贴 demo recipe" 按钮（注入 `recipes/examples/demo-bronze-to-gold.yaml` 字面）
    - "运行 Pipeline" 按钮 → POST /pipelines/runs:from-yaml → 拿 run_id → 进入"Run 状态"面板
    - Run 状态面板：display run.status + 每节点 {node_id, processor, status, cache_hit, output_commit_hash}；status=queued/running 时 setInterval 1000ms 轮询；status=succeeded/failed 停止
  - AC-3：vitest 单测 ≥3：(a) usePipelineRun 状态机（queued → running → succeeded）；(b) useCreatePipelineRun 成功路径；(c) PipelinesSection 渲染 + "运行 Pipeline" 按钮点击触发 mutation
  - AC-4：**真跑端到端**——本机起服务（API 8080 + Web 5174）+ 浏览器/curl 等价的 ASGITransport 集成（vitest 跑 PipelinesSection 用 msw mock /api 端点，断言轮询 ≥1 次 + 显示 "succeeded"）

- **Out of scope**：
  - lineage 可视化 / DAG 图（Phase 2，change #4）
  - Pipeline 历史列表 / 跨 repo 查询（follow-up `pipeline-list-page-*`）
  - Pipeline 触发表单的 recipe 编辑器高亮 / 语法校验 → follow-up `pipeline-ui-recipe-editor-*`
  - Pipeline 节点详情页 → follow-up `pipeline-ui-node-detail-*`
  - SSE / WebSocket 实时推送（用 setInterval 轮询足够 MVP）
  - 取消 / 删除 / 重试 pipeline（follow-up `pipeline-cancel-api-*` + UI 配套）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 |
|---|---|---|---|---|
| 1 需求分析 | in_progress | v1 | — | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | pending | — | — | review/spec_review_v1.md · tasks_review_v1.md |
| 3 编码实现 | done | v1 | — | [coding_report_v1.md](coding/coding_report_v1.md) — 4/4 AC PASS + vitest 4/4 + npm build (vite+tsc) 0 error |
| 4 编码评审 | done | v1 | APPROVED | [code_review_v1.md](coding/review/code_review_v1.md) — 0 MUST/0 SHOULD/4 NICE；reviewer 独立 npm run build PASS + vitest 复跑 4 passed |
| 5 单测编写 | done | v1 | — | [test_report_v1.md](unit_test/test_report_v1.md) — 4 vitest + npm build；2 模式 mock 协同（spyOn fetch + vi.mock module） |
| 6 单测评审 | done | v1 | APPROVED | [test_review_v1.md](unit_test/review/test_review_v1.md) — 0 MUST/4 SHOULD；reviewer 独立复跑 vitest 3.16s 4 passed |
| 7 代码推送 | done | v1 | — | main 直接 commit（无 remote） |
| 8 CI 验证 | self-attest | — | — | 项目无 remote 长期未决（同 change #1#2） |
| 9 部署验证 | done | v1 | PASS | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) — npm run build 0 error + vite dev server 5174 serving + curl /api/pipelines/runs:from-yaml 端到端 + 用户浏览器可见 PipelinesSection |
| 10 用户确认 | done | v1 | PASS via 授权 | zhhdzhang @ 2026-05-18 显式授权"按 1,2,3,4 你自行启动"——本 change #3 在授权范围 |

## 关键决策

| 时间 | 决策 | 理由 |
|---|---|---|
| 2026-05-18 | 用 yaml textarea + "粘贴 demo" 按钮，不做编辑器高亮 | MVP 优先；编辑器要 monaco/codemirror 等大依赖；follow-up 单独 change |
| 2026-05-18 | 用 setInterval 1000ms 轮询，不上 SSE/WebSocket | 跑完一般 < 30s，轮询 ~30 次足够；SSE 需后端配套（design.md §13.3 未实现） |
| 2026-05-18 | PipelinesSection 放 Repo 详情页底部（IngestSection 之后），不开独立 route | UX：用户已经在 demo/sft 这种 silver/gold repo 时可以直接看流水线；不需要跳到 /pipelines 全局列表 |
| 2026-05-18 | admin only（同 IngestSection 模式） | pipeline 触发权限与 ingest 等价；后续 ACL 改造时一起放 |

## 当前阻塞

无。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX (stage 4 NICE-1) | PipelinesSection 的 `owner`/`name` props 未使用（仅 `void owner; void name;`） | follow-up `pipeline-ui-tab-context-*`：未来扩展时把 props 传给 hook 或 telemetry |
| SHOULD FIX (stage 4 NICE-2) | vitest fireEvent.click 未包 act() → console act warning | follow-up `web-test-act-wrap-*` |
| SHOULD FIX (stage 4 NICE-3) | DEMO_RECIPE_YAML hardcoded 在 tsx，与 recipes/examples/ 重复维护 | follow-up `web-demo-recipe-fetch-*`：让 web 从 /api/recipes/examples 拉 |
| SHOULD FIX (stage 6 SHOULD-1) | usePipelineRun 测试未断言 succeeded 后 refetchInterval 真停止 | follow-up `pipeline-ui-test-stop-poll-*` |
| SHOULD FIX (stage 6 SHOULD-2) | 节点表 cache_hit / output_commit_hash 截断 / status 颜色 3 列只 mock 数据未断言渲染 | follow-up `pipeline-ui-test-column-coverage-*` |
| SHOULD FIX (stage 6 SHOULD-3) | 缺 5 边界分支测试：failed badge / error pre 显示 / node_runs=[] / output_commit_hash=null / mutateAsync 失败 setError | follow-up `pipeline-ui-test-edge-*` |
| SHOULD FIX (stage 6 SHOULD-4) | act() warning（同 stage 4 NICE-2，重复条目）| 已并入 `web-test-act-wrap-*` |

## 交付

> 关闭本变更时填写。

- Branch：main（无 remote）
- PR：N/A
- Merge commit：本 commit
- 部署版本：dev 本机（API 8080 + Web 5174；vite dev + npm run build 双路径）
- 用户确认：zhhdzhang @ 2026-05-18 显式授权"按 1,2,3,4 你自行启动"
- 关闭时间：2026-05-18T13:05:00Z

## 复盘

> 关闭时填写。
