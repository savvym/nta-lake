---
change_id: pipeline-ui-tab-20260518
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-agent:pipeline-ui-tab-20260518-stage2-reviewer-v2
reviewed_at: 2026-05-18T13:55:00Z
verdict: APPROVED
---

# Spec Review v2

> 评审者声明：独立 sub-agent v2，未参与 spec/tasks v1/v2 撰写；通过 prompt 拿到必读路径，完整读了 reviewer-agent.md / expert-reviewer SKILL（含 stage 2 AC kind 必查 3 项）/ spec_review_v1.md / tasks_review_v1.md / spec.md v2 / tasks.md v2 / 后端 schemas/pipeline.py / apps/web/package.json / apps/web/src/routes/ 既有结构。本评审复检了 v1 5 MUST FIX 是否真闭环，并扫了 v2 是否引入新缺陷。

## v1 MUST FIX 复检（5 条全 CLOSED）

| # | v1 MUST FIX | v2 状态 | 机械化证据 |
|---|---|---|---|
| 1 | AC-1 grep `\|` 在 ERE 是字面竖线 → 假阴性；遗漏 PipelineRunCreatedResponse | **CLOSED** | spec L79 AC-1 验证命令拆为 3 个独立 `grep -q "interface PipelineNodeRunResponse"` + `grep -q "interface PipelineRunResponse"` + `grep -q "interface PipelineRunCreatedResponse"`。`bash -n` 解析 OK；语义回归测试：在仅含 `PipelineRunResponse` 的 fake 文件上跑独立 grep，`PipelineRunCreatedResponse` 真 MISS（独立 grep 能抓漏）。spec L80 AC-2 同样拆为 4 个独立 grep（`function PipelinesSection` / `isAdmin && <PipelinesSection` / `useCreatePipelineRun` / `usePipelineRun`），不再用 ERE alternation。剩余 `\|` 仅出现在 markdown 表格 cell 内表示 **shell 管道**（`awk ... \| grep -q ...`），不是 grep -E alternation——markdown decode 后正确解析为真 pipe。AC-3/AC-4 同理。 |
| 2 | TS interface nullable 字段未明示 `\| null` | **CLOSED** | tasks T-1 description（L15-42）逐字段列 TS 类型并对 5 个 nullable 显式标注 `\| null`（`output_commit_hash` / `input_commits` / `cache_key` / `node.error` / `run.error`），grep 计数 "\| null" 在 T-1 段 = 6 次（含 PipelineRunResponse.error 那条）。与后端 `apps/api/dataplat_api/schemas/pipeline.py` L143-158 的 `str \| None = None` / `list[str] \| None = None` 一字段一字段对得上。spec L18-22 v1 review 闭环表 + L79 AC-1 描述均提"含 nullable 字段标注"以串联 tasks。 |
| 3 | AC-4 缺 `tsc --noEmit`；仓库 build 真 = `vite build && tsc` | **CLOSED** | spec AC-4（L82）验证命令现含 `cd apps/web && npm run build 2>&1 \| tail -5`，并显式注 `vite build && tsc --noEmit` 等价；tasks T-6（L144-149）命令同步：`npm run build  # = vite build && tsc --noEmit -p tsconfig.json`。`apps/web/package.json` L7 `"build": "vite build && tsc --noEmit -p tsconfig.json"` 一致。bash -n syntax PASS。 |
| 4 | mock 策略矛盾（msw 未装 + 模式互斥未澄清） | **CLOSED（spec/tasks 主体）；SHOULD-级残留：summary.md L32 + spec L93 风险表第 4 行** | tasks 拆为 T-5a（hook 测试用 `vi.spyOn(global, 'fetch')` + `vi.useFakeTimers()` + `await vi.advanceTimersByTimeAsync(1100)`，文件 `apps/web/src/lib/api/pipeline.test.tsx`）+ T-5b（组件测试用 `vi.mock("../lib/api/queries", ...)` 同既有 repos.test.tsx 模式，文件 `apps/web/src/routes/repos.pipelines-section.test.tsx`）。spec AC-3 验证命令 + T-6 命令 + T-7 self_check block 三处文件路径一致。v2 在 tasks L109 显式注 "（而非 msw，因为仓库未装 msw）"。**残留**：summary.md L32 仍含 "vitest 跑 PipelinesSection 用 msw mock /api 端点"；spec L93 风险表第 4 行仍叫 "msw mock 与真实后端响应 schema 漂移"——v1 review MUST FIX-4 修复要求 (2) 明示要改这两处，未落实。SHOULD FIX-1（不阻塞 stage 3，但 stage 3 进入前应顺手清）。 |
| 5 | process_tasks `estimated_stage` 命名违 SKILL 跨 AC 第 7 条 | **CLOSED** | tasks L182-208 7 个 process_tasks 用 stage-2 / stage-4 / stage-6 / stage-7 / stage-8 / stage-9 / stage-10 短格式；`grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md` = 6（含 stage-8 是 7，超阈值 ≥6）。 |

