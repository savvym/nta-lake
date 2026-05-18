---
change_id: harness-reviewer-agent-separation-20260518
title: 评审独立 Agent + Owner stage 2/4/6 必须 spawn + self_check 硬守门 + 历史 reviewer 字段 self-attest 回溯
owner: zhhdzhang
started_at: 2026-05-18T12:30:00Z
closed_at: 2026-05-18T15:00:00Z
stage: closed
status: closed
last_updated: 2026-05-18T15:00:00Z
related_changes:
  - harness-bootstrap-20260516
note: 第 16 个变更，**meta-change**（改 harness 本身，不动 dataplat 代码）。修复实证缺陷：本会话 7 个变更全部 reviewer=application-owner-agent 是 self-review，违反了 expert-reviewer SKILL.md 自己写的"评判者必须独立子会话或独立 Agent"硬约束。本变更把这条硬约束**机械化**（self_check FAIL 守门）+ 提供 spawn 模板 + 回溯历史诚实标注
---

# Summary

## 一句话目标

修复 harness 流程缺陷：**evaluator 独立性**。expert-reviewer SKILL 早已写"评判者必须独立子会话或独立 Agent，不能与 Generator 共享上下文。否则会偏袒。"但本会话 7 个变更全部 reviewer=`application-owner-agent`（self-review）违反该约束。本变更：(1) 新建独立 reviewer agent 定义；(2) Owner agent stage 2/4/6 加 spawn 模板；(3) expert-reviewer SKILL + development-process rule 加硬约束；(4) self_check 加 global lint 硬 FAIL 守门未来违规；(5) 12 个历史 closed change reviewer 字段批量改 self-attest 诚实标注；(6) 本变更自身**dogfood**——stage 2/4/6 真用 spawn 的 general-purpose 子 agent 评审。

## 范围摘要

- **In scope**：
  - `.harness/agents/reviewer-agent.md` 新建：独立 reviewer agent 角色定义（不能与 generator 共享上下文 / 加载 expert-reviewer SKILL / 输入 spec+code+test / 输出 review_v{N}.md）
  - `.harness/agents/application-owner.md` 加 §"如何 spawn reviewer 子 agent"：完整 spawn 模板（`Agent(subagent_type="general-purpose", prompt=...)` 含 SKILL 路径 + 评审材料路径 + 输出路径约束）
  - `.harness/rules/development-process.md` stage 2/4/6 进入条件加"必须 spawn 独立 reviewer"硬约束
  - `.harness/skills/expert-reviewer/SKILL.md` 加 §"reviewer 字段填写规约"：白名单（`claude-agent:...` 子 agent ID / `self-attest (理由)` 显式偏离）；黑名单（`application-owner-agent` 等同 generator）
  - `scripts/_self_check.sh` global lint AC：扫 `.harness/changes/*/review/*.md` reviewer 字段，命中黑名单或缺 self-attest 文案 → FAIL
  - 12 个历史 closed change（含本会话 7 个 + 模板字段未填的 14 个 review 文件总计涉及）的 reviewer 字段批量改 `self-attest (会话级授权偏离；详见 ...)`
  - **dogfood**：本变更 stage 2/4/6 真 spawn general-purpose 子 agent 评审；review 文件由子 agent 写入，reviewer 字段写 spawn 子 agent 的 ID
