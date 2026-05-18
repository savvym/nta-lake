---
change_id: pipeline-ui-tab-20260518
version: 2
authored_at: 2026-05-18T12:35:00Z
status: draft
prior_version: 1
prior_review: request_analysis/review/spec_review_v1.md
---

# Spec：Repo 详情页 Pipelines tab（粘贴 recipe → 一键触发 → 实时轮询节点状态）

> **v2 修订说明**：闭 spec_review_v1 的 5 MUST FIX。

## v1 review 闭环表

| # | v1 问题 | v2 状态 |
|---|---|---|
| MUST #1 | AC-1 grep `\|` 在 ERE 是字面竖线（不是 alternation）→ 假阴性；遗漏 PipelineRunCreatedResponse | **CLOSED**：拆 3 个独立 grep（`grep -q "interface PipelineNodeRunResponse"` + `grep -q "interface PipelineRunResponse"` + `grep -q "interface PipelineRunCreatedResponse"`） |
| MUST #2 | TS interface nullable 字段未明示 `\| null` | **CLOSED**：T-1 description 明示 5 个 nullable 字段（output_commit_hash / input_commits / cache_key / error 节点级 + PipelineRunResponse.error 都是 `string \| null` 或 `string[] \| null`） |
| MUST #3 | AC-4 缺 tsc --noEmit；仓库 build 真 = vite build && tsc | **CLOSED**：AC-4 验证扩展为 `cd apps/web && npm run build`（实跑等价 `vite build && tsc --noEmit -p tsconfig.json`） |
| MUST #4 | msw 未装；仓库测试统一 vi.mock 模块；T-5 同时测 hook + component 互斥 | **CLOSED**：拆为 T-5a（hook 测试用 `vi.spyOn(global, 'fetch')`）+ T-5b（组件测试用 `vi.mock("../lib/api/queries", ...)` 同既有 repos.test.tsx 模式）；2 个测试文件 |
| MUST #5 | process_tasks estimated_stage 命名违 SKILL 跨 AC #7 | **CLOSED**：改用 `stage-2 / stage-4 / stage-6 / stage-7 / stage-9 / stage-10` 短格式 |

## 背景

`pipeline-orchestrator-mvp-20260518` 落地了后端 pipeline 编排（POST /pipelines/runs:from-yaml + GET /pipelines/runs/{id}），但**前端没有 UI**——目前只能用 curl/SDK 触发。

用户最初诉求是"什么时候能用 web 操作一次全流程"（在本会话开头）；pipeline-orchestrator-mvp 的 stage 9 dogfood 完整证明后端跑通，本 change 把"web 一键跑 pipeline"这件事补上。

完成后用户可以：登录 admin → 在 demo/raw-md 等 repo 详情页底部 Pipelines tab → 粘贴 demo recipe → 一键运行 → 看实时节点状态 → 跳转到 silver/gold 看输出 commit。

## 问题陈述

Web 当前缺：
1. 触发 pipeline 的 UI（POST /pipelines/runs:from-yaml）
2. 查看 pipeline run 状态的 UI（GET /pipelines/runs/{id}），含节点级状态 / cache_hit / output_commit_hash
3. 实时刷新机制（pipeline 异步，状态需轮询）

后端 API 已就绪，只是没有前端绑定。

## 范围

In scope（**4 条 AC，含 2 条 behavioral**）：

- **AC-1**：`apps/web/src/lib/api/queries.ts` 新增 2 个 hook：
  - `useCreatePipelineRun()`：mutation，body=`{recipeYaml: string}`，POST /api/pipelines/runs:from-yaml（`Content-Type: text/yaml`），返 `{run_id, job_id}`
  - `usePipelineRun(runId: string \| null)`：query，GET /api/pipelines/runs/{runId}，`refetchInterval` 根据状态：queued/running → 1000ms，succeeded/failed → false（停止轮询），`enabled = !!runId`
  - TS 类型：`PipelineNodeRunResponse`, `PipelineRunResponse`, `PipelineRunCreatedResponse`（与后端 `apps/api/dataplat_api/schemas/pipeline.py` 对齐）
- **AC-2**：`apps/web/src/routes/repos/$owner.$name.tsx` 加 `PipelinesSection` 组件（admin only，模式同 IngestSection）：
  - yaml `<textarea>` + 按钮 "粘贴 demo recipe"（注入 `demo-bronze-to-gold.yaml` 字面 hardcoded）
  - "运行 Pipeline" 按钮：disabled 当 yaml 为空 / mutation pending；点击 → useCreatePipelineRun → 拿 run_id → setActiveRunId
  - Run 状态面板（activeRunId 非 null 时显示）：
    - run.status + run.error（如有）
    - 节点表：列 `node_id` / `processor_name@version` / `status` / `cache_hit` / `output_commit_hash`（截 12 字符）
    - 自动停止轮询当 status ∈ {succeeded, failed}
  - 不影响既有 FilesSection / IngestSection
- **AC-3**：vitest 单测 ≥ 4：
  - (a) `usePipelineRun` 状态机：mocked fetch 返 queued → running → succeeded，轮询计数 ≥ 2
  - (b) `useCreatePipelineRun` 成功路径：POST yaml → 返 {run_id, job_id}
  - (c) `PipelinesSection` 渲染（admin 用户 + 空 yaml → button disabled；填入 yaml + 点 button → mutation 触发）
  - (d) `PipelinesSection` Run 状态面板：mocked run response → 渲染节点表 ≥ 2 行（normalize + qa_gen）
