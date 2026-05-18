---
change_id: pipeline-ui-tab-20260518
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:pipeline-ui-tab-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T13:05:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

> 评审者声明：与 `spec_review_v1.md` 同一独立 sub-agent；tasks 评审与 spec 评审一并进行，共享 MUST FIX 编号（前缀 `MUST FIX-T-*` 表示 tasks 文件本身的问题；与 spec_review 的 MUST FIX-1~5 互相引用）。

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 tasks）

- [x] 每个任务粒度合理（1-3 小时）—— T-1~T-7 都是单文件级别改动，符合
- [x] depends_on 无环 —— DAG 段（L173-176）画出树状无环
- [x] 包含评审 / 单测 / CI 阶段对应任务（process_tasks 完整）—— 列了 6 项 P-* —— **但 estimated_stage 命名违反 SKILL §跨 AC 第 7 条 grep 公式**（见 MUST FIX-T-1）
- [x] 没有 "做完整个系统" 类目标任务 —— T-1 到 T-7 每个都有具体 deliverable
- [x] 每条 AC 都有非 process_tasks 任务覆盖 —— 验收覆盖矩阵 L182-187 全填

## 任务粒度与 DAG 健全性

| Task | 描述 | 估时合理性 | depends_on | 备注 |
|---|---|---|---|---|
| T-1 | TS 类型 3 个 interface | 30 min | [] | OK，纯 type 定义 |
| T-2 | useCreatePipelineRun mutation | 30 min | [T-1] | OK，参考 useUploadBlob |
| T-3 | usePipelineRun query 含 refetchInterval callback | 45 min | [T-1] | OK |
| T-4 | PipelinesSection 组件 | 1.5-2 h | [T-2, T-3] | **粒度偏大**：含 yamlText state + activeRunId state + 两个按钮 + Run 状态面板 + 节点表 + admin 门 + hardcoded demo recipe ~14 行字面。可拆 T-4a (state + 按钮) / T-4b (Run 状态面板)，但不强求 |
| T-5 | 新建 repos.pipelines-section.test.tsx ≥ 4 测试 | 2-3 h | [T-4] | **粒度偏大且 mock 策略矛盾**（见 spec_review MUST FIX-4） |
| T-6 | 跑 vitest + vite build | 15 min | [T-5] | **缺 tsc --noEmit**（见 spec_review MUST FIX-3） |
| T-7 | _self_check.sh 注册 run_pipeline_ui_tab | 30 min | [T-4, T-5] | **缺注册位置说明**（见 spec_review SHOULD FIX-5） |

DAG：

```
T-1 ──┬─→ T-2 ─┐
      └─→ T-3 ─┴─→ T-4 ──┬─→ T-5 ─→ T-6
                          └─→ T-7
```

✅ 无环。T-6 + T-7 是终点，与 spec AC-3 / AC-4 真跑验证一致。

## 验收覆盖矩阵复核

| AC | spec kind | tasks 覆盖关联 | 缺漏 |
|---|---|---|---|
| AC-1 | static | T-1, T-2, T-3, T-7 | ✓ |
| AC-2 | static | T-4, T-7 | ⚠️ 缺 admin only 测试覆盖（见 spec_review SHOULD FIX-2） |
| AC-3 | behavioral | T-5, T-6, T-7 | ✓ |
| AC-4 | behavioral | T-6, T-7 | ⚠️ 缺 tsc --noEmit（见 spec_review MUST FIX-3） |

