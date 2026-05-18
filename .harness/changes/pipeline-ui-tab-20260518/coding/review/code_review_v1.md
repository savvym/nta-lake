---
change_id: pipeline-ui-tab-20260518
target: coding_report_v1.md（+ 5 改动文件全读）
target_version: 1
review_version: 1
reviewer: claude-agent:pipeline-ui-tab-20260518-stage4-reviewer-v1
reviewed_at: 2026-05-18T19:35:00Z
verdict: APPROVED
---

# Code Review v1

## 评审模式

artifact 模式（coding_report + git diff 实际改动文件）。

## 输入材料确认

- `.harness/agents/reviewer-agent.md`（角色定义 + reviewer 字段白名单）✅
- `.harness/skills/expert-reviewer/SKILL.md`（plan/artifact 双模式 + 评级规约）✅
- `summary.md` / `spec.md v2` / `tasks.md v2` / `coding_report_v1.md`✅
- 5 个改动文件全文（queries.ts / repos/$owner.$name.tsx / pipeline.test.tsx / repos.pipelines-section.test.tsx / scripts/_self_check.sh `run_pipeline_ui_tab`）✅
- 后端 schema 源 `apps/api/dataplat_api/schemas/pipeline.py`（TS 对齐核对）✅
- demo recipe 源 `recipes/examples/demo-bronze-to-gold.yaml`（DEMO_RECIPE_YAML 比对）✅

## 4 AC 真覆盖独立复检

> 不依赖 coding_report 自报数；reviewer 本会话独立真跑。

### AC-1 static（queries.ts +2 hook +3 interface 含 nullable）

独立执行 self_check 块：

```
PASS  AC-1        queries.ts 加 2 个 hook + 3 个 interface（独立 grep，不用 ERE alternation）
```

代码层核对（queries.ts L257-323）：
- 3 个 interface 字段一对一对齐 `schemas/pipeline.py`：
  - `PipelineNodeRunResponse`：node_id / processor_name / processor_version / config / status / cache_hit / **output_commit_hash: string | null** / **input_commits: string[] | null** / **cache_key: string | null** / **error: string | null** ↔ Pydantic `str | None = None` × 4，全对齐 ✅
  - `PipelineRunResponse`：run_id / recipe_name / status / **error: string | null** / created_by / node_runs ↔ Pydantic 对齐 ✅
  - `PipelineRunCreatedResponse`：run_id / job_id ↔ 对齐 ✅
- `useCreatePipelineRun`：POST `/api/pipelines/runs:from-yaml`，`Content-Type: text/yaml`，raw body=yaml，参 useUploadBlob 模式（不走 fetchJson），错误兜底 throw new Error ✅
- `usePipelineRun(runId | null)`：refetchInterval callback 形态对 TanStack v5 API；succeeded/failed 返 false（停轮询），其他返 1000ms ✅

### AC-2 static（PipelinesSection + admin gate + textarea + 节点表 5 列）

```
PASS  AC-2        repos/$owner.$name.tsx 含 PipelinesSection + isAdmin gate + 2 个 hook
```

代码层核对（$owner.$name.tsx L575-748）：
- `isAdmin && <PipelinesSection ... />` 挂在 RepoDetailPage L152，门控正确 ✅
- textarea L641-648 + "粘贴 demo recipe" 按钮 L632-639 + DEMO_RECIPE_YAML 字面 L577-595 ✅
- "运行 Pipeline" 按钮 L651-656 disabled 条件 `!yamlText.trim() || createRun.isPending` ✅
- 错误显示 L649（mutation 失败）+ L680-684（run.error <pre>）✅
- Run 状态面板 5 列节点表（node / processor / status / cache / output_commit）L685-741 ✅
- status badge 颜色分支（succeeded/failed/其他）L668-677 ✅
- 轮询停止逻辑：由 `usePipelineRun` 内置 refetchInterval callback（不在组件外加 useEffect 干预，干净）✅

### AC-3 behavioral（vitest 真跑 ≥4 测试 PASS）