- **AC-4**：**真跑** vitest + 本机起 web dev server 5174 + 浏览器无 console.error 自查（self-attest 等价 manual check）

## 非范围

- 不做 monaco/codemirror 等 yaml 编辑器（→ follow-up）
- 不做 SSE / WebSocket 实时推送（轮询足够 MVP）
- 不做 Pipeline 历史列表 / 跨 repo 查询页（→ follow-up `pipeline-list-page-*`）
- 不做 lineage 可视化（→ change #4）
- 不做 cancel / retry / delete pipeline（→ follow-up）
- 不动 `apps/web/src/routes/jobs.$job_id.tsx`（pipeline 触发的 job_id 不显示在 UI 上，仅写入 console for debug；用户看 run_id 即可）

## 验收标准

`kind` 二分：static / behavioral。

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | `queries.ts` 新增 2 个 hook + 3 个 TS interface（含 nullable 字段标注） | `test -f apps/web/src/lib/api/queries.ts && awk '/^export function useCreatePipelineRun/{p=1;next} p && /^export /{exit} p' apps/web/src/lib/api/queries.ts \| grep -q "pipelines/runs:from-yaml" && awk '/^export function usePipelineRun/{p=1;next} p && /^export /{exit} p' apps/web/src/lib/api/queries.ts \| grep -q "refetchInterval" && grep -q "interface PipelineNodeRunResponse" apps/web/src/lib/api/queries.ts && grep -q "interface PipelineRunResponse" apps/web/src/lib/api/queries.ts && grep -q "interface PipelineRunCreatedResponse" apps/web/src/lib/api/queries.ts` | 全 5 grep 命中（不用 `\|` ERE alternation 误把 `\|` 当字面） |
| AC-2 | static | `repos/$owner.$name.tsx` 含 PipelinesSection 组件 + admin 权限门 + textarea + 节点表 | `test -f apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q "function PipelinesSection" apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q "isAdmin && <PipelinesSection" apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q "useCreatePipelineRun" apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q "usePipelineRun" apps/web/src/routes/repos/\$owner.\$name.tsx` | 全 4 grep 命中（拆开避 `\|` 误读）|
| AC-3 | **behavioral** | vitest 跑 hook 测试 + 组件测试 ≥ 4 测试 PASS | `cd apps/web && npx vitest run src/lib/api/pipeline.test.tsx src/routes/repos.pipelines-section.test.tsx 2>&1 \| tail -5` | `Test Files  2 passed` + `Tests  ≥4 passed`；含 `usePipelineRun 状态机` / `useCreatePipelineRun 成功` / `PipelinesSection 渲染` / `节点表渲染` 4 项 |
| AC-4 | **behavioral** | 全仓 self_check 本 block 全 PASS；apps/web 真生产构建（`vite build && tsc --noEmit` 等价 `npm run build`） | `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh pipeline-ui-tab` 退码 0；`cd apps/web && npm run build 2>&1 \| tail -5` 含 `built in`、不含 `error TS` 或 `Found N errors` | 本 block 4/4 PASS；npm run build 成功（含 tsc --noEmit 真类型检查）|

**Behavioral AC：AC-3 + AC-4（vitest 真跑 + vite build 真跑）**，满足 ≥1 自约束。

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| `refetchInterval` 用 callback 形态（`(query) => query.state.data?.status ...`）TanStack v5 API 变化 | 中 | 中 | 实读 `node_modules/@tanstack/react-query` 版本 + 用稳定 callback 签名；vitest 测试用 mocked timers 验证停止轮询 |
| yaml POST 用 `text/yaml` Content-Type，fetchJson 默认 `application/json`，需自定义 fetch | 中 | 中 | 参照 `useUploadBlob` 自定义 fetch 模式（不走 fetchJson；`Content-Type: text/yaml` + raw body）|
| Pipeline 失败状态文案 / error 字符串过长截断（pipeline-orchestrator-mvp 已有 [:500] 截断）| 低 | 低 | UI 用 `<pre>` 显示 + max-h-32 overflow scroll |
| msw mock 与真实后端响应 schema 漂移 | 低 | 中 | 单测构造 mock 直接 import 后端 schema TS 等价；vite build 通过保证编译期类型对齐 |
| admin 权限校验只在前端隐藏 button（后端 require_admin 已强制） | 低 | 低 | 后端守门已足够；前端隐藏是 UX 优化，不当安全防线 |

## 受影响模块

- `apps/web/src/lib/api/queries.ts`（新增 hook + 类型）
- `apps/web/src/routes/repos/$owner.$name.tsx`（加 PipelinesSection 组件）
- `apps/web/src/routes/repos.pipelines-section.test.tsx`（**新建**，vitest）

## 不受影响

- `apps/web/src/routes/jobs.$job_id.tsx`（不动；pipeline 触发的 job_id 不展示给用户）
- `apps/web/src/routes/commits.$owner.$name.$hash.tsx`（不动）
- 后端 `apps/api/*`（**完全不动**，纯前端 change）

## 引用

- `apps/api/dataplat_api/schemas/pipeline.py` TS 类型对齐源
- `apps/api/dataplat_api/routers/pipelines.py` API 路由（POST /pipelines/runs:from-yaml + GET /pipelines/runs/{run_id}）
- `recipes/examples/demo-bronze-to-gold.yaml` demo 注入源
- `.harness/changes/pipeline-orchestrator-mvp-20260518/deployment/deploy_verify_v1.md` 后端 e2e 实证
- `.harness/skills/request-analysis/SKILL.md` § "AC 分层规约"（本 change 应用新规约 dogfood）