**behavioral AC ≥ 1**：AC-3 + AC-4，✅ 满足。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-T-1 | tasks.md `process_tasks` 段（L142-168）| 6 个 P-* 项的 `estimated_stage` 值为长名（`request_analysis_review` / `coding_review` / `unit_test_review` / `ci_result` / `deployment` / `user_confirmation`），不符合 `.harness/skills/request-analysis/SKILL.md` § "跨 AC 一致性自审 9 条" 第 7 条要求的 `stage-2` / `stage-4` / `stage-6` / `stage-7` / `stage-9` / `stage-10` 形态。自查公式 `grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md` **当前 = 0**（应 ≥ 6）。**实证**：参考已 closed change `pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md` 的 process_tasks 命名 | 改 6 项 `estimated_stage`：`stage-2` / `stage-4` / `stage-6` / `stage-7` / `stage-9` / `stage-10`。或在 `.harness/skills/request-analysis/SKILL.md` 跨 AC 第 7 条把 grep 公式同步改为接受两种命名（不在本 change 范围；推荐前者快修）|
| MUST FIX-T-2 | tasks.md T-1 description（L15-22）| 字段表只列字段名，**未明示 nullable**——与 spec MUST FIX-2 同源。后端 `pipeline.py` `output_commit_hash: str \| None = None` 等 5 个字段是 nullable，T-1 description 没列出 → coding 阶段 generator 易写成 non-null TS interface | T-1 description 重写字段表：每个字段附 TS 类型；nullable 字段标 `\| null`：`output_commit_hash: string \| null`；`input_commits: string[] \| null`；`cache_key: string \| null`；`error: string \| null`（PipelineNodeRunResponse 与 PipelineRunResponse 各一）|
| MUST FIX-T-3 | tasks.md T-5 description（L84-105）| (1) "msw / vi.spyOn(global, 'fetch') 路径" 与仓库现状不符：msw 未安装，6 个现存测试统一用 `vi.mock("../lib/api/queries", ...)`；(2) 4 个子测试 (a)(b)(c)(d) 用什么 mock 策略未澄清——其中 (a)(b) 测 hook 内部行为必须用 fetch spy，(c)(d) 测组件渲染必须 mock hook 模块层，两者**不能在同一 test 文件混用**（vi.mock 模块级 hoist 会污染全 file）| 拆 T-5 为：T-5a 测试 hook 状态机（用 `renderHook` + `vi.spyOn(global, 'fetch')` + `vi.useFakeTimers()` + `await vi.advanceTimersByTimeAsync(1100)`；新建文件 `apps/web/src/lib/api/queries.pipeline.test.tsx`）+ T-5b 测试组件渲染（沿用 `vi.mock("../lib/api/queries", ...)` 模式；新建 `apps/web/src/routes/repos.pipelines-section.test.tsx`）。AC-3 期望调整为"≥ 2 测试文件、共 ≥ 4 测试 PASS"|
| MUST FIX-T-4 | tasks.md T-6 description（L107-119）| 命令缺 `npx tsc --noEmit -p tsconfig.json`。spec MUST FIX-3 同源——`apps/web/package.json` L7 `"build": "vite build && tsc --noEmit"` 才是真生产构建链；vite build 单跑不拦类型错（nullable / undefined）| T-6 command 改：`cd apps/web && npx vitest run src/routes/repos.pipelines-section.test.tsx src/lib/api/queries.pipeline.test.tsx && npx vite build && npx tsc --noEmit -p tsconfig.json`，或直接 `npm run build && npm test`。期望：所有命令退码 0；vite 输出 `built in`；tsc 无输出（success） |
| MUST FIX-T-5 | tasks.md T-7 description（L121-136）| 缺 `_self_check.sh` 注册位置说明（与 spec SHOULD FIX-5 同源 → 本处升级为 MUST FIX 因为 T-7 是实际改动 task）。当前描述说 "在 main 调用链插入 run_pipeline_ui_tab"，但**位置**（顺序）会影响 `_self_check.sh full` 模式的输出顺序与跳过逻辑 | T-7 description 增加：(a) 在 `main()` 函数体（约 L1447 后，紧跟 `run_stage9_followup_cleanup`）插入 `run_pipeline_ui_tab`；(b) 在 case 分支段（约 L1503-1509 pattern）增加 `pipeline-ui-tab\|pipeline-ui-tab-20260518) run_pipeline_ui_tab ;;`；(c) `run_pipeline_ui_tab` 函数体写在文件末尾 hold `run_stage9_followup_cleanup` 之后 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-T-1 | tasks.md T-4 description（L60-82）| 粒度偏大（≥ 1.5 h），含 6 大子任务（state + 按钮 + Run 面板 + 节点表 + admin 门 + DEMO_RECIPE_YAML 字面）。SKILL §1 plan 模式 tasks checklist "每个任务粒度合理（1-3 小时）"——略超上界 | 可不拆（仍在 3h 内）；但建议把 DEMO_RECIPE_YAML 抽到独立常量文件 `apps/web/src/lib/recipes/demoRecipe.ts`，方便后续 follow-up `pipeline-ui-recipe-list-*` 复用，且 spec 引用更稳定 |
| SHOULD FIX-T-2 | tasks.md T-7 (`run_pipeline_ui_tab` 内 AC-1 静态检查)（L128-129）| 描述 "grep queries.ts 2 个 hook + 3 个 interface"——3 个 interface 名未列；与 spec_review MUST FIX-1 alternation 转义 bug 同源。如 generator 抄 spec AC-1 命令到 _self_check.sh 时，`\|` 直接 sourced 进 bash → grep -E 字面竖线，假阴性 | T-7 description 加注："**复制 spec AC-1 命令时去掉反斜杠**（写成 `grep -qE 'A\|B\|C'` 而非 `'A\\|B\\|C'`）；或拆三条 `grep -q "interface A" && grep -q "interface B" && grep -q "interface C"` 更稳" |
| SHOULD FIX-T-3 | tasks.md `process_tasks` P-deploy notes | 写 "有部署面（apps/web 改动），必须真跑 deploy_verify（本机起 web dev + vite build）"——MVP 用 dev mode（`vite` port 5174）是否真等价于"部署验证"？vite dev 与 vite build 产出（dist/）行为可能差异（HMR / source map / production minify） | P-deploy notes 加："deploy_verify 必须用 `npx vite build && npx vite preview` 起生产构建预览（端口 4173），而非 `vite` dev 模式——否则 nullable 漏标等 production-only bug 不会暴露" |
| SHOULD FIX-T-4 | tasks.md 无 frontmatter status 字段 | tasks.md L1-5 frontmatter 没 status 字段；spec.md frontmatter 有 `status: draft`。tasks.md 与 spec.md 应一致 frontmatter schema 便于工具读 | 加 `status: draft` 行到 tasks.md L4 之后 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-T-1 | tasks.md T-3 description | refetchInterval callback 内 `query.state.data?.status` 字面写在 description 里，coding 时容易复制错（v5 API 的 `query` 参数类型是 `Query<...>`，`state` 属性确实有 `data` field）。建议加注 "参考 `apps/web/src/lib/api/queries.ts` L166-172 `useJob` 同模式实现" | T-3 加引用注释 |
| NICE-T-2 | tasks.md T-5 description | 4 个测试名只用编号 (a)(b)(c)(d)，建议显式英文 describe 块名（参考 jobs.$job_id.test.tsx 的 `describe("/jobs/$job_id", ...) it("queued status shows polling hint", ...)`） | T-5 加 `it("usePipelineRun polls until succeeded", ...)`、`it("useCreatePipelineRun posts text/yaml body", ...)` 等推荐名 |