```
$ cd apps/web && npx vitest run src/lib/api/pipeline.test.tsx src/routes/repos.pipelines-section.test.tsx
 ✓ src/routes/repos.pipelines-section.test.tsx (2 tests) 413ms
 ✓ src/lib/api/pipeline.test.tsx (2 tests) 2081ms
 Test Files  2 passed (2)
      Tests  4 passed (4)
```

reviewer 独立跑出来与 coding_report 自报一致。4/4 真 PASS。

测试设计核对：
- pipeline.test.tsx (a) usePipelineRun：`vi.spyOn(globalThis, "fetch")` mock 序列 queued/running/succeeded；`waitFor` 直到 data.status==="succeeded"；断言 `fetchSpy.mock.calls.length >= 2`（≥2 次轮询）✅
- pipeline.test.tsx (b) useCreatePipelineRun：捕获 url / contentType / body，断言 `/api/pipelines/runs:from-yaml` + `text/yaml` + body 含 "name: x" ✅
- repos.pipelines-section.test.tsx (c) 默认 button disabled → 填 yaml → enabled → 点击触发 mutation ✅
- repos.pipelines-section.test.tsx (d) mock `usePipelineRun` 返 succeeded + 2 节点 → 节点表 2 行渲染 ✅

### AC-4 behavioral（npm run build 干净 = vite build && tsc --noEmit）

```
$ cd apps/web && npm run build
vite v5.4.21 building for production...
✓ 267 modules transformed.
dist/index.html                   0.40 kB
dist/assets/index-Cq6p59Xv.css   14.00 kB
dist/assets/index-C3WeRkUf.js   423.49 kB
✓ built in 2.28s
```

reviewer 独立真跑 npm run build 成功；`tsc --noEmit` 无输出 = 0 type error。AC-4 真 PASS。

**4/4 AC 全 real-verified，self_check 输出与 coding_report 一致。**

## 代码层审查 checklist

### TS interface ↔ 后端 schema 对齐

| 字段 | 后端 (schemas/pipeline.py) | 前端 (queries.ts) | 状态 |
|---|---|---|---|
| PipelineNodeRunResponse.output_commit_hash | `str \| None = None` | `string \| null` | ✅ |
| PipelineNodeRunResponse.input_commits | `list[str] \| None = None` | `string[] \| null` | ✅ |
| PipelineNodeRunResponse.cache_key | `str \| None = None` | `string \| null` | ✅ |
| PipelineNodeRunResponse.error | `str \| None = None` | `string \| null` | ✅ |
| PipelineRunResponse.error | `str \| None = None` | `string \| null` | ✅ |
| RecipeNode.config | `dict[str, Any]` (default_factory) | `Record<string, unknown>` | ✅ |
| node_runs | `list[PipelineNodeRunResponse]` | `PipelineNodeRunResponse[]` | ✅ |

nullable 真到位，无字段漂移。

### PipelinesSection 组件细节

- admin gate：父层 `{isAdmin && <PipelinesSection .../>}` 用 IngestSection 同模式 ✅
- textarea 输入：受控（value=yamlText, onChange=setYamlText）✅
- Run 面板节点表 5 列：node / processor / status / cache / output_commit_hash（截 12 字符）✅
- 错误显示：mutation error 走 `error` state + `<div class="text-sm text-red-600">`；run.error 走 `<pre class="max-h-32 overflow-auto whitespace-pre-wrap">` ✅
- 轮询停止：依赖 `usePipelineRun` 内置 refetchInterval callback（succeeded/failed → false），无需组件外控制 ✅

### 偏离 1 评估（export PipelinesSection）

trade-off：组件测试 (T-5b) import 时不通过 router 进入，仅 import `PipelinesSection`。