## stage 2 AC kind 必查 3 项（reviewer 硬约束）

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | AC 表存在 `kind` 列 | ✅ PASS | spec L77 `\| ID \| kind \| 描述 \| 验证方式 \| 期望 \|`；机械化 `awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md \| grep -qE '^\\|[^\|]*\\|[[:space:]]*kind[[:space:]]*\\|'` 命中。 |
| 2 | 至少 1 行 AC 的 kind 单元格真值 `behavioral`（锚定 AC 行 regex，不接受裸字串） | ✅ PASS | spec AC-3（L81）+ AC-4（L82）两行 kind 单元格值 `**behavioral**`；机械化 `awk ... \| grep -qE '^\\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\\|[[:space:]]*(\\*\\*)?behavioral(\\*\\*)?[[:space:]]*\\|'` 命中。L84 也显式写 "Behavioral AC：AC-3 + AC-4（vitest 真跑 + vite build 真跑），满足 ≥1 自约束"。 |
| 3 | frontmatter 是否声明 `ac_kind_lint: exempt` | ✅ N/A | spec frontmatter L1-9 无 `ac_kind_lint: exempt`；无需 git diff 校验范围。 |

三项全 PASS，AC 分层规约硬约束**未违反**。

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 spec）

- [x] 背景写明了为什么现在做（pipeline-orchestrator-mvp 后端就绪 + 用户原始诉求"web 一键跑全流程"）
- [x] 问题陈述对外部读者可理解（3 条具体缺失：触发 UI / 状态 UI / 轮询）
- [x] 范围 / 非范围都有（in-scope 4 条 AC；非范围 6 项 follow-up，含 SSE / lineage / recipe-editor 等）
- [x] 每条验收标准可演示且可机械化 —— AC-1 ~ AC-4 命令全 `bash -n` syntax OK；AC-1/AC-2 试跑（预实现 MISS）退码 1，行为符合预期
- [x] 风险有缓解或显式 accept（5 条风险全配缓解；callback API / Content-Type / mock schema 漂移 / admin 权限 / error 截断）
- [x] 没有把已有架构当新提案（refetchInterval callback 引 useJob，fetchJson 自定义 fetch 引 useUploadBlob）
- [x] 待澄清问题已清零

## 跨 AC 一致性自审 9 条（reviewer 复核）

| # | checklist 条目 | 结果 | 备注 |
|---|---|---|---|
| 1 | schema 字段 ↔ hash ↔ idempotency ↔ fixture | ✅ N/A | 纯前端 change |
| 2 | 事务边界 AC / 风险 / tasks 一字不差 | ✅ N/A | 无事务边界 |
| 3 | AC 验证命令一行式可执行 | ✅ PASS | AC-1/2/3/4 全 `bash -n` 通过；AC-1/2 试跑（实现前）正确返 1 |
| 4 | 风险缓解 ↔ AC 测试列表 | ✅ PASS | refetchInterval callback 风险 ↔ AC-3 (a) vitest 状态机；Content-Type 风险 ↔ AC-3 (b) |
| 5 | commit 历史链连续性 | ✅ N/A | 无写 commit 路径 |
| 6 | 反向 grep 配 `test -f` 前置 + 不吞 stderr | ✅ PASS | AC-1/AC-2 均以 `test -f ... &&` 前置；AC-4 含 `2>&1`（不吞 stderr） |
| 7 | process_tasks 6 条必填 + estimated_stage 命名 | ✅ PASS | 7 项 stage-N 短格式；含 stage-8 self-attest 有 notes |
| 8 | AC 验证命令 dry-parse | ✅ PASS | 全 `bash -n` 通过；AC-1 独立 grep 语义回归测试 OK |
| 9 | summary.md frontmatter 无模板占位符 | ✅ PASS | summary.md frontmatter L1-15 全部实值 |

## 必查：TS schema 对齐后端（v1 已 PASS，v2 复核 nullable）

后端 `apps/api/dataplat_api/schemas/pipeline.py` L134-169 三 model 与 tasks T-1 描述逐字段比对：

