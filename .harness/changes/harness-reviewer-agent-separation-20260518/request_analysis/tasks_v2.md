---
change_id: harness-reviewer-agent-separation-20260518
version: 2
authored_at: 2026-05-18T13:15:00Z
note: v2 修 tasks_review_v1.md 列出的 2 条 MUST FIX + 6 条 SHOULD FIX；v1 保留作历史
---

# Tasks v2

## v2 改动摘要

| MUST FIX | v1 问题 | v2 修复 |
|---|---|---|
| #1 T-11 vs spec AC-12 数字打架 | T-11 +1=226+，spec AC-12 +13=238 | 统一为 **+1**（reviewer-lint 1 个 global AC）；T-11 显式写 `期望 PASS = baseline + 1 = 225 + 1 = 226`，AC-12 spec_v2 同步 |
| #2 DAG ↔ depends_on 矛盾 | ASCII DAG 与文字 depends_on 不一致 | 删 ASCII DAG，只留文字 depends_on |
| SHOULD FIX #1 T-7/8/9 stage 与 task 混淆 | dogfood spawn 是流程动作不是实现任务 | T-7/8/9 移到 §process_tasks（与 T-12/13/14 并列）；标 `process action` |
| SHOULD FIX #3 T-6 漏 template 占位符回溯 | T-6 只写改 application-owner-agent，没写 template 占位符 | T-6 拆 T-6a (20 行 application-owner-agent) + T-6b (12 行 template 占位符) |
| SHOULD FIX #4 T-5 lint 前置 / 后置 | 二选一未定 | 明确 **前置 + fail-fast**（lint FAIL 直接 exit 1，阻止后续 block 跑） |
| SHOULD FIX #5 T-7~T-9 prompt 一致性 | dogfood prompt 与 T-2 模板可能不同步 | T-7 描述明确 "使用 T-2 模板"；若临时修改回头补 T-2 |

## T-1 `.harness/agents/reviewer-agent.md` 新建

- 含 section：角色 / 输入 / 输出 / 加载 SKILL / 禁止做的事（MUST NOT）/ spawn 入口签名
- 关键约束：**不能与 generator 共享上下文**；只读模式优先；只写 review 文件
- depends_on: 无
- estimated_stage: stage-3
- covers_ac: AC-1

## T-2 `.harness/agents/application-owner.md` 加 spawn 模板段

- 新增 §"如何 spawn reviewer 子 agent"
- 含 stage 2/4/6 Agent 工具调用模板（subagent_type="general-purpose"；prompt 含 SKILL 路径 + 评审材料路径 + 输出文件名 + reviewer 字段值约定 + verdict 格式）
- 写明 reviewer 字段命名约定：`claude-agent:<change-id>-stage{N}-reviewer-v{M}`
- depends_on: T-1
- estimated_stage: stage-3
- covers_ac: AC-2

## T-3 `.harness/rules/development-process.md` stage 2/4/6 加硬约束

- 实施前先 `cat .harness/rules/development-process.md | grep -E "^##"` 确认 stage 标题层级
- 三处分别加 "**必须由独立 reviewer agent 执行**；不允许同一会话同时扮演 generator 与 reviewer；引用 expert-reviewer SKILL § reviewer 字段填写规约 + application-owner.md § 如何 spawn reviewer 子 agent"
- depends_on: 无
- estimated_stage: stage-3
- covers_ac: AC-3a, AC-3b, AC-3c

## T-4 expert-reviewer SKILL 加 reviewer 字段规约

- `.harness/skills/expert-reviewer/SKILL.md` 加 §"reviewer 字段填写规约"
- 白名单：`claude-agent:<id>` / `self-attest (<理由>)`
- 黑名单：`application-owner-agent` / `application-owner` / `claude` / 空 / 模板占位符
- 说明 self_check 会硬 FAIL
- depends_on: T-1, T-2, T-3
- estimated_stage: stage-3
- covers_ac: AC-4

## T-5 self_check global reviewer lint（前置 + fail-fast）

- 在 `scripts/_self_check.sh` 加 `run_reviewer_lint` function
- 实现：
  - 反向 grep #1：`! grep -rE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/`
  - 反向 grep #2：`! grep -rE "^reviewer:[[:space:]]+<" .harness/changes/ | grep -v _template`
  - 白名单校验：每条 reviewer 字段必须以 `claude-agent:` 或 `self-attest (` 开头
- **位置**：在所有 change block 之前跑（`run_reviewer_lint` 排在 case `""` 第 1 行）
- **fail-fast**：lint FAIL 时立 exit 1（不跑后续 block，省时）
- 加 filter `reviewer-lint` 入口；加 case 调用
- depends_on: T-1~T-4
- estimated_stage: stage-3
- covers_ac: AC-5, AC-8, AC-10

## T-6a 历史回溯：20 行 application-owner-agent → self-attest

