---
change_id: harness-reviewer-model-sonnet-20260518
title: spawn reviewer 子 agent 默认用 sonnet 模型（速度优先 + review 不需 opus 级推理）
owner: application-owner-agent
started_at: 2026-05-18T20:55:00Z
stage: deployment
status: in_progress
last_updated: 2026-05-18T20:55:00Z
related_changes:
  - harness-reviewer-agent-separation-20260518
  - harness-ac-behavioral-tier-20260518
  - repo-files-tab-v2-20260518
note: 由 repo-files-tab-v2 stage 2 准备阶段触发——用户反馈 opus reviewer 太慢，把"reviewer 默认 sonnet"固化到 .harness/ 规约层
---

# Summary

> 微小 harness 演进：把 3 个 spawn reviewer 模板的 `Agent(...)` 调用统一加 `model="sonnet"`，并附"为什么 sonnet"理由文案。

## 一句话目标

修改 `.harness/agents/application-owner.md §7.5` + `.harness/agents/reviewer-agent.md §7` + `.harness/skills/expert-reviewer/SKILL.md § Application Owner 怎么 spawn` 三处 spawn 模板，统一加 `model="sonnet"`。

## 范围摘要

- **In scope**：
  - AC-1：`application-owner.md §7.5` 模板含 `model="sonnet"` + 理由段落
  - AC-2：`reviewer-agent.md §7` 模板含 `model="sonnet"`
  - AC-3：`expert-reviewer/SKILL.md § Application Owner 怎么 spawn` 模板含 `model="sonnet"`
  - AC-4：reviewer-agent.md 单独一节"模型选择"说明 sonnet 的根因（review 任务不需 opus 级推理 / 速度差 3-5x / opus 留给 generator）

- **Out of scope**：
  - 不改 `scripts/_self_check.sh` 加 grep 守门 model="sonnet"（→ follow-up `harness-reviewer-model-lint-*` P3）
  - 不强制改 generator 模型（仍跟 session 主模型）
  - 不引入"model 可配置参数"（保持字面 sonnet，避免过早抽象）
  - 不回填历史 review 文件 model 字段（review 文件本身不记录 spawning model）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done | v1 | — | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | self-attest | — | — | self-attest（会话级授权偏离；micro change 仅改 3 处字面常量 + 1 段理由文案；用户在 repo-files-tab-v2 stage 2 准备阶段授权快速推进） |
| 3 编码实现 | in_progress | v1 | — | （直接 Edit 3 文件 + reviewer-agent.md 加一节） |
| 4 编码评审 | self-attest | — | — | self-attest（同上理由） |
| 5 单测编写 | skipped | — | — | 无代码改动，纯文档；无单测 |
| 6 单测评审 | skipped | — | — | 同上 |
| 7 代码推送 | pending | — | — | main 直接 commit（无 remote） |
| 8 CI 验证 | self-attest | — | — | 项目无 remote 长期未决（沿用既往）|
| 9 部署验证 | pending | — | — | self_check.sh 跑 reviewer-lint + ac-kind-lint PASS 验证未破坏既有约束 |
| 10 用户确认 | pending | — | — | repo-files-tab-v2 stage 2 用新规约 spawn reviewer 实证生效 |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-18 | reviewer 固定 sonnet，不可配置 | review 任务（核对 grep 表达式 / 跨文件 cross-ref / 模板字段）= 模式匹配 + 谨慎陈述，不需 opus 级推理；sonnet 4.6 速度 3-5x opus 4.7；保持字面常量避免过早抽象 | spec.md AC-1/2/3 |
| 2026-05-18 | 不加 self_check grep 守门 | 3 处字面 `model="sonnet"` 漏改 → 回退到 session 主模型（仍能 review），不破坏正确性；加 grep 守门是 P3 polish | spec.md 非范围 |
| 2026-05-18 | stage 2/4/6 self-attest 不 spawn reviewer | micro change（diff 3 处字面 + 几行理由文案）；spawn cost > review value；session 已授权"修一下 reviewer 的逻辑" | summary.md 阶段表 |

## 当前阻塞

- 无。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| NICE | self_check 加 grep 守门"3 处模板必须含 model=\"sonnet\"" | follow-up `harness-reviewer-model-lint-*`（P3） |
| NICE | 把 generator/coding agent 的模型选择也纳入规约 | 暂不做：generator 跟 session 主模型已是合理默认 |

## 交付

- Branch：main（无 remote）+ worktree branch `worktree-harness-reviewer-sonnet`
- PR：N/A
- Merge commit：—
- 部署版本：N/A（纯文档/规约改动）
- 用户确认：—
- 关闭时间：—

## 复盘

> 关闭时填写。