## Verdict

**REVISION REQUIRED**

理由：5 条 MUST FIX-T-*（与 spec_review 5 条 MUST FIX 互锁，部分同源）：
- MUST FIX-T-1：process_tasks estimated_stage 命名违反 SKILL §跨 AC 第 7 条 grep 公式
- MUST FIX-T-2：T-1 字段表未标 nullable（与 spec_review MUST FIX-2 同源）
- MUST FIX-T-3：T-5 mock 策略与仓库现状矛盾（与 spec_review MUST FIX-4 同源），必须拆 T-5a/T-5b
- MUST FIX-T-4：T-6 缺 tsc --noEmit（与 spec_review MUST FIX-3 同源）
- MUST FIX-T-5：T-7 缺 _self_check.sh 注册位置（spec SHOULD FIX-5 在 tasks 侧升级为 MUST FIX）

## 复检指引（generator 修 v2 前自查）

```bash
TASKS=.harness/changes/pipeline-ui-tab-20260518/request_analysis/tasks.md

# MUST FIX-T-1
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" "$TASKS"  # 期望 ≥ 6

# MUST FIX-T-2
grep -cE "\\| null" "$TASKS"  # 期望 ≥ 5

# MUST FIX-T-3
grep -nE "\bmsw\b" "$TASKS"  # 期望 0 命中
grep -cE "queries\.pipeline\.test\.tsx|repos\.pipelines-section\.test\.tsx" "$TASKS"  # 期望 ≥ 2

# MUST FIX-T-4
grep -qE "tsc --noEmit" "$TASKS" && echo OK || echo MISSING

# MUST FIX-T-5
grep -qE "case.*pipeline-ui-tab\\|pipeline-ui-tab-20260518" "$TASKS" && echo OK || echo MISSING-case
grep -qE "main.*run_pipeline_ui_tab|L1447" "$TASKS" && echo OK || echo MISSING-main-pos

# DAG 无环（保留）
echo "T-1→T-2→T-4→T-5→T-6; T-3→T-4; T-7 from T-4/T-5" | grep -q "无环" || echo OK
```

全 PASS 后开 `tasks_review_v2.md` 申请二次评审；同步 `summary.md` 阶段 2 行的 v1 → v2、verdict 列、报告路径。
