---
change_id: pipeline-ui-tab-20260518
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:pipeline-ui-tab-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T13:05:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

> 评审者声明：本 reviewer 是独立 sub-agent，未参与本 change spec/tasks 撰写；通过 prompt 拿到必读路径，完整读了 expert-reviewer SKILL §1 / request-analysis SKILL § "跨 AC 9 条" + "AC 分层规约" / 后端 schemas/pipeline.py + routers/pipelines.py / 前端 queries.ts + repos/$owner.$name.tsx + repos.test.tsx + jobs.$job_id.test.tsx + package.json + vite.config.ts + pnpm-lock.yaml + node_modules/.pnpm/@tanstack+query-core@5.100.10 d.ts。

## stage 2 AC kind 必查 3 项

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | AC 表存在 `kind` 列 | ✅ PASS | spec.md L63 表头 `\| ID \| kind \| 描述 \| 验证方式 \| 期望 \|`；`awk` 提取 §验收标准段 + `grep -qE '^\\|[^\|]*\\|[[:space:]]*kind[[:space:]]*\\|'` 命中 |
| 2 | 至少 1 行 AC 的 kind 单元格真值 `behavioral`（锚定 AC 行 regex，不接受裸字串） | ✅ PASS | AC-3 + AC-4 两行 kind 单元格值 `**behavioral**`；`grep -qE '^\\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\\|[[:space:]]*(\\*\\*)?behavioral(\\*\\*)?[[:space:]]*\\|'` 命中 |
| 3 | frontmatter 是否声明 `ac_kind_lint: exempt`（如是必跑 git diff --stat 验证范围） | ✅ N/A | spec.md frontmatter L1-6 无 `ac_kind_lint: exempt` 声明，无需 git diff 校验 |

三项全 PASS，AC 分层规约硬约束**未违反**——但下面发现的其它问题仍构成 REVISION REQUIRED（详 MUST FIX 表）。

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 spec）

- [x] 背景写明了为什么现在做（pipeline-orchestrator-mvp 后端就绪，前端缺；用户原始诉求"web 一键跑全流程"）
- [x] 问题陈述对外部读者可理解（3 条具体缺失：触发 UI / 状态 UI / 轮询）
- [x] 范围 / 非范围都有（in-scope 4 条 AC；非范围 7 项 follow-up，含 SSE/lineage/recipe-editor 等）
- [~] 每条验收标准可演示且可机械化 —— **AC-1/AC-4 验证命令有实质 bug**（详 MUST FIX-1/MUST FIX-3）
- [x] 风险有缓解或显式 accept（5 条风险全配缓解，含 callback API 风险、Content-Type 风险、msw schema 漂移）
- [x] 没有把已有架构当新提案（refetchInterval callback / fetchJson 自定义 fetch 模式都引用既有 `useJob` / `useUploadBlob`）
- [x] 待澄清问题已清零

## 跨 AC 一致性自审 9 条（reviewer 复核）

| # | checklist 条目 | 结果 | 备注 |
|---|---|---|---|
| 1 | schema 字段 ↔ hash ↔ idempotency ↔ fixture 一致 | ✅ N/A | 纯前端 change，无 hash/idempotency 链路 |
| 2 | 事务边界 AC / 风险 / tasks 一字不差 | ✅ N/A | 无事务边界 |
| 3 | AC 验证命令一行式可执行 | ❌ FAIL | 见 MUST FIX-1（AC-1 验证命令字面 `\|` 在 grep -E 是字面竖线 → 永远 miss） |
| 4 | 风险缓解 ↔ AC 测试列表 | ⚠️ 弱 | 风险表 "callback API 变化" 缓解写"vitest 测试用 mocked timers 验证停止轮询"——AC-3 (a) 已覆盖 |
| 5 | commit 历史链连续性 | ✅ N/A | 无写 commit 路径 |
| 6 | 反向 grep 配 `test -f` 前置 + 不吞 stderr | ⚠️ AC-4 隐式风险 | AC-4 用 `grep ... ! grep -q "error"` 过宽，见 SHOULD FIX-1 |
| 7 | process_tasks 6 条必填 + estimated_stage 命名 | ❌ FAIL | tasks.md `process_tasks` 用了 `request_analysis_review` 等长名，不是 `stage-2` 形态，违反 SKILL §第 7 条 grep 自查公式 → 见 tasks_review_v1.md MUST FIX-T-1 |
| 8 | AC 验证命令 dry-parse（真跑 syntax 检查） | ❌ FAIL | AC-1 `\|` 反斜杠转义 → grep -E 不匹配，bash 不报 syntax error，但 semantic 假阴性（见 MUST FIX-1） |
| 9 | summary.md frontmatter 无模板占位符 | ✅ PASS | summary.md L1-15 frontmatter 全部填实值，无 `<feature-slug>` / `<YYYY-MM-DDTHH:MM:SSZ>` 占位 |

