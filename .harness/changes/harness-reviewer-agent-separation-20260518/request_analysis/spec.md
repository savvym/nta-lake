---
change_id: harness-reviewer-agent-separation-20260518
version: 1
authored_at: 2026-05-18T12:35:00Z
status: draft
---

# Spec：评审独立 Agent + spawn 模板 + self_check 硬守门 + 历史 reviewer 回溯

## 背景

实证发现的流程缺陷（用户 2026-05-18 提问触发）：

- `.harness/skills/expert-reviewer/SKILL.md` 自己写：**"评判者必须是独立子会话或独立 Agent，**不能与 Generator 共享上下文**。否则会偏袒。"** + "当前会话**未**参与该产物的撰写"
- 但本会话（2026-05-17/18）连续 7 个变更（processor-framework / llm-gateway-mvp / adapter-firecrawl / llm-qa-gen / sdk-cli-mvp 等）reviewer 字段全部写 `application-owner-agent` —— **同一个会话同一个 agent 同时扮演 generator + reviewer**
- 早期 5 个变更（bootstrap / core-domain / cas-storage / auth-scaffold / repo-api-mvp）reviewer 字段是 `claude-agent:<change-id>-stage{2|4|6}-reviewer`——真 spawn 过子 agent
- **流程退化**：硬约束被静默违反，且**没有任何机械化手段**阻止再发生
- 结果：本会话 21 份 review 文件（7 change × 3 阶段）verdict 一律 APPROVED 0 MUST FIX——不是 spec 真没问题，是评审视角与实现视角合一了

## 问题陈述

- 缺独立 reviewer agent 文档定义（`.harness/agents/` 只有 application-owner.md）
- 缺 owner agent 中"如何 spawn reviewer 子 agent"的可复制模板
- expert-reviewer SKILL 的硬约束**未机械化**到 self_check
- 12 个历史 closed change 的 reviewer 字段保留 `application-owner-agent` 误导未来读者以为流程合规
- 需要一个**dogfood**：本变更自己用新流程跑通才说明新流程可行

## 范围

**In scope**：

- `.harness/agents/reviewer-agent.md`：独立 reviewer agent 角色定义（角色 / 输入 / 输出 / 不允许的事 / 加载 SKILL / spawn 入口签名）
- `.harness/agents/application-owner.md`：加 §"如何 spawn reviewer 子 agent"完整代码模板（Agent tool 调用形式 + prompt 模板 + 输出文件路径约束）
- `.harness/rules/development-process.md`：stage 2/4/6 §进入条件 加硬约束 "必须由独立 reviewer agent 执行；不允许同会话 self-review"
- `.harness/skills/expert-reviewer/SKILL.md`：加 §"reviewer 字段填写规约"：白名单 (`claude-agent:...` 实际 spawn 子 agent ID 或 `self-attest (<理由>)` 明确偏离声明) + 黑名单（裸 `application-owner-agent` / `application-owner` / generator id）
- `scripts/_self_check.sh`：global lint AC（不属任何 change block，在汇总区前跑）：扫 `.harness/changes/*/request_analysis/review/*.md + coding/review/*.md + unit_test/review/*.md` 的 `reviewer:` 字段，命中黑名单或缺合规白名单 → FAIL
- **历史回溯**：12 个历史 closed change（含本会话 7 个直接命中 application-owner-agent + 5 个早期变更模板字段 `<name 或 agent id>` 未填）的 reviewer 字段批量改 `self-attest (会话级授权偏离 #N；详见 ...)`
- **dogfood**：本变更 stage 2/4/6 review 文件由 spawn 的 general-purpose 子 agent 写入；reviewer 字段以 `claude-agent:` 开头记录子 agent 名称

**Out of scope**（显式）：

- 自定义 `.claude/agents/reviewer-agent` Markdown subagent（zero-config 选 general-purpose） → follow-up `custom-reviewer-subagent-*`
- worktree 隔离的 reviewer → follow-up `reviewer-worktree-isolation-*`
- 历史 12 个 change 补真评审（spawn 36 次 + 可能要动 closed 代码） → follow-up `historical-reviewer-backfill-*`
- planner / generator 三角色完整分离 → follow-up `harness-planner-generator-separation-*`
- reviewer 子 agent 工具限定（Read/Grep only） → follow-up `reviewer-tool-restrict-*`
- reviewer 评审深度 metric（MUST FIX 数量分布等） → follow-up `reviewer-quality-metric-*`

