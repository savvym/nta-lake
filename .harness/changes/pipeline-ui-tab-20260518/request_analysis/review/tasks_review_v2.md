---
change_id: pipeline-ui-tab-20260518
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-agent:pipeline-ui-tab-20260518-stage2-reviewer-v2
reviewed_at: 2026-05-18T13:55:00Z
verdict: APPROVED
---

# Tasks Review v2

> 评审者声明：同 spec_review_v2.md 独立 sub-agent v2；tasks 与 spec 一并评审。

## v1 MUST FIX-T 复检（5 条全 CLOSED）

| # | v1 MUST FIX-T | v2 状态 | 机械化证据 |
|---|---|---|---|
| T-1 | process_tasks `estimated_stage` 命名违 SKILL 跨 AC 第 7 条 grep 公式 | **CLOSED** | tasks L182-208 7 项 process_tasks 全用 `stage-2` / `stage-4` / `stage-6` / `stage-7` / `stage-8` / `stage-9` / `stage-10` 短格式。`grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md` = 6（超阈值 ≥6；含 stage-8 self-attest 计 7）。 |
| T-2 | T-1 字段表未标 nullable | **CLOSED** | T-1 description L15-42 逐字段列 TS 类型；5 个 nullable 字段显式 `\| null`：`output_commit_hash: string \| null`、`input_commits: string[] \| null`、`cache_key: string \| null`、节点 `error: string \| null`、`PipelineRunResponse.error: string \| null`。后端 `apps/api/dataplat_api/schemas/pipeline.py` L143-158 一字段对一字段。 |
| T-3 | T-5 mock 策略矛盾 + 必须拆 T-5a/T-5b | **CLOSED** | tasks 拆为 T-5a（L105-121，hook 测试，文件 `apps/web/src/lib/api/pipeline.test.tsx`，用 `vi.spyOn(global, 'fetch')` + `vi.useFakeTimers()` + `vi.advanceTimersByTimeAsync(1100)`）+ T-5b（L123-141，组件测试，文件 `apps/web/src/routes/repos.pipelines-section.test.tsx`，用 `vi.mock("../lib/api/queries", ...)` 同既有 repos.test.tsx 模式）。AC-3 期望（spec L81）+ T-6 命令（L147）+ T-7 self_check（L167）三处文件路径一致：`src/lib/api/pipeline.test.tsx` + `src/routes/repos.pipelines-section.test.tsx`。tasks L109 显式注 "（而非 msw，因为仓库未装 msw）"。 |
| T-4 | T-6 缺 `tsc --noEmit` | **CLOSED** | T-6 description L144-149 命令 `npm run build  # = vite build && tsc --noEmit -p tsconfig.json`；T-7 self_check AC-4 block L167 同步 "npm run build（含 tsc --noEmit）"。`apps/web/package.json` L7 `"build": "vite build && tsc --noEmit -p tsconfig.json"` 一致。`bash -n` syntax PASS。 |
| T-5 | T-7 缺 `_self_check.sh` 注册位置说明 | **CLOSED**（达成最低门槛） | T-7 description L160-169 含：(a) "在 main 调用链插入 run_pipeline_ui_tab（stage9-followup-cleanup 之后、harness-ac-behavioral-tier 之前）"明示**顺序锚点**；(b) "加 case 分支 pipeline-ui-tab \| pipeline-ui-tab-20260518"明示 case 模式。**未给具体行号锚点（L1447 / L1503）**，但 `_self_check.sh` 既有结构（`run_stage9_followup_cleanup` L1318 + `run_harness_ac_behavioral_tier` L1339）顺序锚点足够指导 coding 阶段生成位置。降级为 NICE-T-3。 |

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 tasks）

- [x] 每个任务粒度合理（1-3 小时）—— T-1 ~ T-7 单文件级；T-4 仍偏大（≥1.5h）但在上界内
- [x] depends_on 无环 —— DAG（L215-219）画出树状无环：`T-1 → {T-2, T-3} → T-4 → T-5b → T-6`，`T-5a` 接 T-3，`T-7` 接 T-4/T-5a/T-5b
- [x] 包含评审 / 单测 / CI 阶段对应任务 —— 7 项 P-* process_tasks 全 stage-N 短格式
- [x] 没有 "做完整个系统" 类目标任务 —— 全单文件 deliverable
- [x] 每条 AC 都有非 process_tasks 任务覆盖 —— 验收覆盖矩阵 L225-230 全填