## 必查 2：TS schema 对齐后端（按 apps/api/dataplat_api/schemas/pipeline.py 逐字段校对）

| 后端字段（pipeline.py） | spec 描述 | 字段名 | nullability | 嵌套 |
|---|---|---|---|---|
| `PipelineNodeRunResponse.node_id: str` | AC-1 + T-1 列 `node_id` | ✅ | 后端非 None；spec 未明示 → 前端默认 `string` 安全 | — |
| `processor_name: str` | T-1 列 `processor_name` | ✅ | 同上 | — |
| `processor_version: str` | T-1 列 `processor_version` | ✅ | — | — |
| `config: dict[str, Any]` | T-1 列 `config` | ✅ | — | TS 应为 `Record<string, unknown>` |
| `status: str` | T-1 列 `status` | ✅ | — | — |
| `cache_hit: bool` | T-1 列 `cache_hit` | ✅ | — | — |
| `output_commit_hash: str \| None = None` | T-1 列 `output_commit_hash` | ✅ | ❌ **spec 未明示 `\| null`** —— MUST FIX-2 | — |
| `input_commits: list[str] \| None = None` | T-1 列 `input_commits` | ✅ | ❌ **未明示 nullable** —— MUST FIX-2 | TS `string[] \| null` |
| `cache_key: str \| None = None` | T-1 列 `cache_key` | ✅ | ❌ **未明示 nullable** —— MUST FIX-2 | — |
| `error: str \| None = None` | T-1 列 `error` | ✅ | ❌ **未明示 nullable** —— MUST FIX-2 | — |
| `PipelineRunResponse.run_id: str` | T-1 列 | ✅ | — | — |
| `recipe_name: str` | T-1 列 | ✅ | — | — |
| `status: str` | T-1 列 | ✅ | — | — |
| `error: str \| None = None` | T-1 列 | ✅ | ❌ **未明示 nullable**——AC-2 Run 状态面板"run.error（如有）"会 render，TS 漏 nullable → 运行期访问可能报错 | — |
| `created_by: str` | T-1 列 | ✅ | — | — |
| `node_runs: list[PipelineNodeRunResponse]` | T-1 列 | ✅ | — | TS `PipelineNodeRunResponse[]` |
| `PipelineRunCreatedResponse.run_id: str` | T-1 + AC-2 用 `res.run_id` | ✅ | — | — |
| `job_id: str` | T-1 + AC-2 "job_id 写入 console for debug" | ✅ | — | — |

**结论**：字段名 / 嵌套结构与后端完全一致；但 **5 个 nullable 字段（`output_commit_hash` / `input_commits` / `cache_key` / `node.error` / `run.error`）在 AC-1 / T-1 描述里未明示 `\| null`**，coding 阶段易实现成 non-null TS interface → 后续真 pipeline 失败时 `run.error` 非空 / `output_commit_hash` 为 null 等场景类型不匹配 → MUST FIX-2。

## 必查 3：refetchInterval callback API（TanStack v5.100.10 实读 d.ts）