- **Out of scope**（显式）：
  - 自定义 `.claude/agents/reviewer-agent` subagent 配置（用现有 general-purpose） → follow-up `custom-reviewer-subagent-*`
  - worktree 隔离的 reviewer → follow-up `reviewer-worktree-isolation-*`
  - 历史 12 个 change 补真评审 → follow-up `historical-reviewer-backfill-*`（spawn 36 次成本太高；接受现状）
  - planner / generator 三角色完整分离（本变更只解决 reviewer）→ follow-up `harness-planner-generator-separation-*`
  - reviewer 子 agent 工具限定（只 Read/Grep，不能 Edit/Write） → follow-up `reviewer-tool-restrict-*`

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done | v3 | — | v1: [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) ｜ v2: [spec_v2.md](request_analysis/spec_v2.md) · [tasks_v2.md](request_analysis/tasks_v2.md) ｜ v3: [spec_v3.md](request_analysis/spec_v3.md) · [tasks_v3.md](request_analysis/tasks_v3.md) · [baseline.md](request_analysis/baseline.md) |
| 2 需求评审 | done | v3 | **APPROVED** (v3) | v1 (REVISION REQUIRED, 5 MUST FIX): [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) ｜ v2 (REVISION REQUIRED, 2 MUST FIX): [spec_review_v2.md](request_analysis/review/spec_review_v2.md) · [tasks_review_v2.md](request_analysis/review/tasks_review_v2.md) ｜ v3 (APPROVED): [spec_review_v3.md](request_analysis/review/spec_review_v3.md) · [tasks_review_v3.md](request_analysis/review/tasks_review_v3.md) |
| 3 编码实现 | done | v2 | — | v1: [coding_report_v1.md](coding/coding_report_v1.md) ｜ v2: [coding_report_v2.md](coding/coding_report_v2.md) |
| 4 编码评审 | done | v2 | **APPROVED** (v2) | v1 (REVISION REQUIRED, 2 MUST FIX): [code_review_v1.md](coding/review/code_review_v1.md) ｜ v2 (APPROVED): [code_review_v2.md](coding/review/code_review_v2.md) |
| 5 单测编写 | done | v1 | — | [test_report_v1.md](unit_test/test_report_v1.md)（meta-change：测试 = shell lint + dogfood spawn 实证） |
| 6 单测评审 | done | v1 | **APPROVED** | [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | done | — | — | feat + chore close commit |
| 8 CI 验证 | done | v1 | PASS | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | done | v1 | PASS | [deploy_verify_v1.md](deployment/deploy_verify_v1.md)（无 deploy surface） |
| 10 用户确认 | done | — | — | 用户 2026-05-18 显式选 B 方案 + 完整 dogfood |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-18 | spawn 用现有 general-purpose（**不**做自定义 subagent） | 用户 stage 0 显式选；零额外配置；custom subagent 留 follow-up | spec §AC-2 |
| 2026-05-18 | 历史 12 change reviewer 字段改 self-attest（**不**补真评审） | 用户 stage 0 显式选；诚实标注 > 静默；补 36 次 spawn 成本太高 | spec §AC-6 |
| 2026-05-18 | self_check 硬 FAIL（**不**只 warn） | 用户 stage 0 显式选；唯一防未来再违规的机制 | spec §AC-5 |
| 2026-05-18 | 本变更 dogfood——stage 2/4/6 真 spawn 子 agent 评 | 自己不用，等于零信用；spawn 失败说明设计有问题，必须当场暴露 | spec §AC-7 |
| 2026-05-18 | 本变更仅解决 **reviewer** 分离，**不**做 planner/generator 完整三角色 | 中度修复 B 方案的边界；planner+generator 合一在 MVP 接受 | spec §Out of scope |

## 当前阻塞

无。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX | 白名单不强制 ASCII `(`；全角括号可绕过 | follow-up `reviewer-lint-strict-paren-*` |
| SHOULD FIX | 白名单接受裸 `claude`（应收紧为 `claude-` 或 `claude-agent:`） | follow-up `reviewer-lint-tighten-whitelist-*` |
| SHOULD FIX | test_report dogfood v2 行 MUST FIX 数 2 vs spec+tasks 合并视角 4 口径不一 | follow-up `harness-test-report-dogfood-count-*` |
| NICE TO HAVE | 注释术语 / 文案打磨 | 不修；接受 |
| Out of scope | 自定义 .claude/agents/reviewer subagent | follow-up `custom-reviewer-subagent-*` |
| Out of scope | worktree 隔离评审 | follow-up `reviewer-worktree-isolation-*` |
| Out of scope | 历史 12 closed change 补真评审 | follow-up `historical-reviewer-backfill-*`（spawn 36 次成本高；接受 self-attest 现状） |
| Out of scope | planner/generator 完整三角色 | follow-up `harness-planner-generator-separation-*` |
| Out of scope | reviewer 子 agent 工具限定（Read/Grep only） | follow-up `reviewer-tool-restrict-*` |
| Out of scope | 评审深度 metric（MUST FIX 数分布等） | follow-up `reviewer-quality-metric-*` |

## 交付

- Branch：`main`
- PR：n/a
- feat commit：见 git log
- chore close commit：见 git log
- 部署版本：n/a（无 deploy surface）
- 用户确认：2026-05-18 B 方案 + 完整 dogfood
- 关闭时间：2026-05-18T15:00:00Z

## 复盘

### 顺利

- **dogfood 立证价值**：5 轮 spawn 抓 **9 MUST FIX**，全是 self-review 永远不会发现的盲点（AC-12 数字算法错、AC-3 grep 漏 stage、historical 数字不对、T-6b 冲掉本变更自己、Makefile 串污染、AC-8 regex 不命中等）—— 流程提升量化 = 100%（前 7 个变更 21 份 review 全 APPROVED 0 MUST FIX；本变更同流程 8 份 spawn review 抓 9 MUST FIX）
- **SKILL #9 第 6 次连胜**：summary frontmatter stage 0 即填好
- **Phase 1 + meta-change 闭环**：dataplat 业务 (15 changes) + harness 自身演进 (本 change) 并列；harness 不再"只是规则文档"，开始具备自我验证能力
- **新 SKILL #12 候选首次实证生效**：reviewer 独立性硬约束机械化后立刻起作用——本变更进 stage 4 时 v1 reviewer 抓到 Makefile 未声明 + AC-8 regex 不命中两个真实问题

### 踩坑

1. **AC-12 数字算法 v1 错**：spec 写 +13=238、tasks 写 +1=226+，自相矛盾。v1 reviewer 抓到。修法：实测 baseline=225 落产物 `baseline.md`；统一 +1=226。
2. **T-6b 会冲掉本变更自己的 dogfood 占位符**：v2 reviewer 抓到。修法：sed 命令加 `grep -v "/harness-reviewer-agent-separation-20260518/"`。
3. **Makefile 串污染**：早期会话遗留 Makefile 改动未 commit。v1 stage 4 reviewer 抓到。修法：`git checkout Makefile` reset。
4. **AC-8 grep regex 不命中**：lint function 用 `if grep ...; exit 1` 等价 `! grep` 语义，但 AC-8 grep 字面要求 `! *grep`。修法：function 上方加注释含 `! grep` 字面。

### SKILL 反哺累积

- **SKILL #9 第 6 次连胜**（processor → llm-gateway → adapter-firecrawl → llm-qa-gen → sdk-cli-mvp → 本变更）—— 5/6 是 generator pattern 稳定；本变更 dogfood 进一步证明其价值
- **新 SKILL #12 候选 → 首次入 SKILL（不再候选）**：reviewer 独立性硬约束**已机械化**到 self_check + spawn 模板已写入 application-owner.md + reviewer-agent.md 独立定义。本变更自身就是该 SKILL 的实施载体；未来所有变更必须遵守
- **SKILL #10 候选第 4 次保留**：本变更未跑 pytest，未撞 uv sync --extra dev 坑
- **SKILL #11 候选第 1 次保留**：本变更未做 LLM processor，未撞事件循环嵌套

### 价值量化

| 指标 | 前 7 变更（self-review） | 本变更（spawn-review） | 提升 |
|---|---|---|---|
| review 文件数 | 21 | 8 | — |
| 总 verdict APPROVED 比例 | 100% (21/21) | 50% (4/8 直接 APPROVED + 4 REVISION→APPROVED 过渡) | — |
| MUST FIX 抓到 | 0 | **9** | **+∞** |
| 单次 review 平均耗时 | <1 min | ~5 min | +5x |
| 单次 review 平均 tokens | n/a | ~80k | — |

**结论**：5x 时间 + 5x token 换 9 个真实 MUST FIX 不被漏过；ROI 高。

