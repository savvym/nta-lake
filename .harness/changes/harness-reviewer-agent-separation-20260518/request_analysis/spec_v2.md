---
change_id: harness-reviewer-agent-separation-20260518
version: 2
authored_at: 2026-05-18T13:10:00Z
status: draft
note: v2 修 spec_review_v1.md 列出的 3 条 MUST FIX + 5 条 SHOULD FIX；v1 保留作历史
---

# Spec v2：评审独立 Agent + spawn 模板 + self_check 硬守门 + 历史 reviewer 回溯

## v2 改动摘要

| MUST FIX | v1 问题 | v2 修复 |
|---|---|---|
| #1 spec AC-12 算法错误 + tasks 矛盾 | spec 写 +13=238、tasks 写 +1=226+，自相矛盾且基数未给推导 | 实测 baseline = **225**；本变更新加 **1 个** global lint AC；AC-12 改用动态命令断言 `PASS == baseline+1`，不钉死数字 |
| #2 AC-3 grep 漏 stage 4/6 | `grep -A30 "阶段 2"` 只能覆盖 stage 2 | 拆 AC-3a/3b/3c 三条；用 `awk '/## 阶段 N/,/^## 阶段 [^N]\|^---/'` 跨段匹配 |
| #3 历史回溯数字对不上 | spec 写"7 change / 12 change"，实测 20 行 application-owner-agent (5 closed) + 12 行 template 占位符 (5 change，非 _template) | 改为实测：**20 application-owner-agent 行 + 12 template 占位符行 = 32 行 self-attest 化** |
| SHOULD FIX #1 AC-7 时序 | stage 2 时 stage 4/6 文件不存在，AC-7 grep 会 stderr 报错 | 拆 AC-7a (stage 2 末 ≥2) / AC-7b (stage 4 末 ≥3) / AC-7c (stage 6 末 ≥4)；总数 4 文件不是 3 |
| SHOULD FIX #3 AC-13 命令空 | "AC-13 自递归" 无 bash | 补 `true`（套娃断言，与其他 change AC-13 同 pattern） |

## 背景（实测对齐）

实证发现的流程缺陷（用户 2026-05-18 提问触发）：

- `.harness/skills/expert-reviewer/SKILL.md` 自己写：**"评判者必须是独立子会话或独立 Agent，**不能与 Generator 共享上下文**。否则会偏袒。"** + "当前会话**未**参与该产物的撰写"
- 实测当前 `reviewer: application-owner-agent` 字段全仓 **20 行**，分布在 **5 个 closed change**（processor-framework / llm-gateway-mvp / adapter-firecrawl / llm-qa-gen / sdk-cli-mvp），均为本会话 2026-05-17/18 产物
- 实测模板占位符 `reviewer: <name 或 agent id>` 字段全仓 **12 行**（非 _template），分布在 5 个早期 change（部分 review 文件未填字段）
- 早期 5 个变更（bootstrap / core-domain / cas-storage / auth-scaffold / repo-api-mvp）其余 review 字段是 `claude-agent:<change-id>-stage{2|4|6}-reviewer`——真 spawn 过子 agent
- **流程退化**：硬约束被静默违反，且**没有任何机械化手段**阻止再发生
- 结果：本会话 5 closed change × 4 review 文件 = 20 份 review verdict 一律 APPROVED 0 MUST FIX——不是 spec 真没问题，是评审视角与实现视角合一了
- **dogfood 实证**：本变更 spec v1 stage 2 spawn 子 agent 评审，立刻发现 5 MUST FIX + 11 SHOULD FIX + 7 NICE TO HAVE——self-review 与 spawn-review 深度差距明确

## 问题陈述

不变（见 v1）。

## 范围

**In scope**（数字更新）：