## 任务粒度与 DAG 健全性

| Task | 估时 | depends_on | 备注 |
|---|---|---|---|
| T-1 | 30 min | [] | TS 类型 3 个 interface（含 nullable 矩阵）；OK |
| T-2 | 30 min | [T-1] | useCreatePipelineRun mutation；OK |
| T-3 | 45 min | [T-1] | usePipelineRun query 含 refetchInterval callback；OK |
| T-4 | 1.5-2 h | [T-2, T-3] | PipelinesSection 组件；上界内但偏大 |
| T-5a | 1-1.5 h | [T-3] | hook 测试（fetch spy + fake timer）；OK |
| T-5b | 1-1.5 h | [T-4] | 组件测试（vi.mock 模块）；OK |
| T-6 | 15 min | [T-5a, T-5b] | vitest + npm run build；OK |
| T-7 | 30 min | [T-4, T-5a, T-5b] | _self_check.sh 注册；OK |

DAG（tasks.md L215-219 自画）：
```
T-1 ──┬─→ T-2 ─┐
      └─→ T-3 ─┴─→ T-4 ──┬─→ T-5b ─┐
              └─────────────────────→ T-5a ──┴─→ T-6
                          └─→ T-7
```

✅ 无环。T-6 + T-7 是终点（真跑验证 + self_check 注册）。

## 验收覆盖矩阵复核

| AC | spec kind | tasks 覆盖 | 缺漏 |
|---|---|---|---|
| AC-1 | static | T-1, T-2, T-3, T-7 | ✓ |
| AC-2 | static | T-4, T-7 | ⚠️ 缺 admin only 测试覆盖（SHOULD-T-1）|
| AC-3 | behavioral | T-5a, T-5b, T-6, T-7 | ✓ |
| AC-4 | behavioral | T-6, T-7 | ✓ |

**behavioral AC ≥ 1**：AC-3 + AC-4，✅ 满足。

## 问题列表

### MUST FIX

