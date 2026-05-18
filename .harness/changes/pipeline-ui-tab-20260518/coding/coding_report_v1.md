---
change_id: pipeline-ui-tab-20260518
version: 1
authored_at: 2026-05-18T12:50:00Z
branch: main（无 remote）
base_commit: 2db8c60
head_commit: (uncommitted)
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `apps/web/src/lib/api/queries.ts` | mod | 新增 3 个 TS interface（PipelineNodeRunResponse / PipelineRunResponse / PipelineRunCreatedResponse，含 nullable `\| null` 标注）+ `useCreatePipelineRun()` mutation（自定义 fetch，text/yaml body）+ `usePipelineRun(runId)` query（动态 refetchInterval，succeeded/failed 停止轮询） | T-1 / T-2 / T-3 |
| `apps/web/src/routes/repos/$owner.$name.tsx` | mod | (a) import 加 useCreatePipelineRun / usePipelineRun；(b) RepoDetailPage 末尾加 `{isAdmin && <PipelinesSection />}` ；(c) **export** PipelinesSection 组件（含 DEMO_RECIPE_YAML 字面注入 + textarea + 按钮 + Run 状态面板含 5 列节点表）| T-4 |
| `apps/web/src/lib/api/pipeline.test.tsx` | new | vitest hook 测试（vi.spyOn(globalThis, "fetch")）：(a) usePipelineRun 状态机 queued→running→succeeded + 轮询次数 ≥2；(b) useCreatePipelineRun POST yaml 含 Content-Type: text/yaml | T-5a |
| `apps/web/src/routes/repos.pipelines-section.test.tsx` | new | vitest 组件测试（vi.mock("../lib/api/queries", ...)）：(c) 默认 button disabled + 填 yaml 后 enabled + 点击触发 mutation；(d) Run 状态面板渲染 2 节点表 | T-5b |
| `scripts/_self_check.sh` | mod | 加 `run_pipeline_ui_tab` block（4 AC，含 AC-3 vitest 真跑 + AC-4 npm run build 真跑 = vite build && tsc --noEmit）+ main 调用链 + case 分支 | T-7 |

## 与 tasks.md 的映射

| Task ID | 状态 | 备注 |
|---|---|---|
| T-1 | done | 3 个 interface 含 nullable `\| null` 标注（按后端 schemas/pipeline.py 字段一对一）|
| T-2 | done | useCreatePipelineRun（参 useUploadBlob 自定义 fetch 模式）|
| T-3 | done | usePipelineRun 含 refetchInterval callback（参 useJob 模式）|
| T-4 | done | PipelinesSection（admin only；DEMO_RECIPE_YAML hardcoded；Run 状态面板含 5 列节点表 + status badge + error 区）|
| T-5a | done | hook 测试 2/2 PASS（usePipelineRun 状态机 + useCreatePipelineRun POST yaml） |
| T-5b | done | 组件测试 2/2 PASS（disabled→enabled→click + Run 面板 2 节点表）|
| T-6 | done | vitest 2 files 4/4 + npm run build 干净（含 tsc --noEmit；0 error TS）|
| T-7 | done | self_check block 4/4 PASS（自递归覆盖）|

## 偏离 spec / trade-off

### 偏离 1（export PipelinesSection）

spec T-4 未明示是否要 export PipelinesSection。stage 3 实施时为了让 T-5b 组件测试能 `import { PipelinesSection } from "./repos/$owner.$name"`（无需通过 router 进入页面 mock 10 个 hook），将 `function PipelinesSection` 改为 `export function PipelinesSection`。

不影响 TanStack Router 路由生成（routeTree.gen.ts 由 `createFileRoute("/repos/$owner/$name")` 单独驱动），不影响 tree-shaking（生产构建仅 export Route 被 router 引用，PipelinesSection 仍内联在 chunk）。

### 偏离 2（test 第 4 测 succeeded 多匹配）

`screen.getByText("succeeded")` 因 Run 状态面板的 status badge + 2 个 node 状态列共 3 处出现 → `getByText` 报 multiple match 错。改用 `getAllByText("succeeded").length >= 2` 断言，不破坏测试语义。

## 本地校验结果

### vitest 真跑（AC-3 核心证据）

```text
$ cd apps/web && npx vitest run src/lib/api/pipeline.test.tsx src/routes/repos.pipelines-section.test.tsx
 ✓ src/routes/repos.pipelines-section.test.tsx (2 tests) 390ms
   ✓ PipelinesSection > disables run button when yaml is empty and enables when filled; click triggers mutation 361ms
   ✓ PipelinesSection > renders node table with 2 rows when run.status=succeeded 28ms
 ✓ src/lib/api/pipeline.test.tsx (2 tests) 2080ms
   ✓ usePipelineRun > polls until status reaches succeeded 2072ms
   ✓ useCreatePipelineRun > POSTs yaml with text/yaml content-type and returns run_id 6ms

 Test Files  2 passed (2)
      Tests  4 passed (4)
```

### npm run build 干净（AC-4 核心证据）

```text
$ cd apps/web && npm run build
> vite build && tsc --noEmit -p tsconfig.json
vite v5.4.21 building for production...
✓ 267 modules transformed.
dist/index.html                   0.40 kB │ gzip:   0.27 kB
dist/assets/index-Cq6p59Xv.css   14.00 kB │ gzip:   3.40 kB
dist/assets/index-C3WeRkUf.js   423.49 kB │ gzip: 129.93 kB
✓ built in 2.30s
（tsc --noEmit 无输出 = 0 errors）
```

### self_check 本 change block

```text
=== pipeline-ui-tab-20260518 :: 4 AC ===
PASS  AC-1        queries.ts 加 2 个 hook + 3 个 interface（独立 grep，不用 ERE alternation）
PASS  AC-2        repos/$owner.$name.tsx 含 PipelinesSection + isAdmin gate + 2 个 hook
PASS  AC-3        vitest pipeline.test.tsx + repos.pipelines-section.test.tsx ≥4 passed
PASS  AC-4        npm run build 干净（vite build && tsc --noEmit；含 built in 不含 error TS）

=== 汇总 ===
PASS: 4
FAIL: 0
SKIP: 0
```

## 已知未解决问题

- 无（4 AC 全 PASS，build / test / lint 全干净）

## 下一步

- 准备 stage 4 review：spawn `claude-agent:pipeline-ui-tab-20260518-stage4-reviewer-v1`
- summary.md stage=`coding_review` status=`in_progress`