## 验收标准（13 AC）

- AC-1：reviewer-agent.md 存在且含关键 section（角色 / 输入 / 输出 / 黑约束）；
  `test -f .harness/agents/reviewer-agent.md && grep -q "角色" .harness/agents/reviewer-agent.md && grep -q "禁止\|不允许\|MUST NOT" .harness/agents/reviewer-agent.md`
- AC-2：application-owner.md 含 spawn 模板段（含 `Agent(` + `subagent_type` + `general-purpose`）；
  `test -f .harness/agents/application-owner.md && grep -q "Agent(" .harness/agents/application-owner.md && grep -q "subagent_type" .harness/agents/application-owner.md && grep -q "general-purpose" .harness/agents/application-owner.md`
- AC-3：development-process.md stage 2/4/6 进入条件含"独立"+"reviewer"硬约束；
  `grep -A30 "阶段 2" .harness/rules/development-process.md | grep -qE "独立.*reviewer|reviewer.*独立|不允许.*self-review"`
- AC-4：expert-reviewer SKILL 含 reviewer 字段白名单 + 黑名单规约；
  `grep -q "reviewer 字段" .harness/skills/expert-reviewer/SKILL.md && grep -q "claude-agent:" .harness/skills/expert-reviewer/SKILL.md && grep -q "self-attest" .harness/skills/expert-reviewer/SKILL.md`
- AC-5：self_check 含 global reviewer lint AC（独立 function 或汇总区前）；
  `grep -q "run_reviewer_lint\|reviewer_field_lint" scripts/_self_check.sh`
- AC-6：历史回溯无遗漏——全仓 grep `reviewer: application-owner-agent` 命中数 = 0（仅 reviewer-agent.md 内引用例外）；
  `! grep -rE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/`
- AC-7：dogfood——本变更 3 个 review 文件 reviewer 字段以 `claude-agent:` 开头（不是 application-owner-agent，不是 self-attest）；
  `[ "$(grep -hE "^reviewer:[[:space:]]+claude-agent:" .harness/changes/harness-reviewer-agent-separation-20260518/request_analysis/review/spec_review_v1.md .harness/changes/harness-reviewer-agent-separation-20260518/coding/review/code_review_v1.md .harness/changes/harness-reviewer-agent-separation-20260518/unit_test/review/test_review_v1.md | wc -l)" -ge 3 ]`
- AC-8：global lint 含正向（白名单匹配 ≥1）+ 反向（黑名单匹配 = 0）双 grep；
  `grep -A20 "run_reviewer_lint\|reviewer_field_lint" scripts/_self_check.sh | grep -qE "! *grep|grep -v" && grep -A20 "run_reviewer_lint\|reviewer_field_lint" scripts/_self_check.sh | grep -qE "self-attest|claude-agent"`
- AC-9：self-attest 文案规约——历史 12 change 改为 self-attest 的字段每条都含括号文案；
  `[ "$(grep -rhE "^reviewer:[[:space:]]+self-attest" .harness/changes/ | grep -cE "\\(.+\\)")" -ge 12 ]`
- AC-10：跑 self_check global lint 通过（不 FAIL）；
  `bash scripts/_self_check.sh reviewer-lint 2>&1 | tail -3 | grep -q "PASS"`
- AC-11：ruff + mypy 全仓不回归（本变更不动 Python 但跑确认）；
  `uv run ruff check apps/api packages/core packages/sdk-py worker/src && uv run mypy apps/api/dataplat_api packages/core/src packages/sdk-py/src worker/src`
- AC-12：全仓 self_check 通过 = 旧 225 + 本块 13 = 238（含全局 lint）；
  `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh 2>&1 | tail -3 | grep -q "PASS: 238"`