（无）

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD-T-1 | tasks.md T-5b 或新 T-5c（admin only 测试覆盖）| spec §AC-2 仍写"admin only"，T-5b 4 个测试（c)(d) 未覆盖 isAdmin=false → button 不渲染场景。v1 review SHOULD FIX-2 已提出，v2 未补。**不阻塞**（前端隐藏只是 UX），但 follow-up 价值；或 spec §非范围显式 accept | T-5b 加测试 (e)：mock useMe 返 role=viewer → 断言 `screen.queryByText("运行 Pipeline") === null`；或 spec §非范围明示 "前端 admin 隐藏不做单测覆盖（accept；后端 require_admin 已守门）" |
| SHOULD-T-2 | tasks.md T-4 description（L83-103）| DEMO_RECIPE_YAML hardcoded "字面（10-15 行）"——`recipes/examples/demo-bronze-to-gold.yaml` 实际 23 行（含 header 注释）。v1 review SHOULD FIX-4 已提，v2 未明示复制源 | T-4 description 加："hardcoded DEMO_RECIPE_YAML **逐字复制** `recipes/examples/demo-bronze-to-gold.yaml`（去 header 注释保留 name + nodes 段，约 14-18 行）"；T-7 self_check AC-2 加 grep `"name: demo-bronze-to-gold"` + `"processor: markdown-normalize@0.1"` + `"processor: llm-qa-gen@0.1"` 三条 |
| SHOULD-T-3 | tasks.md process_tasks P-deploy notes（L204-206）| 写"必须真跑 deploy_verify（本机起 web dev + npm run build）"——"web dev"（`vite` 端口 5174）+ `npm run build` 两者只跑一即可还是必跑？v1 review SHOULD-T-3 提出，v2 未澄清。production-only bug（minify / dead code elim）只有 `npm run preview`（端口 4173）能暴露 | P-deploy notes 改为："必须 `npm run build && npx vite preview --port 4173` 起生产构建预览验证；vite dev mode 不等价部署验证（HMR / source map / production minify 差异）" |
| SHOULD-T-4 | tasks.md frontmatter L1-7 | tasks.md frontmatter 没 `status` 字段；spec.md frontmatter L7 有 `status: draft`。schema 应一致 | tasks.md frontmatter 加 `status: draft`（L4 之后） |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-T-1 | tasks.md T-7 description（L158-174）| T-7 描述用顺序锚点 "stage9-followup-cleanup 之后、harness-ac-behavioral-tier 之前"，未给具体行号 L1318/L1339；coding 阶段 generator 仍需 grep 既有结构定位 | T-7 加注："`_self_check.sh` 当前 `run_stage9_followup_cleanup()` 在 L1318 附近，`run_harness_ac_behavioral_tier()` 在 L1339 附近——本 change 插入位置 = 两者之间或 `run_harness_ac_behavioral_tier` 之后（建议后者，保持已 closed 顺序）" |
| NICE-T-2 | tasks.md T-3 description（L62-79）| refetchInterval callback `query.state.data?.status` 字面写在 description 里，coding 时易复制错；v1 review NICE-T-1 提出，v2 未补 | T-3 加引用："参考 `apps/web/src/lib/api/queries.ts` L166-172 `useJob` 同模式实现" |
| NICE-T-3 | tasks.md T-5a/T-5b description | 4 个子测试用编号 (a)(b)(c)(d) + spec AC-3 期望含中文测试名 "usePipelineRun 状态机 / useCreatePipelineRun 成功 / PipelinesSection 渲染 / 节点表渲染"——若 coding 阶段 it 名写英文（更符合既有 jobs.$job_id.test.tsx 模式），AC-3 期望 cell 就 mismatch | T-5a/T-5b 加推荐 it 名："`it('usePipelineRun polls until succeeded')`、`it('useCreatePipelineRun posts text/yaml body')`、`it('PipelinesSection disables button when yaml empty')`、`it('PipelinesSection renders node table with cache_hit and output_commit_hash')`"；或 spec AC-3 期望 cell 改成 "≥4 测试 PASS，it 名不约束" |

## Verdict

**APPROVED**

理由：
- v1 5 MUST FIX-T 全 CLOSED
- 跨 AC 9 条全 PASS
- DAG 无环；7 任务粒度合理（T-4 偏大但在上界）；AC 覆盖矩阵完整；behavioral AC ≥ 1 满足
- T-5 mock 策略矛盾问题主体闭环（拆 T-5a/T-5b 文件 + 注释 "而非 msw"）
- T-6 含 `tsc --noEmit`；T-7 self_check 注册位置达最低门槛

4 条 SHOULD-T + 3 条 NICE-T 全为优化项，不阻塞 stage 3。

## 后续指引

APPROVED → 进入 stage 3（coding）。Application Owner 推荐：

1. 更新 summary.md 阶段 2 row verdict=APPROVED；阶段 status=completed；报告路径列加 v2
2. （可选）SHOULD-T-1 ~ T-4 + NICE-T-1 ~ T-3 顺手补在 v3 或 stage 3 启动前
3. 启动 stage 3 generator（独立 sub-agent）按 T-1 → T-2/T-3 → T-4 → T-5a/T-5b → T-6/T-7 执行

复检指引（若想补 v3）：

```bash
cd /data/home/zhhdzhang/nta/nta-lake
TASKS=.harness/changes/pipeline-ui-tab-20260518/request_analysis/tasks.md

# v3 前自查
grep -qE "^status:" "$TASKS" && echo "frontmatter status OK"   # SHOULD-T-4
grep -qE "demo-bronze-to-gold\.yaml" "$TASKS" && echo "demo source ref OK"  # SHOULD-T-2
grep -qE "npm run preview|--port 4173" "$TASKS" && echo "preview note OK"   # SHOULD-T-3
grep -qE "L1318|L1339|run_harness_ac_behavioral_tier" "$TASKS" && echo "T-7 line anchor OK"  # NICE-T-1
```