| 验证项 | 结果 | 证据 |
|---|---|---|
| 仓库实装 react-query 版本 | v5.100.10 | `apps/web/package.json` L15 `"@tanstack/react-query": "^5.100.10"` + `node_modules/@tanstack/react-query/package.json` `"version": "5.100.10"` |
| 实际 query-core d.ts | v5.100.10 | `node_modules/.pnpm/@tanstack+query-core@5.100.10/node_modules/@tanstack/query-core/build/legacy/_tsup-dts-rollup.d.ts` L1679 |
| `refetchInterval` callback 签名 | ✅ 合法 | `refetchInterval?: number \| false \| ((query: Query<TQueryFnData, TError, TQueryData, TQueryKey>) => number \| false \| undefined);` |
| 仓库现有同模式实践 | ✅ 已用 | `apps/web/src/lib/api/queries.ts` L166-172 `useJob` 已用 `refetchInterval: (query) => { const data = query.state.data as JobRead ...; ... return false; }` 模式 |

**结论**：T-3 描述的 `refetchInterval: (query) => { const status = query.state.data?.status; if (status === 'succeeded' \|\| status === 'failed') return false; return 1000; }` callback 形态**与 v5.100.10 类型完全兼容**，且仓库已有先例。风险表第 1 条已显式 accept 此风险并配 vitest mocked timer 测试缓解——**无问题**。

## 必查 4：测试 mock 路径可行性（实读 repos.test.tsx + jobs.$job_id.test.tsx + pnpm-lock.yaml）

| 验证项 | 结果 | 证据 |
|---|---|---|
| 仓库是否真正安装 msw | ❌ **未安装** | `apps/web/package.json` deps/devDeps 全文无 `msw`；`pnpm-lock.yaml` 仅有 `msw: ^2.4.9` 作为 `@vitest/mocker@2.1.9` 的 **optional peer**（L706-710）；安装树未实例化 msw 包 |
| 现存 6 个测试文件用什么 mock 模式 | `vi.mock("../lib/api/queries", ...)` 模块级 mock | repos.test.tsx L8 / repos.new.test.tsx L12 / repos.files-section.test.tsx L16 / jobs.$job_id.test.tsx L16 / commits.$owner.$name.$hash.test.tsx L15 / login.test.tsx L8 全部一致 |
| `vi.spyOn(global, 'fetch')` 或 `fetch` spy 使用 | ❌ 无 | grep `vi\.spyOn\|setupServer\|rest\.` 全仓 0 命中 |
| spec summary.md L32 描述 | `"vitest 跑 PipelinesSection 用 msw mock /api 端点"` | summary.md L32 字面写"msw" |
| spec.md T-5 / tasks.md T-5 描述 | `"参考 ... msw / vi.spyOn(global, 'fetch') 路径"` | tasks.md L100 |

**结论**：spec 内部矛盾——summary.md 写 "msw"、tasks.md 又写 "msw / fetch spy"，但仓库**两者都没用**且 msw 未装。AC-3 (a) "usePipelineRun 状态机：mocked fetch 序列 queued → running → succeeded，断言 mock fetch 调用次数 ≥ 2" 必须真起 hook + 推 fake timer + spy fetch（否则 mock 整个 queries 模块就绕过了 hook 内部 refetchInterval 逻辑，无法验证轮询机制）；AC-3 (c)(d) PipelinesSection 渲染又**必须 mock hook 层**（否则得装 msw + setupServer，但仓库没装）。**两种策略互斥且 spec 未澄清各自归宿** → MUST FIX-4。

## 必查 5：vite build AC-4 是否真验证生产构建

| 验证项 | 结果 | 证据 |
|---|---|---|
| spec AC-4 命令 | `cd apps/web && npx vite build 2>&1 \| tail -3` 含 `built in` 不含 `error` | spec.md L68 |
| 仓库 package.json 真正的 build script | `"build": "vite build && tsc --noEmit -p tsconfig.json"` | apps/web/package.json L7 |
| spec AC-4 是否包含 tsc --noEmit | ❌ **缺** | spec 只跑 vite build，不跑 tsc --noEmit |
| 类型错误是否会被 vite build 拦截 | ❌ **不会** | vite 用 esbuild 转译，不做 strict TS 检查；缺 tsc 步骤 → AC-1/T-1 漏 nullable 在 vite build 仍能 PASS，但生产环境 runtime 报错 |
| AC-4 `! grep -q "error"` 反向 grep | ⚠️ 过宽 | vite build stderr/stdout 可能含字串 "error" 即使无致命错（warnings / deprecation 消息），易假 FAIL；且未 `test -f dist/index.html` 正向断言（违反跨 AC 第 6 条修复模板） |