- vs route 生成：TanStack Router routeTree.gen.ts 由 `createFileRoute("/repos/$owner/$name")` 驱动；只识别 `Route` export，新增 `PipelinesSection` named export 不会被注册为 child route ✅（依然只有 `/repos/$owner/$name` 一个 route）
- vs tree-shaking：production 构建（npm run build 已真跑通过）只有 Route 被 router 引用，PipelinesSection 仍内联在 chunk；引入命名 export 不影响 bundle size（已用 `423.49 kB / gzip: 129.93 kB` 印证；与改动前同量级）✅
- 合理性：相比 mock 10 个 hook 拉整页 render 的成本，单独 export 测试组件是干净的取舍 ✅

**结论：偏离 1 合理**。

### vitest mock 策略评估

| 测试文件 | mock 策略 | 评估 |
|---|---|---|
| pipeline.test.tsx | `vi.spyOn(globalThis, "fetch")` | hook 层测试聚焦 fetch 行为（url / content-type / body / 轮询次数）；真跑 useQuery 状态机 + refetchInterval ✅ 合理 |
| repos.pipelines-section.test.tsx | `vi.mock("../lib/api/queries", ...)` | 组件层测试聚焦 UI 状态机（按钮 disabled/enabled / 节点表渲染）；隔离 fetch 细节 ✅ 合理；与既有 `repos.test.tsx` 模式一致 |

两种 mock 策略**各得其所**——hook 测试要测 fetch + 轮询，必须 spy 真 fetch；组件测试要测 UI 状态机，必须 mock 整个 queries 模块。

### `void owner; void name;` 评估（用户特别 flag）

设计意图：PipelinesSection 接受 `owner` + `name` props 是为了**未来扩展**（如把 owner/name 注入 DEMO_RECIPE_YAML，让 demo 跑当前 repo 而非 hardcoded `demo/raw-md`）。当下 MVP DEMO_RECIPE_YAML 是 hardcoded 字面，owner/name 暂未使用。

`void owner; void name;` 是 TypeScript 抑制 `noUnusedParameters` 编译错误的惯用法（`tsc --noEmit` 配 strict 模式会报 TS6133）。

**这是设计 bug 还是合理过渡**？

- coding_report 偏离声明里**没有显式说明** `void owner; void name;` 的存在理由
- spec / tasks 也未明示 owner/name 是否要在 PipelinesSection 内部使用（spec L52 描述 PipelinesSection 是 `{isAdmin && <PipelinesSection owner={owner} name={name} />}`，按 IngestSection 模式传入；但内部用不用未说）
- IngestSection 内部**真用**了 owner/name（POST /api/repos/{owner}/{name}/blobs + enqueueIngest body 包 owner/name）
- PipelinesSection 当下**不需要** owner/name（POST /api/pipelines/runs:from-yaml 路径无 owner/name 占位；body 是 yaml 字面）

**评估**：这是**有意识的预留**——保留 prop 签名（与 IngestSection 对齐）+ `void` 抑制 unused 编译警告。不是 bug，但**有改进空间**：

- 选项 A：现在就用 owner/name 替换 DEMO_RECIPE_YAML 里 hardcoded `demo/raw-md`（动态注入当前 repo 路径）→ UX 更好
- 选项 B：删 props 签名，组件不接 owner/name（直到真需要时再加）
- 选项 C（当前）：保留 + void（预留 props 但不用）

选项 C 是合理过渡，未阻塞。归 **NICE TO HAVE**（不强求；follow-up `pipeline-ui-recipe-editor-*` 时再决定）。

## 安全 / UX 审查

### XSS / overflow on `run.error <pre>`（用户特别 flag）

代码：
```tsx
<pre className="text-xs text-red-700 bg-red-50 p-2 rounded max-h-32 overflow-auto whitespace-pre-wrap">
  {runQuery.data.error}
</pre>
```

- React JSX 文本插值（`{runQuery.data.error}`）**默认对字符串做 HTML 转义**——任何 `<script>` 注入都会变成纯文本展示，不会执行。✅ 无 XSS 风险
- overflow：`max-h-32`（8rem）+ `overflow-auto` + `whitespace-pre-wrap`——内容超过滚动展示，UI 不会被撑爆。✅ 合理
- 字符长度：后端 `pipeline-orchestrator-mvp` 已做 `[:500]` 截断（pipeline.py 引用过），前端无需再截。✅
- 风险评估：`<pre>` 用于错误堆栈展示是 web 标准实践，等价 `<div>` + 文本插值。**无安全 / UX 缺陷**。

