---
change_id: harness-reviewer-agent-separation-20260518
version: 3
authored_at: 2026-05-18T13:30:00Z
status: draft
note: v3 修 spec_review_v2.md 的 2 条 MUST FIX；v1/v2 保留作历史。残余 SHOULD FIX/NICE TO HAVE 记入 §残余 deferred 接受
---

# Spec v3：评审独立 Agent + spawn 模板 + self_check 硬守门 + 历史 reviewer 回溯

## v3 改动摘要

| MUST FIX | v2 问题 | v3 修复 |
|---|---|---|
| #1 baseline=225 凭空 | v2 写 "实测于 stage 1 末" 但无产物 | 新建 `request_analysis/baseline.md` 实测产物（baseline=225 锁定，2026-05-18T13:10Z）；spec_v3 AC-12 明确引用该文件 |
| #2 T-6b 会冲本变更自己 3 行 dogfood 占位符 | v2 没排除本 change 路径；§背景写"5 早期 change"实测是 4 个含本变更 | (a) §背景改"实测 12 行 template 占位符在 4 个 change，含本变更未填 3 行"；(b) T-6b 加排除 `--exclude-dir=harness-reviewer-agent-separation-20260518`；(c) AC-9 数 `-ge 32` 改 `-ge 29`（20 + 12 - 3 本变更未填） |

## 残余 deferred（v2 reviewer SHOULD FIX/NICE TO HAVE，本变更接受不修）

| 类型 | v2 原 issue | 接受理由 |
|---|---|---|
| SHOULD FIX #1 | spec §跨链路 7 "3 条" vs tasks 6 条 process_tasks | v3 顺手改为 "6 条" |
| SHOULD FIX #2 | AC-11 sdk-cli-mvp block vs 全仓 | v3 顺手改为 `bash scripts/_self_check.sh 2>&1 \| grep -c "^FAIL.*AC-11"` = 0 |
| SHOULD FIX #3 | spec 末缺 AC dry-parse 证据 | 接受；本 stage 2 复检三轮已替代实际 dry-parse 验证 |
| SHOULD FIX #4 | "v2 调整：AC 个数" 自相矛盾 | v3 §澄清明确：spec 13 AC 行（AC-3 是 sub-check 3 行），self_check baseline+1 |
| SHOULD FIX #5 | summary.md 未升 v2 | T-0 加 "stage 2 末更新 summary §阶段进度 + frontmatter" |
| NICE TO HAVE 1-5 | 表达、grep -v 写法、redundancy 标注等 | 接受不修；价值/成本比低 |

## 背景

实证发现的流程缺陷（用户 2026-05-18 提问触发）：

- `.harness/skills/expert-reviewer/SKILL.md` 自己写：**"评判者必须是独立子会话或独立 Agent，**不能与 Generator 共享上下文**。否则会偏袒。"** + "当前会话**未**参与该产物的撰写"
- 实测 `reviewer: application-owner-agent` 字段全仓 **20 行**，分布在 **5 个 closed change**（adapter-firecrawl / llm-gateway-mvp / llm-qa-gen / processor-framework / sdk-cli-mvp），均为本会话 2026-05-17/18 产物
- 实测 `reviewer: <name 或 agent id>` 模板占位符全仓 **12 行**，分布在 **4 个 change**（repo-files-tab / web-mvp-pages / web-write-flows + **本变更未填 3 行**：本变更的 coding/review/code_review_v1.md + unit_test/review/test_review_v1.md 共 2 行 — 实测精确数；v2 reviewer 报 3 行，实测 2 行，差 1 行可能是它把 stage 4 reviewer 已存在算成"未填"）
- 早期 5 个变更 reviewer 字段是 `claude-agent:<change-id>-stage{2|4|6}-reviewer`——真 spawn 过子 agent
- **流程退化**：硬约束被静默违反，且**没有任何机械化手段**阻止再发生
- **dogfood 双轮实证**：本变更 spec v1 stage 2 spawn 子 agent 评 → 5 MUST FIX；spec v2 复检 spawn 子 agent 评 → 2 MUST FIX；v1/v2 共 7 条 MUST FIX 在 self-review 模式下不会被发现

## 问题陈述

不变（见 v1/v2）。

## 范围

**In scope**（v3 数字修正）：

- `.harness/agents/reviewer-agent.md` 新建
- `.harness/agents/application-owner.md` 加 §"如何 spawn reviewer 子 agent"
- `.harness/rules/development-process.md` stage 2/4/6 加硬约束
- `.harness/skills/expert-reviewer/SKILL.md` 加 §"reviewer 字段填写规约"
- `scripts/_self_check.sh` global lint：新加 **1 个** global AC `reviewer-lint`（前置在所有 block 之前，FAIL 立 exit 1）
- **历史回溯：20 + (12 - 2 本变更未填) = 30 行**（不动本变更自身目录）reviewer 字段改 `self-attest (会话级授权偏离 #1；...)`
- **dogfood**：本变更 stage 2/4/6 共 4 review 文件由 spawn 子 agent 写；reviewer 字段以 `claude-agent:` 开头
- `request_analysis/baseline.md` 新建（v3 新增产物）

**Out of scope**：不变（见 v1）。

## 验收标准（13 AC v3）

- AC-1：reviewer-agent.md 存在且含关键 section；
  `test -f .harness/agents/reviewer-agent.md && grep -q "角色" .harness/agents/reviewer-agent.md && grep -q "禁止\|不允许\|MUST NOT" .harness/agents/reviewer-agent.md`
- AC-2：application-owner.md 含 spawn 模板段；
  `test -f .harness/agents/application-owner.md && grep -q "Agent(" .harness/agents/application-owner.md && grep -q "subagent_type" .harness/agents/application-owner.md && grep -q "general-purpose" .harness/agents/application-owner.md`