- AC-13：self_check 自递归

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| spawn 子 agent 评审用时长 | 高 | 本变更 stage 2/4/6 慢 3x | 接受；这是"找回评审独立性"的代价 |
| spawn 子 agent 拿不到上下文写出空 review | 中 | dogfood 失败 | prompt 模板里给完整文件路径 + SKILL 路径 + 明确输出文件名 + 限定输出格式（含 verdict + MUST FIX 列表） |
| 历史回溯改 12 个 change 字段后破坏既有 self_check（block-specific AC 含 reviewer 字段断言？） | 中 | 全仓 self_check FAIL | 现 self_check 各 block 不检 reviewer 字段，只新加 global lint；预扫一遍 |
| AC-6 反向 grep 误命中（如 reviewer-agent.md 文档里举例用 application-owner-agent） | 中 | AC-6 FAIL | 反向 grep pattern 加 `^reviewer:[[:space:]]+` 前缀严格匹配字段行；文档示例不在字段位置 |
| AC-7 dogfood 要先有 spawn 模板 + 子 agent 真跑过 | 中 | AC-7 顺序依赖 | tasks T-1 先写 spawn 模板；T-2 spawn 子 agent 评审；review 文件由子 agent 落盘 |
| 子 agent 没权限写文件（subagent 工具限制） | 低 | dogfood 卡 | general-purpose subagent 有 Write 权限（见 Agent 工具描述）；预演 1 次 |
| AC 验证命令 dry-parse 全过（SKILL #8） | 低 | spec 卡 stage 2 | 本变更 AC 全是 bash 命令；用 shell -n 检 |
| summary.md SSoT 漂移（SKILL #9 第 6 次） | 低 | 流程缺陷 | stage 0 已填好；占位符 grep = 0 |
| reviewer 字段约束在 reviewer-agent.md 引用 `application-owner-agent` 示例触发 AC-6 误报 | 中 | 误 FAIL | 文档示例用代码块 + 反向 grep 限定字段行（`^reviewer:`） |

## 跨链路一致性自审（SKILL 9 条 + 候选第 11 / 12 反哺）

1. ✅ 四链路一致：reviewer-agent.md 定义 ↔ application-owner.md spawn 模板 ↔ expert-reviewer SKILL 字段规约 ↔ self_check lint ↔ AC-1/2/4/5
2. ✅ 事务边界：本变更无 DB；纯文档 + shell script
3. ✅ AC 验证命令一行式：13 条全单行
4. ✅ 风险缓解 ↔ AC：spawn 模板 ↔ AC-2/7；历史回溯 ↔ AC-6/9；lint 守门 ↔ AC-5/8/10
5. ✅ commit 链：sdk-cli-mvp-20260518 (4ae8a35) → 本变更 base
6. ✅ 反向 grep：AC-6 反向拦 `^reviewer: application-owner-agent` 字段行（不会误命中文档示例）
7. ✅ process_tasks 6 条：T-9~T-14 占位
8. ✅ AC 验证命令真跑 dry-parse：bash 命令，需用 `bash -n` 句法检
9. ✅ summary.md frontmatter：stage 0 即填好；占位符 grep = 0
10. (候选) `cd apps/api && uv sync --extra dev`：本变更不跑 pytest，不撞此坑
11. (候选第 11) processor view.open 嵌套：本变更纯文档不撞
12. **(新候选 #12) reviewer 必须独立 agent**：**本变更就是要把这条机械化**——若 self_check 守门通过 + dogfood 通过，候选直接落 SKILL（第 1 次实证就落，因为这是 SKILL 自己已写的硬约束，违反者已累积 7 次）

## 受影响模块

- 新建：`.harness/agents/reviewer-agent.md`
- 改动：`.harness/agents/application-owner.md`（加 spawn 模板段）
- 改动：`.harness/rules/development-process.md`（stage 2/4/6 加硬约束）
- 改动：`.harness/skills/expert-reviewer/SKILL.md`（加 reviewer 字段规约）
- 改动：`scripts/_self_check.sh`（加 global reviewer lint）
- 改动：12 个历史 closed change 的 review 文件 reviewer 字段（self-attest 化）
- 改动：本变更自己的 review 文件 reviewer 字段（dogfood claude-agent:...）

## 不受影响但易混淆的模块

- dataplat 代码（apps/api / packages/* / worker / apps/web）：本变更不动一行 Python/TS
- 其他 15 个 change 的非 review 文件（spec.md / coding_report.md / test_report.md / ci_result.md / deploy_verify.md / summary.md）：不动

## 引用

- `.harness/skills/expert-reviewer/SKILL.md` §进入条件 § plan 模式（已有硬约束）
- `.harness/agents/application-owner.md` §1.3（已写"由 Generator 还是 Reviewer 执行"）
- `.harness/rules/development-process.md` §阶段 2/4/6
- 用户 2026-05-18 提问 + B 方案授权 + 3 个 scope 选择（spawn=general-purpose；历史=self-attest；守门=硬 FAIL）
- 实证数据：本会话 7 change × 3 review = 21 文件 reviewer 字段命中违规