### YAML 输入 sanitize（用户特别 flag）

- 前端 textarea **不做 sanitize**——直接 raw POST body=yaml（`Content-Type: text/yaml`）
- 后端 `routers/pipelines.py` → `load_recipe(yaml_text)` → `yaml.safe_load(...)`
  - `yaml.safe_load`：禁 `!!python/object/...` 等 Python tag 反序列化，**避免 YAML deserialization RCE**。✅
  - Pydantic `Recipe.model_validate(...)` + `model_config = ConfigDict(extra="forbid")`：拦截未知字段。✅
  - field_validator 校验 processor / inputs / output 引用形态。✅
- **前端不做 sanitize 是正确的**——sanitize 由后端 `yaml.safe_load` + Pydantic 守门，前端动手反而降低 trust 边界清晰度（参考 OWASP "validate input at trust boundary"）。✅

### DEMO_RECIPE_YAML 内容一致性（用户特别 flag）

`repos/$owner.$name.tsx` L577-595 内联 vs `recipes/examples/demo-bronze-to-gold.yaml`：

```diff
recipes/examples/demo-bronze-to-gold.yaml（lines 1-23）:
- (lines 1-4: 4 行注释 + 1 空行)
  name: demo-bronze-to-gold

  nodes:
    - id: normalize
      processor: markdown-normalize@0.1
      ...
```

- 字面内容：从 `name: demo-bronze-to-gold` 起到结尾，**逐字一致**（已用 awk + diff 真验证）
- 差异：内联 hardcoded **去掉了头部 4 行注释**（行 1-4 是源文件的实现注释，不进入实际 recipe 语义）
- 是否有漂移风险：未来 demo recipe 更新时（如改 model_id / records_per_doc），前端 hardcoded 字面**不会自动同步**。已在 spec / tasks 决策中标记 "字面 hardcoded"；可在 follow-up 用 vite asset import（如 `?raw`）取替（NICE TO HAVE）。
- **当前**：内容一致，**无 bug**。

### admin gate 安全性

- 前端 `{isAdmin && <PipelinesSection .../>}` 仅做 UI 隐藏
- 后端 `routers/pipelines.py` 由 `require_admin` 守门（已在 pipeline-orchestrator-mvp 落地）
- 前端隐藏是 UX 优化，**不当安全防线**（risk 表中已明示）✅

## 测试质量审查

### act() warning（vitest 真跑时观察到）

reviewer 真跑时 stderr 出现：

```
Warning: An update to PipelinesSection inside a test was not wrapped in act(...).
```

来源：repos.pipelines-section.test.tsx 测试 (c) `fireEvent.click(button)` 触发 mutation；mutation 是 async，resolve 后 setActiveRunId → state update 未包 act。

- **不影响 test PASS**（4/4 仍通过）
- 是 React Testing Library 18 + async mutation 的已知噪声；规范做法是 `await act(async () => { ... })` 或 `await waitFor(() => expect(mockMutateAsync).toHaveBeenCalled())`
- 实际测试 (d) 用了 `await screen.findByText("normalize")` 等异步等待，**已规避**；测试 (c) 没有等待 mutation resolve 后的 setState（不需要断言后续状态，只断 mutateAsync 被调）

归 **NICE TO HAVE**（测试可读性优化，不影响正确性）。

### test name 可读性

测试名都是具体行为（`polls until status reaches succeeded` / `POSTs yaml with text/yaml content-type and returns run_id` / `disables run button when yaml is empty and enables when filled; click triggers mutation` / `renders node table with 2 rows when run.status=succeeded`）——符合 expert-reviewer SKILL § 1 artifact mode：「测试名能反映场景，不是 test_1」✅