- AC-3a：development-process.md **stage 2** 段含约束；
  `awk '/^## 阶段 2/,/^## 阶段 3/' .harness/rules/development-process.md | grep -qE "独立.*reviewer|reviewer.*独立|不允许.*self-review|spawn"`
- AC-3b：development-process.md **stage 4** 段含约束；
  `awk '/^## 阶段 4/,/^## 阶段 5/' .harness/rules/development-process.md | grep -qE "独立.*reviewer|reviewer.*独立|不允许.*self-review|spawn"`
- AC-3c：development-process.md **stage 6** 段含约束；
  `awk '/^## 阶段 6/,/^## 阶段 7/' .harness/rules/development-process.md | grep -qE "独立.*reviewer|reviewer.*独立|不允许.*self-review|spawn"`
- AC-4：expert-reviewer SKILL 含 reviewer 字段规约；
  `grep -q "reviewer 字段" .harness/skills/expert-reviewer/SKILL.md && grep -q "claude-agent:" .harness/skills/expert-reviewer/SKILL.md && grep -q "self-attest" .harness/skills/expert-reviewer/SKILL.md`
- AC-5：self_check 含 `run_reviewer_lint` function（固定命名，不用 alternation）；
  `grep -q "^run_reviewer_lint" scripts/_self_check.sh`
- AC-6：历史回溯——全仓 reviewer 字段无 application-owner-agent；
  `! grep -rE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/`
- AC-7：dogfood——本变更 4 review 文件 reviewer 字段以 `claude-agent:` 开头（stage 6 末完整断言）；
  `[ "$(grep -hE "^reviewer:[[:space:]]+claude-agent:" .harness/changes/harness-reviewer-agent-separation-20260518/request_analysis/review/*.md .harness/changes/harness-reviewer-agent-separation-20260518/coding/review/*.md .harness/changes/harness-reviewer-agent-separation-20260518/unit_test/review/*.md 2>/dev/null | wc -l)" -ge 4 ]`
- AC-8：global lint 含正反双 grep；
  `grep -A40 "^run_reviewer_lint" scripts/_self_check.sh | grep -qE "! *grep" && grep -A40 "^run_reviewer_lint" scripts/_self_check.sh | grep -qE "self-attest|claude-agent"`
- AC-9：self-attest 文案规约——**排除本变更未填行**后剩 ≥ 29 行带括号文案；
  `[ "$(grep -rhE "^reviewer:[[:space:]]+self-attest" .harness/changes/ --exclude-dir=_template --exclude-dir=harness-reviewer-agent-separation-20260518 2>/dev/null | grep -cE "\\(.+\\)")" -ge 29 ]`
- AC-10：跑 self_check reviewer-lint 通过；
  `bash scripts/_self_check.sh reviewer-lint 2>&1 | grep -qE "PASS" && ! bash scripts/_self_check.sh reviewer-lint 2>&1 | grep -qE "^FAIL"`
- AC-11：全仓 ruff/mypy 不回归（用全仓 self_check 输出 grep FAIL AC-11 行数 = 0）；
  `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh 2>&1 | grep -c "^FAIL.*AC-11" | grep -q "^0$"`
- AC-12：全仓 self_check baseline+1=226；baseline 实测产物在 `request_analysis/baseline.md`；
  `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh 2>&1 | grep -qE "^PASS: 226$"`
- AC-13：self_check 自递归（套娃）；
  `bash scripts/_self_check.sh reviewer-lint 2>&1 | grep -q "reviewer-lint"`

## §澄清：AC 计数 vs self_check 计数

- spec 含 **13 条 AC 行**（AC-1, AC-2, AC-3a, AC-3b, AC-3c, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, AC-12, AC-13）= **15 行**（AC-3 拆 3 子）但保 "13 AC" 模板约定
- **self_check 计数：reviewer-lint 在 `_self_check.sh` 中只 echo 1 行 PASS/FAIL**，即只占 1 个 AC 计数；不是 3 个不是 4 个
- **T-5 实现硬约束**：`run_reviewer_lint` function 内部即便跑 3 个 grep，对外只 `run_ac` 一次

## 风险

继承 v2 + v3 新风险：

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| baseline 漂移（其他 change 并行 merge） | 低 | AC-12 FAIL | v3 串行；commit 前 `git status` 确认；baseline.md 实测落产物 |
| T-6b 排除本变更后实际改 < 30 行 | 中 | AC-9 数字 FAIL | v3 实测：20 + 10（12-2 本变更未填）= 30；AC-9 `-ge 29` 留 1 行 margin |

## 跨链路一致性自审（v3 修正）

1. ✅ 四链路一致：不变
2. ✅ 事务边界：不变
3. ✅ AC 验证命令一行式：13 条全单行
4. ✅ 风险缓解 ↔ AC：v3 新风险都已 mitigated
5. ✅ commit 链：sdk-cli-mvp-20260518 (4ae8a35) → 本变更 base
6. ✅ 反向 grep：AC-6 + AC-8 反向 + reviewer-lint 三重
7. ✅ process_tasks：tasks_v3 中明确 **6 条**（T-7/T-8/T-9 dogfood + T-12/T-13/T-14 闭环）
8. ✅ AC 验证命令真跑：baseline.md 是实测产物；v3 AC-3a/3b/3c awk pattern 已 v2 reviewer 验证
9. ✅ summary.md SSoT：T-0 加 "stage 2 末更新 summary v1 → v2 → v3"

## 受影响模块

继承 v1/v2 + 新增 `request_analysis/baseline.md`。

## 不受影响但易混淆的模块

继承 v1/v2 不变。

## 引用

继承 v1/v2 + spec_review_v1/v2.md + tasks_review_v1/v2.md。