- 命令：找出所有 `reviewer: application-owner-agent` 字段行，原地改为：
  `reviewer: self-attest (会话级授权偏离 #1；2026-05-17/18 用户授权 "你合理安排规划" 省 spawn 成本；详见 harness-reviewer-agent-separation-20260518 §背景)`
- 实测：20 行分布在 5 closed change（processor-framework / llm-gateway-mvp / adapter-firecrawl / llm-qa-gen / sdk-cli-mvp）
- 不动 review 文件其他内容
- depends_on: T-5
- estimated_stage: stage-3
- covers_ac: AC-6, AC-9

## T-6b 历史回溯：12 行 template 占位符 → self-attest

- 命令：找出所有 `reviewer: <name 或 agent id>` 字段行（非 _template），改为：
  `reviewer: self-attest (template 占位符未填；早期 5 change 部分 review 文件未填字段；详见 harness-reviewer-agent-separation-20260518 §背景)`
- 实测：12 行分布在 5 个早期 change
- depends_on: T-5
- estimated_stage: stage-3
- covers_ac: AC-6, AC-9

## T-7 [process action] stage 2 spawn 子 agent 评 spec + tasks（dogfood）

- 用 T-2 写的 spawn 模板，调用 Agent(subagent_type="general-purpose", prompt=...)
- prompt **必须与 T-2 模板一致**；若实操中临时修改，回头补 T-2
- 子 agent 写 spec_review_v{N}.md + tasks_review_v{N}.md
- reviewer 字段：`claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v{N}`
- depends_on: T-1, T-2
- estimated_stage: stage-2（process action）
- covers_ac: AC-7（partial：stage 2 末 ≥2 文件）

## T-8 [process action] stage 4 spawn 子 agent 评 coding（dogfood）

- 同 T-7，stage 4 评 coding_report_v1.md + git diff
- reviewer 字段：`claude-agent:harness-reviewer-agent-separation-stage4-reviewer-v1`
- depends_on: T-1, T-2, T-7
- estimated_stage: stage-4（process action）
- covers_ac: AC-7（partial：stage 4 末 ≥3 文件）

## T-9 [process action] stage 6 spawn 子 agent 评 test（dogfood）

- 同 T-7，stage 6 评 test_report_v1.md
- reviewer 字段：`claude-agent:harness-reviewer-agent-separation-stage6-reviewer-v1`
- depends_on: T-1, T-2, T-8
- estimated_stage: stage-6（process action）
- covers_ac: AC-7（**full**：stage 6 末 ≥4 文件）

## T-10 lint + type 不回归

- 本变更不动 Python；跑 self_check AC-11 sdk-cli-mvp block 确认仍 PASS
- depends_on: T-1~T-6
- estimated_stage: stage-3
- covers_ac: AC-11

## T-11 注册 + 跑全仓 self_check（baseline + 1 = 226）

- 本变更**不**建 13 AC change block；只加 1 个 global reviewer-lint AC
- 跑 `bash scripts/_self_check.sh` 确认 `PASS: 226`（baseline 225 + 1）
- 跑 `bash scripts/_self_check.sh reviewer-lint` 套娃断言含 "reviewer-lint" 字面（AC-13 自递归）
- depends_on: T-5, T-6a, T-6b, T-7~T-9
- estimated_stage: stage-3
- covers_ac: AC-12, AC-13

## §process_tasks（含 dogfood spawn 与流程动作）

- T-7：[process action] stage 2 spec/tasks spawn 评
- T-8：[process action] stage 4 code spawn 评
- T-9：[process action] stage 6 test spawn 评
- T-12：stage-7 commit + push
- T-13：stage-9 deploy verify（无部署面 → skipped）
- T-14：stage-10 close

## 任务依赖（文字 only；删除 ASCII DAG）

- T-1, T-3 并行（独立无依赖）
- T-2 ← T-1
- T-4 ← T-1, T-2, T-3
- T-5 ← T-1~T-4
- T-6a, T-6b 并行 ← T-5
- T-7 ← T-1, T-2（**不等 T-3/T-4/T-5/T-6**；spawn 自评 spec 不需要 self_check lint 完成）
- T-8 ← T-1, T-2, T-7
- T-9 ← T-1, T-2, T-8
- T-10 ← T-1~T-6
- T-11 ← T-5, T-6a, T-6b, T-7, T-8, T-9（全收口）
- T-12 ← T-11
- T-13 ← T-12
- T-14 ← T-12, T-13

无环 ✓。

## AC 覆盖矩阵

| AC | task |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3a/3b/3c | T-3 |
| AC-4 | T-4 |
| AC-5 | T-5 |
| AC-6 | T-6a, T-6b |
| AC-7 | T-7, T-8, T-9 |
| AC-8 | T-5 |
| AC-9 | T-6a, T-6b |
| AC-10 | T-11 |
| AC-11 | T-10 |
| AC-12 | T-11 |
| AC-13 | T-11 |