### mock 范围合规

- `vi.spyOn(globalThis, "fetch")`：仅 mock 网络层 ✅（不 mock data access layer）
- `vi.mock("../lib/api/queries", ...)`：仅 mock UI 输入的 hook 层 ✅（不 mock data access layer）

符合 `.harness/rules/coding-style.md` § 1.7「数据访问层禁 mock」隐含约束。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| N-1 | `apps/web/src/routes/repos/$owner.$name.tsx` L604-605 `void owner; void name;` | PipelinesSection 接 owner/name props 但内部未用（用 void 抑制 noUnusedParameters）；coding_report 未声明此偏离的过渡定位 | 选项 A：动态注入 owner/name 到 DEMO_RECIPE_YAML 替换 hardcoded `demo/raw-md`（UX 更好）；选项 B：删 props（直到真需要）；当前选项 C 合理过渡，建议在下次 follow-up `pipeline-ui-recipe-editor-*` 时决定 |
| N-2 | `repos.pipelines-section.test.tsx` 测试 (c) | `fireEvent.click(button)` 后 mutation async resolve 引发 setActiveRunId state update 未包 act → stderr warning（不影响 PASS） | 测试末追加 `await waitFor(() => expect(mockMutateAsync).toHaveBeenCalled())`；或不断言 mutation 完成后的状态（保持当前行为也可） |
| N-3 | `apps/web/src/routes/repos/$owner.$name.tsx` L577-595 DEMO_RECIPE_YAML 字面 hardcoded | 与 `recipes/examples/demo-bronze-to-gold.yaml` 漂移风险（recipe 未来更新前端不同步） | follow-up 用 vite `import yamlText from "../../recipes/examples/demo-bronze-to-gold.yaml?raw"`（需 monorepo path 调整） |
| N-4 | `coding_report_v1.md` § 偏离 | 未列出 `void owner; void name;` 作为第 3 个偏离 | 下版本 coding_report 可补「偏离 3：PipelinesSection 接 owner/name props 但 MVP 阶段不使用，用 void 抑制编译错误，预留未来扩展」 |

## Verdict

**APPROVED**

理由：
1. **4 AC 全 real-verified PASS**（reviewer 独立真跑 self_check + vitest + npm run build，与 coding_report 自报一致）
2. **TS interface 与后端 Pydantic schema 100% 字段对齐**（4 个 nullable 字段全标）
3. **PipelinesSection 设计干净**（admin gate / textarea / 5 列节点表 / 错误显示 / 轮询停止逻辑全到位）
4. **2 个偏离均合理**（export PipelinesSection 用于测试隔离；succeeded 多匹配用 getAllByText）
5. **无 XSS / overflow / yaml deserialization 风险**（React 转义 + 后端 yaml.safe_load + Pydantic 守门）
6. **DEMO_RECIPE_YAML 与源 yaml 字面一致**（去注释后 byte-for-byte 同；diff 真验证）
7. **测试 mock 策略合规**（仅 mock 网络 / hook 层；不 mock data access）
8. 4 个 NICE TO HAVE 均不阻塞（void props / act warning / yaml hardcoded / coding_report 补偏离），可在 follow-up 处理

无 MUST FIX、无 SHOULD FIX → 进入 stage 5（单测编写）。

## 后续指引

generator (Application Owner) 复检步骤：

1. 复核本 review APPROVED；如有不同意见，在 coding_report 补 deferred 说明或开 v2 重提
2. NICE TO HAVE N-1/N-2/N-3/N-4 不阻塞 stage 5；可选在 stage 5 单测编写时一并处理 N-2（act warning）
3. 推进 stage 5（unit_test）；按 reviewer-agent.md spawn stage 6 reviewer
4. 复检命令：
   ```bash
   DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
     DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
     DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh pipeline-ui-tab
   ```
   期望：`PASS: 4 / FAIL: 0`
5. summary.md stage 4 行追加：`v1`, `APPROVED`, MUST FIX=0, `coding/review/code_review_v1.md`