**结论**：AC-4 命令未真验证完整生产构建路径（缺 tsc），且反向 grep 不健壮 → MUST FIX-3 / SHOULD FIX-1。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md AC-1 验证方式（L65） | `grep -qE "interface PipelineRunResponse\|interface PipelineNodeRunResponse"`——bash 字串里 `\|` 传给 grep -E 是**字面竖线**，不是 ERE alternation。**实证**：`printf 'interface PipelineRunResponse {}\n' \| grep -qE 'interface PipelineRunResponse\|interface PipelineNodeRunResponse' && echo HIT \|\| echo MISS` 输出 `MISS`；去掉反斜杠输出 `HIT`。AC-1 即便代码已正确实现也会**假 FAIL**。同样问题潜在影响 AC-2 验证里 `"useCreatePipelineRun\|usePipelineRun"`（仓库 grep -E 行为同上）。**另**：AC-1 grep 只断言了 `interface PipelineRunResponse` / `interface PipelineNodeRunResponse` 两个，**漏 `PipelineRunCreatedResponse`**（T-1 列了 3 个 interface） | 改用单引号纯命令 + `grep -qE 'interface PipelineRunResponse\|interface PipelineNodeRunResponse\|interface PipelineRunCreatedResponse'`（markdown `\|` 转义只在表格列分隔；写命令时本就要把"想给 grep 的 alternation"写成裸 `\|`），并在 T-7 抄入 `_self_check.sh` 时**实际写两个表达式 AND** 或 grep alternation 用 `\\|` 在 bash 解析后变 `\|`、shell 字串里实际为 `|`——最稳：把单个 grep 拆三条 `grep -q ... && grep -q ... && grep -q ...` 避免 alternation 转义坑。Generator 自查：复制 spec 命令到 shell 真跑（dry-parse 已不够，必须真跑），命中 `MISS` 则 spec 修。 |
| MUST FIX-2 | spec.md AC-1 + tasks.md T-1（L15-22） | TS interface 字段描述未明示 nullable。后端 `pipeline.py`：`PipelineNodeRunResponse.{output_commit_hash, input_commits, cache_key, error}` + `PipelineRunResponse.error` 共 5 个字段 `\| None = None`。spec 写"对齐 schema"但**未列 nullability 矩阵**，coding 阶段 generator 易写成 `string` / `string[]`（非 nullable），AC-2 "run.error（如有）"渲染时 TS 不报错但运行期可能 access null 字段 → 影响 AC-3 (d) 节点表展示 cache_hit=false 节点（output_commit_hash 为 null）时 `.slice(12)` 抛错 | T-1 description 补充字段表 + 明示 `\| null`：`output_commit_hash: string \| null`；`input_commits: string[] \| null`；`cache_key: string \| null`；`error: string \| null`；`PipelineRunResponse.error: string \| null`。AC-3 (d) 测试增加一条 mock 场景：节点 status=running / cache_hit=false / output_commit_hash=null，断言渲染不抛错（运行时 null safety） |
| MUST FIX-3 | spec.md AC-4 + tasks.md T-6 验证方式（L68 / L107-119） | AC-4 只跑 `npx vite build`，缺 `tsc --noEmit -p tsconfig.json`。仓库 `apps/web/package.json` L7 真正 build 是 `"vite build && tsc --noEmit"`。Vite 用 esbuild 转译期**不做 strict TS 检查**——MUST FIX-2 列的 nullable 漏标在 vite build 阶段不暴露，但 `tsc --noEmit` 会。AC-4 自称 "behavioral 真跑生产构建"但实际**没跑全 build 链** | AC-4 命令加 `&& npx tsc --noEmit -p tsconfig.json` 或改用 `npm run build`（直接调 package.json 里的脚本）；T-6 命令同步改。复检：`cd apps/web && npx tsc --noEmit -p tsconfig.json` 退码 0 |
| MUST FIX-4 | spec.md AC-3 + tasks.md T-5 + summary.md L32 | 测试 mock 策略**仓库不可行 + 内部矛盾**：(a) `apps/web/package.json` 与 `pnpm-lock.yaml` 显示 **msw 未真安装**（仅 @vitest/mocker optional peer 提及），summary.md L32 + spec AC-4 + tasks.md T-5 都提"msw" → coding 阶段会卡在 `pnpm i msw`；(b) 仓库 6 个现存测试**统一用 `vi.mock("../lib/api/queries", ...)`** 模式，spec T-5 (c)(d) PipelinesSection 渲染必须沿此路；(c) 但 T-5 (a) `usePipelineRun 状态机：mocked fetch 序列 queued → running → succeeded，断言 mock fetch 调用次数 ≥ 2` 必须**真跑 hook + 推 fake timer + spy fetch**（如果整个 queries 模块被 vi.mock，hook 内部的 refetchInterval / queryFn / fetchJson 都被替换，无法验证轮询机制）；(d) 两种策略互斥但 spec 未澄清各自归宿 | (1) 删除"msw"措辞，明确策略：`(a)` 测试 `usePipelineRun` 状态机用 `vi.spyOn(global, 'fetch')`（不 mock queries 模块）+ `renderHook` + `act` + `vi.useFakeTimers()` + `vi.advanceTimersByTime` 推时间；`(b)` 测试 `useCreatePipelineRun` 同上；`(c)(d)` PipelinesSection 渲染用 `vi.mock("../lib/api/queries", ...)` 模块级 mock，注入 `useCreatePipelineRun` / `usePipelineRun` 的 mocked 返回值。(2) 修改 summary.md L32 + spec AC-4 表述去掉 "msw"。(3) T-5 description 拆分明示 (a)(b) vs (c)(d) 用不同 mock 路径。(4) 风险表 #4 "msw mock 与真实后端响应 schema 漂移"删掉或改成 "TS interface 与后端 pydantic 漂移"——靠 MUST FIX-3 的 tsc --noEmit + openapi-typescript 兜底 |
| MUST FIX-5 | tasks.md `process_tasks`（L142-168） | `estimated_stage` 值写的是 `request_analysis_review` / `coding_review` / `unit_test_review` / `ci_result` / `deployment` / `user_confirmation`——**不符合** SKILL §跨 AC 第 7 条要求的 `stage-2` / `stage-4` / `stage-6` / `stage-7` / `stage-9` / `stage-10` 形态。Generator 自查公式 `grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md` 期望 ≥ 6，但**当前会 = 0** | `process_tasks` 6 项 `estimated_stage` 改为 `stage-2` / `stage-4` / `stage-6` / `stage-7` / `stage-9` / `stage-10`（参考 pipeline-orchestrator-mvp-20260518 / harness-ac-behavioral-tier-20260518 既有 closed change 形态）。如团队偏好长名，必须在 `request-analysis/SKILL.md` 跨 AC 第 7 条把 grep 公式同步改宽（不属于本 change 范围） |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md AC-4 验证方式 | `vite build 2>&1 \| tail -3` 含 `built in` 不含 `error`——反向 grep 过宽（vite 输出可能含 "errorOverlay" / "errorCallback" / "errorHandler" 等字串作为代码导出名，不代表构建失败），且**缺正向断言** `test -f apps/web/dist/index.html`（违反 SKILL §跨 AC 第 6 条修复模板：(a) `test -f` 前置 (b) 正向断言 (c) 不吞 stderr） | 改成：`cd apps/web && npx vite build 2>&1 \| tee /tmp/vite-build.log; echo "exit=$?" >> /tmp/vite-build.log; test -f apps/web/dist/index.html && grep -q "built in" /tmp/vite-build.log && grep -q "^exit=0$" /tmp/vite-build.log`。或更简单：`cd apps/web && npx vite build && test -f dist/index.html`（vite 非 0 退码会中断 `&&` 链，比 grep `! error` 更准确） |
| SHOULD FIX-2 | spec.md §AC-2 + §风险表第 5 行 | "admin only" 模式声明前端隐藏 button + 后端 require_admin。但 AC-2 验证命令只 grep `"isAdmin && <PipelinesSection"`，**没断言**当 isAdmin=false 时 PipelinesSection 不渲染（前端 hide 是 UX，但 spec 自称"admin only"含语义）。T-5 测试也没覆盖 isAdmin=false 路径 | T-5 加一条测试 (e)：`renderWithProviders(<RepoDetailPage />, { mockMe: { role: "viewer" } })` 断言 `screen.queryByText("运行 Pipeline") === null`；或 spec.md §非范围明示"前端 admin 隐藏不做单测覆盖"（accept 风险） |
| SHOULD FIX-3 | spec.md AC-3 "(a) usePipelineRun 状态机" | "mock fetch 返 queued → running → succeeded，轮询计数 ≥ 2"——**fetch spy 的实现细节**未在 spec / task 描述：用 `vi.fn().mockResolvedValueOnce(...).mockResolvedValueOnce(...).mockResolvedValueOnce(...)` 还是 `mockImplementation` 计数？fake timer 配 fetchJson 内部 `await fetch` 的 microtask 等问题（v5 react-query refetchInterval 内部用 setTimeout，fakeTimers 与 microtask 协同需 `await Promise.resolve()` flush） | T-5 description 加伪代码片段：示范 `vi.useFakeTimers()` + `vi.spyOn(global, 'fetch').mockResolvedValue(new Response(JSON.stringify(...)))` + `await vi.advanceTimersByTimeAsync(1100)` 模式；或参考 TanStack v5 官方 testing guide 的轮询测试 recipe。否则 coding 阶段会卡在 timer + microtask 顺序坑 |
| SHOULD FIX-4 | spec.md §背景 + 风险表 | 缺 demo recipe YAML 内容**与后端真实 `recipes/examples/demo-bronze-to-gold.yaml` 一致性**的校验。T-4 写"hardcoded demo recipe 字面（10-15 行）"——但 `recipes/examples/demo-bronze-to-gold.yaml` 实际 23 行（含 header 注释），且节点 id 为 `normalize` / `qa_gen`。spec 没列出**复制源**，coding 阶段可能写偏（漏 `config` / 错 `processor` 引用），AC-3 (d) "screen.getByText('normalize') + getByText('qa_gen')"测试通过不代表 demo recipe 真能后端 POST 成功 | T-4 description 加："hardcoded DEMO_RECIPE_YAML 字面**逐字复制** `recipes/examples/demo-bronze-to-gold.yaml` 内容（去 header 注释保留 name + nodes，约 14-18 行）"；加 AC-1c 或 AC-2 子项断言：`grep -q "name: demo-bronze-to-gold" apps/web/src/routes/repos/$owner.$name.tsx`、`grep -q "processor: markdown-normalize@0.1"`、`grep -q "processor: llm-qa-gen@0.1"` |
| SHOULD FIX-5 | spec.md AC-4 + T-7 self_check block | AC-4 写 `bash scripts/_self_check.sh pipeline-ui-tab`，预设 `_self_check.sh` 已含 `run_pipeline_ui_tab` block——但 T-7 才负责加入 block。**循环依赖**：AC-4 假设 T-7 已完成；T-7 又 depends_on T-4 / T-5。`scripts/_self_check.sh` 调度 `run_pipeline_ui_tab` 需要在 `main` 链或 `case` 分支注册（参考 L1503-1509 pattern）。spec 没明示注册位置 | T-7 description 增加："在 `_self_check.sh` `main()` 函数体（约 L1447 后）按 closed change 顺序插入 `run_pipeline_ui_tab`；且在 case 分支（约 L1503 后）增加 `pipeline-ui-tab\|pipeline-ui-tab-20260518) run_pipeline_ui_tab ;;`" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | spec.md §范围 AC-2 | "Run 状态面板"显示 `output_commit_hash`（截 12 字符）但没说**点击是否跳 commit 详情页**。`repos/$owner.$name.tsx` FilesSection 已有 `<Link to="/commits/$owner/$name/$hash" ...>` 模式可复用 | AC-2 子项加："output_commit_hash 非空时，渲染为 `<Link to=/commits/$owner/$name/$hash>` 跳转 commit 详情页"。或显式 follow-up `pipeline-ui-node-detail-*` |
| NICE-2 | spec.md §风险 #3 | "Pipeline 失败状态文案 / error 字符串过长截断" 影响 = "低" —— 但用户复盘 pipeline 失败时**期望看完整 error**，UX 角度可能影响"中"。`<pre>` + `max-h-32 overflow scroll` 是合理设计但用户体验可优化（如"展开/收起"按钮） | 可不改，follow-up `pipeline-ui-error-detail-*` |
| NICE-3 | spec.md §引用 | 缺 `apps/web/src/lib/api/client.ts`（fetchJson + UnauthorizedError + ApiError 实现）引用——T-2 / T-3 实现要复用 fetchJson 错误处理路径 | §引用加：`apps/web/src/lib/api/client.ts`（fetchJson / 401 处理路径） |