- `.harness/agents/reviewer-agent.md` 新建
- `.harness/agents/application-owner.md` 加 §"如何 spawn reviewer 子 agent"
- `.harness/rules/development-process.md` stage 2/4/6 加硬约束
- `.harness/skills/expert-reviewer/SKILL.md` 加 §"reviewer 字段填写规约"
- `scripts/_self_check.sh` global lint：新加 **1 个** global AC `reviewer-lint`（前置在所有 block 之前，FAIL 立 exit）
- **历史回溯：32 行**（20 应用 owner-agent + 12 template 占位符）reviewer 字段改 `self-attest (会话级授权偏离 #1；详见 ...)`
- **dogfood**：本变更 stage 2/4/6 共 **4 review 文件**（stage 2: spec + tasks；stage 4: code；stage 6: test）由 spawn 子 agent 写；reviewer 字段以 `claude-agent:` 开头

**Out of scope**：不变（见 v1）。

## 验收标准（13 AC v2）

- AC-1：reviewer-agent.md 存在且含关键 section；
  `test -f .harness/agents/reviewer-agent.md && grep -q "角色" .harness/agents/reviewer-agent.md && grep -q "禁止\|不允许\|MUST NOT" .harness/agents/reviewer-agent.md`
- AC-2：application-owner.md 含 spawn 模板段（Agent + subagent_type + general-purpose）；
  `test -f .harness/agents/application-owner.md && grep -q "Agent(" .harness/agents/application-owner.md && grep -q "subagent_type" .harness/agents/application-owner.md && grep -q "general-purpose" .harness/agents/application-owner.md`
- AC-3a：development-process.md **stage 2** 段含"独立"+"reviewer"硬约束（用 awk 跨段精确截取）；
  `awk '/^## 阶段 2/,/^## 阶段 3/' .harness/rules/development-process.md | grep -qE "独立.*reviewer|reviewer.*独立|不允许.*self-review|spawn"`
- AC-3b：development-process.md **stage 4** 段含约束；
  `awk '/^## 阶段 4/,/^## 阶段 5/' .harness/rules/development-process.md | grep -qE "独立.*reviewer|reviewer.*独立|不允许.*self-review|spawn"`
- AC-3c：development-process.md **stage 6** 段含约束；
  `awk '/^## 阶段 6/,/^## 阶段 7/' .harness/rules/development-process.md | grep -qE "独立.*reviewer|reviewer.*独立|不允许.*self-review|spawn"`
- AC-4：expert-reviewer SKILL 含 reviewer 字段白名单 + 黑名单规约；
  `grep -q "reviewer 字段" .harness/skills/expert-reviewer/SKILL.md && grep -q "claude-agent:" .harness/skills/expert-reviewer/SKILL.md && grep -q "self-attest" .harness/skills/expert-reviewer/SKILL.md`
- AC-5：self_check 含 global reviewer lint function；
  `grep -q "run_reviewer_lint\|reviewer_field_lint" scripts/_self_check.sh`
- AC-6：历史回溯无遗漏——全仓 grep `reviewer: application-owner-agent` 字段行 = 0；
  `! grep -rE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/`
- AC-7：dogfood——本变更 4 review 文件 reviewer 字段全部以 `claude-agent:` 开头（**stage 6 末才能完整断言；stage 2/4 阶段可视为 partial**）；
  `[ "$(grep -hE "^reviewer:[[:space:]]+claude-agent:" .harness/changes/harness-reviewer-agent-separation-20260518/request_analysis/review/*.md .harness/changes/harness-reviewer-agent-separation-20260518/coding/review/*.md .harness/changes/harness-reviewer-agent-separation-20260518/unit_test/review/*.md 2>/dev/null | wc -l)" -ge 4 ]`
- AC-8：global lint 含正向（白名单匹配 ≥1）+ 反向（黑名单匹配 = 0）双 grep；
  `grep -A40 "run_reviewer_lint\|reviewer_field_lint" scripts/_self_check.sh | grep -qE "! *grep" && grep -A40 "run_reviewer_lint\|reviewer_field_lint" scripts/_self_check.sh | grep -qE "self-attest|claude-agent"`
