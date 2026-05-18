---
change_id: pipeline-ui-tab-20260518
version: 2
authored_at: 2026-05-18T12:35:00Z
prior_version: 1
prior_review: request_analysis/review/tasks_review_v1.md
---

# Tasks

> **v2 修订说明**：闭 spec_review_v1 联动的 tasks 改动（T-1 nullable 明示 / T-5 拆 a/b / process_tasks stage 命名）。

## 任务清单

```yaml
tasks:
  - id: T-1
    title: queries.ts 新增 TS 类型（PipelineRunResponse / PipelineNodeRunResponse / PipelineRunCreatedResponse）
    description: |
      apps/api/dataplat_api/schemas/pipeline.py 的 Pydantic 模型对齐 TS interface
      **必须显式标 nullable 字段（| null）**：
        PipelineNodeRunResponse:
          node_id: string
          processor_name: string
          processor_version: string
          config: Record<string, unknown>
          status: string
          cache_hit: boolean
          output_commit_hash: string | null    # backend: str | None
          input_commits: string[] | null       # backend: list[str] | None
          cache_key: string | null             # backend: str | None
          error: string | null                 # backend: str | None
        PipelineRunResponse:
          run_id: string
          recipe_name: string
          status: string
          error: string | null                 # backend: str | None
          created_by: string
          node_runs: PipelineNodeRunResponse[]
        PipelineRunCreatedResponse:
          run_id: string
          job_id: string
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending
    commits: []

  - id: T-2
    title: queries.ts 加 useCreatePipelineRun() mutation
    description: |
      自定义 fetch（不走 fetchJson，Content-Type 不同）：
        POST /api/pipelines/runs:from-yaml + Content-Type: text/yaml + raw body=yaml
        返 PipelineRunCreatedResponse
      参考 useUploadBlob 自定义 fetch 模式。
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending
    commits: []

  - id: T-3
    title: queries.ts 加 usePipelineRun(runId) query 含动态轮询
    description: |
      useQuery({
        queryKey: ['pipeline-run', runId],
        queryFn: () => fetchJson<PipelineRunResponse>(`/api/pipelines/runs/${runId}`),
        enabled: !!runId,
        refetchInterval: (query) => {
          const status = query.state.data?.status;
          if (status === 'succeeded' || status === 'failed') return false;
          return 1000;
        },
      })
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending
    commits: []

  - id: T-4
    title: repos/$owner.$name.tsx 加 PipelinesSection 组件
    description: |
      在 RepoDetailPage return JSX 末尾（IngestSection 之后）：
        {isAdmin && <PipelinesSection owner={owner} name={name} />}
      新建 PipelinesSection 函数组件：
        - useState: yamlText (string) + activeRunId (string | null)
        - useCreatePipelineRun mutation
        - usePipelineRun query (enabled when activeRunId)
        - 按钮 "粘贴 demo recipe"：setYamlText(DEMO_RECIPE_YAML) - hardcoded inline
          demo-bronze-to-gold.yaml 的字面（10-15 行）
        - 按钮 "运行 Pipeline"：disabled if !yamlText.trim() || mutation.isPending
          点击 → mutation.mutateAsync(yamlText) → setActiveRunId(res.run_id)
        - Run 状态面板 (activeRunId 非 null)：
          run.status badge + run.error <pre>（如有）
          节点表：<table> 含 node_id / processor / status / cache_hit / output_commit_hash 5 列
        - 自动停止轮询当 status ∈ {succeeded, failed}（refetchInterval 内置）
      用 shadcn UI Button / Textarea / Card 组件（已有）。
    depends_on: [T-2, T-3]
    estimated_stage: coding
    covers_ac: [AC-2]
    status: pending
    commits: []

  - id: T-5a
    title: 新建 vitest hook 测试 src/lib/api/pipeline.test.tsx
    description: |
      apps/web/src/lib/api/pipeline.test.tsx，含 2 测试，**用 `vi.spyOn(global, 'fetch')` 模式
      （而非 msw，因为仓库未装 msw）**：
        (a) usePipelineRun 状态机：spy fetch 序列 queued/running/succeeded，
            用 vi.useFakeTimers() + vi.advanceTimersByTimeAsync(1100) 推 2 次轮询，
            断言 spy.mock.calls.length ≥ 2，最终 query.data.status === 'succeeded'
        (b) useCreatePipelineRun：spy fetch POST 返 {run_id, job_id}，断言
            mutation.mutateAsync(yamlText) 返回的对象有 run_id 字段
      用 renderHook + QueryClientProvider wrapper（参考 useJob/useUploadBlob 现有测试模式
      或新建 wrapper）。
    depends_on: [T-3]
    estimated_stage: unit_test
    covers_ac: [AC-3]
    status: pending
    commits: []

  - id: T-5b
    title: 新建 vitest 组件测试 src/routes/repos.pipelines-section.test.tsx
    description: |
      apps/web/src/routes/repos.pipelines-section.test.tsx，含 2 测试，**用
      `vi.mock("../lib/api/queries", ...)` 模式（同既有 repos.test.tsx）**：
        (c) PipelinesSection 渲染：renderWithProviders(<PipelinesSection ... />)
            + mock useCreatePipelineRun / usePipelineRun
            + 默认 yaml 为空 → 按钮 disabled
            + fireEvent.change(textarea, value='name: x\nnodes: []') → 按钮 enabled
            + fireEvent.click(button) → mockMutation.mutateAsync 被调
        (d) PipelinesSection Run 状态面板：mock usePipelineRun 返 status=succeeded
            + 2 节点（normalize / qa_gen）→ screen.getByText('normalize') +
            screen.getByText('qa_gen') 都命中
      参考既有 apps/web/src/routes/repos.test.tsx 的 vi.mock 模块模式。
    depends_on: [T-4]
    estimated_stage: unit_test
    covers_ac: [AC-3]
    status: pending
    commits: []

  - id: T-6
    title: 跑通 vitest + npm run build（含 tsc --noEmit）
    description: |
      cd apps/web
      npx vitest run src/lib/api/pipeline.test.tsx src/routes/repos.pipelines-section.test.tsx
      期望: Test Files 2 passed; Tests ≥4 passed
      npm run build  # = vite build && tsc --noEmit -p tsconfig.json
      期望: 含 "built in"; 不含 "error TS" 或 "Found N errors"
    depends_on: [T-5a, T-5b]
    estimated_stage: unit_test
    covers_ac: [AC-3, AC-4]
    status: pending
    commits: []

  - id: T-7
    title: scripts/_self_check.sh 加 run_pipeline_ui_tab block
    description: |
      在 main 调用链插入 run_pipeline_ui_tab（stage9-followup-cleanup 之后、
      harness-ac-behavioral-tier 之前）。
      4 个 AC：
        - AC-1 static：5 个独立 grep（2 hook 函数 awk 状态机锚定 + 3 interface 各自）
        - AC-2 static：4 个独立 grep（PipelinesSection / isAdmin gate / useCreatePipelineRun /
                       usePipelineRun，**不用 \| ERE alternation**）
        - AC-3 behavioral：cd apps/web && npx vitest run 2 测试文件
        - AC-4 behavioral：cd apps/web && npm run build（含 tsc --noEmit），
                          检查 stdout 含 "built in" + 不含 "error TS" 或 "Found ... errors"
      加 case 分支 pipeline-ui-tab | pipeline-ui-tab-20260518。
    depends_on: [T-4, T-5a, T-5b]
    estimated_stage: coding
    covers_ac: [AC-3, AC-4]
    status: pending
    commits: []
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: stage-2
    status: pending

  - id: P-code-review
    estimated_stage: stage-4
    status: pending

  - id: P-test-review
    estimated_stage: stage-6
    status: pending

  - id: P-push
    estimated_stage: stage-7
    status: pending

  - id: P-ci
    estimated_stage: stage-8
    status: self-attest
    notes: "项目无 remote 长期未决"

  - id: P-deploy
    estimated_stage: stage-9
    status: pending
    notes: "有部署面（apps/web 改动），必须真跑 deploy_verify（本机起 web dev + npm run build）"

  - id: P-user-confirm
    estimated_stage: stage-10
    status: pending
```

## DAG 健全性

```text
T-1 ──┬─→ T-2 ─┐
      └─→ T-3 ─┴─→ T-4 ──┬─→ T-5b ─┐
              └─────────────────────→ T-5a ──┴─→ T-6
                          └─→ T-7
```

无环。T-6 + T-7 是终点（真跑验证）。

## 验收覆盖矩阵

| AC | kind | 关联任务 |
|---|---|---|
| AC-1 | static | T-1, T-2, T-3, T-7 |
| AC-2 | static | T-4, T-7 |
| AC-3 | **behavioral** | T-5a, T-5b, T-6, T-7 |
| AC-4 | **behavioral** | T-6, T-7 |

**behavioral AC：AC-3 + AC-4**，满足 ≥1。