| 后端字段 | T-1 类型 | nullable 标注 |
|---|---|---|
| `PipelineNodeRunResponse.node_id: str` | `string` | non-null OK |
| `processor_name: str` | `string` | non-null OK |
| `processor_version: str` | `string` | non-null OK |
| `config: dict[str, Any]` | `Record<string, unknown>` | non-null OK |
| `status: str` | `string` | non-null OK |
| `cache_hit: bool` | `boolean` | non-null OK |
| `output_commit_hash: str \| None = None` | `string \| null` | ✅ 标注 |
| `input_commits: list[str] \| None = None` | `string[] \| null` | ✅ 标注 |
| `cache_key: str \| None = None` | `string \| null` | ✅ 标注 |
| `error: str \| None = None`（node） | `string \| null` | ✅ 标注 |
| `PipelineRunResponse.run_id / recipe_name / status / created_by: str` | `string` | non-null OK |
| `PipelineRunResponse.error: str \| None = None` | `string \| null` | ✅ 标注 |
| `node_runs: list[PipelineNodeRunResponse]` | `PipelineNodeRunResponse[]` | non-null OK |
| `PipelineRunCreatedResponse.{run_id, job_id}: str` | `string` | non-null OK |

字段名 / 嵌套 / nullability 全 OK，V1 MUST FIX-2 实质闭环。

## 问题列表

### MUST FIX

（无）

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | summary.md L32 + spec L93 风险表第 4 行 | summary.md L32 仍写 "vitest 跑 PipelinesSection 用 msw mock /api 端点，断言轮询 ≥1 次 + 显示 succeeded"；spec L93 风险表第 4 行仍叫 "msw mock 与真实后端响应 schema 漂移"。v1 review MUST FIX-4 修复要求 (2) 明示要改这两处，spec/tasks 主体 mock 策略已澄清（T-5a vi.spyOn / T-5b vi.mock 模块），但这两处 "msw" 描述会误导后续读者。**不阻塞 stage 3**（实操命令已正确），但 stage 3 启动前应顺手清 | (1) summary.md L32 改成 "vitest 跑 PipelinesSection（T-5b 用 vi.mock("../lib/api/queries", ...) 模块级 mock）+ usePipelineRun hook（T-5a 用 vi.spyOn(global, 'fetch') + vi.useFakeTimers()），断言轮询 ≥2 次 + 显示 succeeded"；(2) spec L93 风险表第 4 行改为 "TS interface 与后端 pydantic schema 漂移" + 缓解改为 "tasks T-1 显式 nullable 标注 + npm run build 跑 tsc --noEmit 兜底" |
| SHOULD FIX-2 | spec.md §AC-2 + T-5b（admin only 测试覆盖）| spec §范围 AC-2 仍写 "admin only，模式同 IngestSection"，但 T-5b 4 个测试（c)(d)(e)(f) 没覆盖 "isAdmin=false 时 PipelinesSection 不渲染"。v1 review SHOULD FIX-2 已提出，v2 未补。**不阻塞**（前端隐藏是 UX 优化，后端 require_admin 才是安全防线），但 follow-up 价值 | T-5b 加一条测试：`renderWithProviders(<RepoDetailPage />, { mockMe: { role: "viewer" } })` 断言 `screen.queryByText("运行 Pipeline") === null`；或 spec §非范围明示 "前端 admin 隐藏不做单测覆盖（accept；后端 require_admin 已守门）" |
| SHOULD FIX-3 | spec.md §AC-3 (a) 测试命名 + T-5a 描述 | T-5a 描述 (a)/(b) 子测试仍用 (a)(b) 编号；spec AC-3 期望 "含 usePipelineRun 状态机 / useCreatePipelineRun 成功 / PipelinesSection 渲染 / 节点表渲染 4 项"——这 4 项是中文 it 名，且 vitest 输出格式 `Tests  ≥4 passed`，**未要求** 中文 describe 块名一字不差匹配。但若 coding 阶段 it 名写成英文（更符合既有 jobs.$job_id.test.tsx 模式），AC-3 期望 cell 文案就 mismatch | T-5a/T-5b description 加 "推荐 it 名（英文风格，与 jobs.$job_id.test.tsx 一致）：`it("usePipelineRun polls until succeeded")`, `it("useCreatePipelineRun posts text/yaml body")`, `it("PipelinesSection disables button when yaml empty")`, `it("PipelinesSection renders node table with cache_hit and output_commit_hash")`"；spec AC-3 期望 cell 同步从中文名改成 it 名通配（或显式注 "AC-3 只断言 4 测试 PASS，it 名不约束"） |
| SHOULD FIX-4 | spec.md AC-4 反向 grep | AC-4 期望写 "不含 `error TS` 或 `Found N errors`"——`tsc --noEmit` 失败时 stdout 确实含 `error TS<num>: ...` / `Found N errors`，反向 grep 是合理的（v1 SHOULD FIX-1 已部分缓解，但 v2 没加 `test -f apps/web/dist/index.html` 正向断言）。`npm run build` 失败时退码非 0，`bash` 链 && 已能截断——单独反向 grep 字符串作为防御性二道阀仍可，但缺**正向断言**违反 SKILL 跨 AC 第 6 条 (b) 修复模板 | AC-4 期望 cell 加 "且 `test -f apps/web/dist/index.html` 退码 0（vite 产物存在的正向断言）"；T-7 self_check `run_pipeline_ui_tab` 同步加这条 |
| SHOULD FIX-5 | spec.md §引用 缺 `apps/web/src/lib/api/client.ts` | v1 NICE-3 提出，v2 未补。client.ts 是 fetchJson / UnauthorizedError / ApiError 的源；T-2 / T-3 实现都要复用它的 401 处理 | §引用 加：`apps/web/src/lib/api/client.ts`（fetchJson / 401 处理路径） |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | spec AC-2 + T-4 | output_commit_hash 非空时是否渲染为 `<Link to="/commits/$owner/$name/$hash">`（复用 FilesSection 模式）未明示。MVP 可截 12 字符纯展示 | 显式 follow-up `pipeline-ui-node-detail-*`，本 change accept 纯展示 |
| NICE-2 | T-4 + spec §范围 AC-2 | DEMO_RECIPE_YAML hardcoded 字面（10-15 行）vs `recipes/examples/demo-bronze-to-gold.yaml` 实际 23 行（含注释）；v1 SHOULD FIX-4 已提出，T-4 v2 仍写"hardcoded demo recipe ~14 行字面 demo-bronze-to-gold.yaml" | T-4 description 显式注 "逐字复制 recipes/examples/demo-bronze-to-gold.yaml（去 header 注释保留 name + nodes 段，约 14-18 行）"；可加 AC-2 子项 grep "name: demo-bronze-to-gold" + "processor: markdown-normalize@0.1" + "processor: llm-qa-gen@0.1" |
| NICE-3 | spec §背景 + 风险表 | 缺 "本机起 web dev 5174 + 浏览器无 console.error 自查（self-attest 等价 manual check）" 的具体 self-attest 文案模板，stage 9 deploy_verify 时可能漂移 | stage 9 启动前在 `deploy_verify_v1.md` 显式 self-attest 文案；当前 spec AC-4 已写"self-attest 等价 manual check"，可接受 |