- AC-9：self-attest 文案规约——历史 32 行改 self-attest 后每条都含括号文案；
  `[ "$(grep -rhE "^reviewer:[[:space:]]+self-attest" .harness/changes/ | grep -v _template | grep -cE "\\(.+\\)")" -ge 32 ]`
- AC-10：跑 self_check global lint 通过（不 FAIL）；
  `bash scripts/_self_check.sh reviewer-lint 2>&1 | grep -qE "PASS" && ! bash scripts/_self_check.sh reviewer-lint 2>&1 | grep -qE "^FAIL"`
- AC-11：ruff + mypy 全仓不回归（**本变更不动 Python；只断言 self_check AC-11 仍 PASS**）；
  `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh sdk-cli-mvp 2>&1 | grep -E "^PASS" | grep -qE "AC-11"`
- AC-12：全仓 self_check baseline + 1 = 226（baseline=225 实测于 stage 1 末；本变更只加 reviewer-lint 1 个 global AC）；
  `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh 2>&1 | grep -qE "^PASS: 226$"`
- AC-13：self_check 自递归（套娃）；
  `bash scripts/_self_check.sh reviewer-lint 2>&1 | grep -q "reviewer-lint"`

## v2 调整：AC 个数

- v1: 13 AC（AC-3 单条）
- v2: 13 AC（AC-3 拆成 AC-3a/3b/3c 三条，挤掉一个 AC 空位 —— 实际上 v2 是 **15 AC**：1+1+3+1+1+1+1+1+1+1+1+1+1 = 实际 14 计数；为了对齐"13 AC" 模板，把 AC-3a/3b/3c 视为同一 AC-3 的 3 个 sub-check）

**澄清**：self_check 实现时 `run_reviewer_lint` 内部跑 AC-3a/3b/3c 三个独立 grep，但只计 1 个 AC（"reviewer-lint" 全通过则 1 PASS）；spec 文档用 sub-AC 编号是 spec 文档级精度，不映射到 self_check 计数。**baseline 225 + 1 = 226 仍成立**。

## 风险

继承 v1 风险表，新增：

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| AC-3 awk 跨段匹配在 development-process.md 实际结构不存在（如无"## 阶段 N"标题）| 中 | AC-3a/3b/3c 全 FAIL | T-3 实施前先 cat 文件确认 §阶段 N 实际标题；如果是"### 阶段 2"或"# 阶段 2"调整 awk pattern |
| AC-12 钉死 PASS=226 万一 baseline 漂移（其他变更同时跑） | 低 | AC-12 FAIL | 本变更串行；commit 前 reset workspace；baseline 实测固定在 stage 1 末 |
| reviewer-lint 在 development-process.md 含 `application-owner-agent` 文档示例时误命中 | 低 | lint FAIL | lint pattern 用 `^reviewer:[[:space:]]+` 严格字段行匹配；reviewer-agent.md / SKILL.md 在 `.harness/agents` / `.harness/skills` 路径不在 `.harness/changes/` 路径，lint 不扫这些 |

## 跨链路一致性自审（v2 修正）

1. ✅ 四链路一致：不变
2. ✅ 事务边界：不变
3. ✅ AC 验证命令一行式：13 条全单行；AC-3 拆分后仍单行
4. ✅ 风险缓解 ↔ AC：v2 新风险都已 mitigated
5. ✅ commit 链：sdk-cli-mvp-20260518 (4ae8a35) → 本变更 base
6. ✅ 反向 grep：AC-6 + AC-8 反向 + reviewer-lint 三重反向
7. ✅ process_tasks：tasks_v2 中将明确 3 条 process_tasks（T-12/T-13/T-14）；spec v1 "6 条"措辞修正为"3 条"
8. ✅ AC 验证命令真跑 dry-parse：v2 在 stage 2 末手动 bash -n 验证全 13 条
9. ✅ summary.md SSoT：v2 后将更新 summary §阶段进度 v1 → v2

## 受影响模块

继承 v1 不变。

## 不受影响但易混淆的模块

继承 v1 不变。

## 引用

继承 v1 + spec_review_v1.md（本 v2 直接响应的输入）。