## Verdict

**REVISION REQUIRED**

理由：5 条 MUST FIX 未关闭：
1. AC-1 grep alternation 转义 bug（spec.md L65 `\|` 在 grep -E 是字面竖线，AC 假阴性）
2. TS interface 5 个 nullable 字段未明示 `\| null`（与后端 schema 不一致风险）
3. AC-4 缺 `tsc --noEmit` → 生产构建链不完整，nullable 漏标不会被拦
4. 测试 mock 策略矛盾（msw 未装 + 模式互斥未澄清）
5. tasks.md process_tasks `estimated_stage` 命名违反 SKILL §跨 AC 第 7 条 grep 公式

stage 2 AC kind 必查 3 项**全 PASS**（kind 列存在 + AC-3/AC-4 锚定 behavioral + 无 exempt 声明），AC 分层规约硬约束本身未违反——但其余跨 AC 一致性问题足以阻塞 stage 3。

## 复检指引（generator 修 v2 前自查）

修完 spec_v2.md / tasks_v2.md 后，**逐条**跑：

```bash
cd /data/home/zhhdzhang/nta/nta-lake

# MUST FIX-1：alternation 转义 dry-run
SPEC=.harness/changes/pipeline-ui-tab-20260518/request_analysis/spec.md
# 反向：spec 不应再含 `\|` 在 grep -E 上下文（除 markdown 表格分隔）
grep -nE 'grep[^|]*-q?[^|]*E[^|]*"[^"]*\\\|[^"]*"' "$SPEC"  # 期望 0 行
# 正向：把 AC-1 验证命令复制到 shell 真跑
test -f apps/web/src/lib/api/queries.ts || echo "[expected miss before T-1 implemented]"

# MUST FIX-2：nullable 矩阵
grep -cE "\\| null" "$SPEC"  # 期望 ≥ 5（5 个 nullable 字段都标注）

# MUST FIX-3：AC-4 含 tsc --noEmit
grep -qE "tsc --noEmit" "$SPEC" && echo "AC-4 has tsc check" || echo "MISSING tsc"

# MUST FIX-4：msw 字串清零
grep -nE "\bmsw\b" .harness/changes/pipeline-ui-tab-20260518/ -r  # 期望 0 命中

# MUST FIX-5：process_tasks 命名
TASKS=.harness/changes/pipeline-ui-tab-20260518/request_analysis/tasks.md
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" "$TASKS"  # 期望 ≥ 6

# AC kind 必查（v1 已 PASS，但 v2 不能回退）
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' "$SPEC" | grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|' && echo "kind col OK"
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' "$SPEC" | grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|' && echo "behavioral row OK"
```

全部期望命中后，把本 review 文件路径写入 `summary.md` 阶段 2 行 verdict 列 + 标记 stage 2 status=in_progress（v2 进行中），开 `spec_review_v2.md` 申请二次评审。