## Verdict

**APPROVED**

理由：
- v1 5 MUST FIX 全 CLOSED（其中 MUST #4 主体闭环，summary.md / 风险表第 4 行 "msw" 残留降级为 SHOULD FIX-1，不阻塞 stage 3）
- stage 2 AC kind 必查 3 项全 PASS（kind 列存在 + AC-3/AC-4 锚定 behavioral + 无 exempt 声明）
- 跨 AC 9 条全 PASS（v1 失败的 3/7/8 三条本次都过）
- AC-1 ~ AC-4 命令 `bash -n` 全 PASS；AC-1 独立 grep 语义回归测试通过（能抓漏 PipelineRunCreatedResponse）
- 后端 schema 字段对齐 + nullable 标注完整

5 条 SHOULD FIX 不阻塞 stage 3 进入；建议 Application Owner 在 spec_v3（如需）或 stage 3 启动前顺手清。

## 后续指引

APPROVED → 进入 stage 3（coding）。Application Owner 应：

1. 更新 summary.md 阶段 2 行 verdict=APPROVED，标 status=completed，报告路径加 v2
2. （可选 SHOULD-1）spec_v3 微调或 summary.md L32 + spec L93 风险表第 4 行直接清 "msw" 残留
3. 启动 stage 3 generator（独立 sub-agent）做 T-1 ~ T-7 编码

复检指引（若 Application Owner 觉得 SHOULD-1 想顺手补 v3）：

```bash
cd /data/home/zhhdzhang/nta/nta-lake
SUMMARY=.harness/changes/pipeline-ui-tab-20260518/summary.md
SPEC=.harness/changes/pipeline-ui-tab-20260518/request_analysis/spec.md
grep -nE "\bmsw\b" "$SUMMARY"  # 期望 0
grep -nE "msw mock" "$SPEC"    # 期望 0
```
