---
change_id: harness-reviewer-agent-separation-20260518
version: 1
authored_at: 2026-05-18T12:40:00Z
---

# Tasks

## T-1 `.harness/agents/reviewer-agent.md` 新建

- 文件含 section：角色 / 输入 / 输出 / 加载的 SKILL / 禁止做的事（MUST NOT）/ spawn 入口签名
- 关键约束：**不能与 generator 共享上下文**；**只读模式优先**（用 Read/Grep/Glob，不 Edit/Write 代码）；**只写自己的 review 文件**
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-1

## T-2 `.harness/agents/application-owner.md` 加 spawn 模板段

- 新增 §"如何 spawn reviewer 子 agent"
- 含 stage 2/4/6 三处场景下 Agent 工具调用模板（`subagent_type="general-purpose"`，prompt 给完整路径 + SKILL 路径 + 输出文件名 + verdict 格式要求）
- 写明 reviewer 字段如何填（`claude-agent:<change-id>-stage{N}-reviewer-v{M}` 命名约定）
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-2

## T-3 `.harness/rules/development-process.md` 加硬约束

- stage 2 §进入条件：新加 "**必须由独立 reviewer agent 执行**；不允许同一会话同时扮演 generator 与 reviewer"
- stage 4 / stage 6 同
- 引用 expert-reviewer SKILL 与 application-owner.md spawn 模板
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-3

## T-4 expert-reviewer SKILL 加 reviewer 字段规约

- `.harness/skills/expert-reviewer/SKILL.md` 加 §"reviewer 字段填写规约"
- 白名单：`claude-agent:<id>` 真 spawn 子 agent / `self-attest (<理由>)` 显式偏离
- 黑名单：`application-owner-agent` / `application-owner` / `claude` / 空 / 模板占位符
- 说明 self_check 会硬 FAIL
- depends_on: T-1, T-2, T-3 / estimated_stage: stage-3 / AC: AC-4

## T-5 self_check global reviewer lint

- 在 `scripts/_self_check.sh` 各 block 之前加 `run_reviewer_lint` function（独立段）
- 实现：
  - 正向 grep：所有 `.harness/changes/*/review/*.md` reviewer 字段必须 ≥ 1（即所有 review 文件都有字段）
  - 反向 grep：`! grep -rE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/`
  - 反向 grep：`! grep -rE "^reviewer:[[:space:]]+<name" .harness/changes/`（模板占位符）
  - 白名单校验：每条 reviewer 字段必须以 `claude-agent:` 开头或 `self-attest (` 开头
- 加 filter `reviewer-lint` 入口；加 case 调用
- 全跑入口排在所有 block 之前（或最后），不与 block 重复
- depends_on: T-1~T-4 / estimated_stage: stage-3 / AC: AC-5, AC-8

## T-6 历史 12 change reviewer 字段批量回溯

- 扫描全仓所有 review 文件，把 `reviewer: application-owner-agent` 改为 `reviewer: self-attest (会话级授权偏离 #1；2026-05-17/18 通宵会话用户授权 "你合理安排规划" 省 spawn 成本；详见 harness-reviewer-agent-separation-20260518 §背景)`
- 模板占位符 `<name 或 agent id>` 也改为 self-attest（这是模板未填的另一种偏离形态）
- 不动 review 文件其他内容（content 不变；只字段诚实标注）
- depends_on: T-5 / estimated_stage: stage-3 / AC: AC-6, AC-9

## T-7 dogfood：spawn 子 agent 评 stage 2

- 在 stage 2 用 Agent(subagent_type="general-purpose") spawn reviewer 子 agent
- prompt 给：spec.md 路径 + tasks.md 路径 + expert-reviewer SKILL 路径 + 输出文件路径 + reviewer 字段值（`claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v1`）+ verdict 格式
- 子 agent 独立读所有材料 + 写 spec_review_v1.md + tasks_review_v1.md
- 验证：grep `reviewer: claude-agent:` 命中
- depends_on: T-1, T-2 / estimated_stage: stage-2 / AC: AC-7

## T-8 dogfood：spawn 子 agent 评 stage 4

- 同 T-7，stage 4 评 coding_report + 实际 git diff
- reviewer 字段：`claude-agent:harness-reviewer-agent-separation-stage4-reviewer-v1`
- depends_on: T-1, T-2, T-7 / estimated_stage: stage-4 / AC: AC-7

## T-9 dogfood：spawn 子 agent 评 stage 6

- 同 T-7，stage 6 评 test_report（本变更 test 主要是 self_check lint，不是 pytest）
- reviewer 字段：`claude-agent:harness-reviewer-agent-separation-stage6-reviewer-v1`
- depends_on: T-1, T-2, T-8 / estimated_stage: stage-6 / AC: AC-7

## T-10 lint + type 不回归

- 本变更不动 Python；跑 ruff + mypy 仅确认全仓无回归
- depends_on: T-1~T-6 / estimated_stage: stage-3 / AC: AC-11

## T-11 注册 + 跑全仓 self_check

- 暂时不为本变更建一个 13 AC block；本变更的 AC 在 spec 阶段通过 global lint + 阶段产物覆盖
- 但 reviewer-lint 是新 block；加入总入口
- 期望全仓 PASS: 225（原 16 block）+ lint 计入新 1 个 → 226+；具体数等实测
- depends_on: T-5, T-6, T-7~T-9 / estimated_stage: stage-3 / AC: AC-10, AC-12, AC-13

## process_tasks

- T-12 stage-7 commit + push
- T-13 stage-9 deploy verify（无部署面 → skipped）
- T-14 stage-10 close

## 任务依赖图

```
T-1 (reviewer-agent.md) ─┐
T-3 (process rule) ──────┤
                         ↓
                    T-2 (owner spawn 模板)
                         ↓
                    T-4 (SKILL 字段规约)
                         ↓
                    T-5 (self_check lint) ← T-7 dogfood stage 2
                         ↓                      ↓
                    T-6 (历史回溯)         T-8 dogfood stage 4
                         ↓                      ↓
                    T-10 (lint+type)       T-9 dogfood stage 6
                         ↓                      ↓
                    T-11 (全仓 self_check)
                         ↓
                    T-12 → T-13 → T-14
```

## AC 覆盖矩阵

| AC | task |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3 | T-3 |
| AC-4 | T-4 |
| AC-5 | T-5 |
| AC-6 | T-6 |
| AC-7 | T-7, T-8, T-9 |
| AC-8 | T-5 |
| AC-9 | T-6 |
| AC-10 | T-11 |
| AC-11 | T-10 |
| AC-12 | T-11 |
| AC-13 | T-11 |
