---
change_id: harness-reviewer-agent-separation-20260518
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v1
reviewed_at: 2026-05-18T12:50:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 spec）

- [x] 背景写明了为什么现在做（实证 7 change × 3 review = 21 文件违反硬约束）。
- [x] 问题陈述对外部读者可理解（缺独立 agent 文档 / 缺 spawn 模板 / 硬约束未机械化 / 历史误导 / 缺 dogfood）。
- [x] 范围 / 非范围都有，且 In/Out 边界清晰；out-of-scope 各有 follow-up 名占位。
- [ ] **验收标准每条可机械化** —— AC-12 算法自相矛盾（详见 MUST FIX #1）；AC-3 grep 只能拿到 stage 2 段不覆盖 stage 4/6（详见 MUST FIX #2）。
- [x] 风险有缓解措施，且与 AC 显式映射（spec §跨链路 第 4 条）。
- [x] 没有把已有架构当新提案 —— 本变更是 meta-change（改 harness 流程本身），不动 dataplat 代码。
- [x] 没有遗留待澄清问题（spec §跨链路 9 条自审已逐条勾，候选 #12 提出但同变更解决）。

## 跨链路一致性检查（SKILL 9 条 + spec 自审）

- [x] 1 四链路一致：reviewer-agent.md ↔ owner spawn 模板 ↔ SKILL 字段规约 ↔ self_check lint 串联到 AC-1/2/4/5。
- [x] 2 事务边界：本变更纯文档 + shell；无 DB。
- [x] 3 AC 验证命令一行式：13 条全 bash 单行。
- [ ] **4 风险缓解 ↔ AC**：风险表"AC 验证命令 dry-parse"对应 SKILL #8，但 spec 未对每条 AC bash 命令做 `bash -n` 实测，AC-12 数学算法错误正是这一缺漏的表现（详见 MUST FIX #1）。
- [x] 5 commit 链：base 指向 sdk-cli-mvp-20260518 (4ae8a35)，summary.md frontmatter 已声明。
- [ ] **6 反向 grep 安全性**：AC-6 反向 grep 模式有死角 —— 若 T-1 reviewer-agent.md 在文档示例段写 `reviewer: application-owner-agent`（作为反例），即便不在字段行位置，因 `grep -rE` 是按行匹配，只要那行以 `^reviewer:[[:space:]]+application-owner-agent` 起首即命中。spec §风险表第 4 行说"反向 grep pattern 加 `^reviewer:[[:space:]]+` 前缀严格匹配字段行"是缓解，但**该缓解只在风险表声明，未落到 AC-6 的实际命令里**——AC-6 命令已写对 `^reviewer:[[:space:]]+ application-owner-agent`，可放心。复核通过。
- [x] 7 process_tasks 6 条：T-12/13/14 占位（仅 3 条，spec 写"6 条"是笔误但不阻塞）。
- [ ] **8 AC 验证命令真跑 dry-parse**：AC-7 dogfood 命令 `grep -hE "^reviewer:[[:space:]]+claude-agent:" ... | wc -l` —— 若 stage 4/6 文件不存在（stage 2 评审时这是事实），`grep` 会 stderr 报错但 stdout 仍输出本 stage 2 的 2 行，wc -l = 2，断言 `-ge 3` 会 FAIL。AC-7 实际是"全 3 stage 完成后才能验"的复合 AC，spec 未明示"AC-7 仅在 stage 6 dogfood 跑完后断言"。详见 SHOULD FIX #1。
- [x] 9 summary.md SSoT：frontmatter 已填，占位符 grep = 0。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §验收标准 AC-12 + §跨链路 第 4 条 | **算法自相矛盾**：AC-12 写 `旧 225 + 本块 13 = 238`，但 (a) 实测当前 baseline 是 `PASS: 211`（FAIL=14 因环境）；理想态全 PASS 也是 225（15 change × 13 + 含 bootstrap 17 + core-domain 17 + auth 17 + cas 17 = 多算）—— "225" 数字未给推导；(b) tasks.md T-11 自己写 "暂时**不**为本变更建一个 13 AC block；本变更的 AC 在 spec 阶段通过 global lint + 阶段产物覆盖"——既然不建 13 AC block，AC-12 `+ 本块 13` 无来源；(c) tasks T-11 自己写"期望全仓 PASS: 225（原 16 block）+ lint 计入新 1 个 → 226+；具体数等实测"，与 spec AC-12 的 238 直接打架。 | 三选一：① AC-12 改为 `bash scripts/_self_check.sh 2>&1 \| tail -3 \| grep -qE "PASS: [0-9]+"`（不钉死具体数，只断言能跑出 PASS）；② 重新对账：实测 baseline 后给精确推导（含 reviewer-lint 计入 1 个 AC 时为 baseline+1）；③ 显式声明本变更**加 reviewer-lint 1 个全局 AC**，把 AC-12 改为 `+ 1 = baseline_plus_1`。务必同步改 tasks T-11 的"226+"措辞与 spec 一致。 |
| 2 | spec.md §验收标准 AC-3 | **AC-3 grep 覆盖不全**：spec 说 stage 2/4/6 都要加硬约束（T-3），但 AC-3 命令 `grep -A30 "阶段 2" ... \| grep -qE "独立.*reviewer\|reviewer.*独立\|不允许.*self-review"` 只校验 stage 2 段。实测 `grep -A30 "阶段 2"` 命中 2 处（行 36 stage 2 标题 + 行 53 stage 3 内容里"阶段 2 verdict = APPROVED"），输出含 stage 3 部分但 stage 4/6 完全不在窗口里。若 T-3 只在 stage 2 加约束、stage 4/6 漏改，AC-3 仍 PASS——**这是 AC 没法捕捉的实现漏洞**。 | 拆成 AC-3a / AC-3b / AC-3c 三条，每条 `grep -A30 "阶段 N · "` 分别管 stage 2/4/6；或用 `awk '/## 阶段 [246]/,/^## /' ... \| grep -qE ...`（更严但 awk 写法要测）；或最干脆：要求每个 stage 段都有完整原文（spec 引用），让 reviewer 一眼对比。 |
| 3 | spec.md §背景 + §范围 + 风险 #3 + AC-6 数量 | **历史回溯数对不上**：背景写"本会话 7 个变更...全部 reviewer=application-owner-agent"，范围写"12 个历史 closed change（含本会话 7 个 + 模板字段未填的 14 个 review 文件总计涉及）"。实测：(a) `reviewer: application-owner-agent` 字段当前共 **20 行**，分布在 **5 个** closed change（adapter-firecrawl / llm-gateway-mvp / llm-qa-gen / processor-framework / sdk-cli-mvp，每个 4 个 review 文件）——不是 7 也不是 12；(b) `reviewer: <name 或 agent id>` 字段共 **18 行**（含 _template/ 4 行），非 template 共 14 行，分布在 6 个 change；(c) self-attest 已 ≥1 行的有 `core-domain-model` 2 行。"12 个 change"与"7 个会话"两个数都与实测不符。 | 重数实测：5 个 closed × 4 review = 20 行 application-owner-agent；6 个 change × ~2-4 review = 14 行 template 占位符；总计需回溯 ~34 行字段。改 spec §背景 / §范围 / 风险 #3 / AC-9 的"≥12"为实测后准确数（或改为 `-ge $(...)` 用 grep 动态算）。AC-6 反向 grep 不变（只要回溯完整就 = 0）。AC-9 改成"原 application-owner-agent 行数 + 模板占位符行数总和应全部带括号文案 self-attest"。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md AC-7 + tasks T-7/T-8/T-9 | AC-7 是"3 review 文件 reviewer 字段以 claude-agent: 开头 ≥3"复合断言，但 stage 2 评审时只能产 2 文件（spec_review + tasks_review），stage 4/6 文件 grep 时 stderr "No such file or directory" 输出非空。AC-7 实际只有 stage 6 完成后才完整可验。spec 未明示此时序约束。 | AC-7 加注："仅在 stage 6 dogfood 完成后断言；stage 2/4 阶段可视为 partial PASS（≥1 / ≥2）"；或拆为 AC-7a (stage 2 ≥2) / AC-7b (stage 4 ≥3) / AC-7c (stage 6 ≥3) 三条。 |
| 2 | spec.md §跨链路 第 7 条 | 写"process_tasks 6 条：T-9~T-14 占位"但 tasks.md 里实际 process_tasks 只 3 条（T-12/T-13/T-14）；T-7/T-8/T-9 是 dogfood 实质任务非 process_tasks。 | 修正为"process_tasks 3 条：T-12/T-13/T-14"或补 3 条 process_tasks（如 spec-review / code-review / test-review 这 3 个 stage 2/4/6 的 process 占位）。 |
| 3 | spec.md AC-13 | "AC-13：self_check 自递归" —— 命令缺失。其它 AC 都有 bash 命令，AC-13 单行空。 | 补 `true` 或 `bash scripts/_self_check.sh reviewer-lint`（套娃断言）。 |
| 4 | spec.md AC-11 | `uv run ruff check apps/api packages/core packages/sdk-py worker/src && uv run mypy ...` —— 实测当前 mypy 在 apps/api/dataplat_api/jobs 有现存的 mypy/ruff 失败（baseline self_check 显示 AC-11 FAIL 多次）。本变更不动 Python，"不回归"应该是"不引入新错误"而非"全 PASS"。 | 措辞改"本变更未引入新 ruff/mypy 错误（对比本变更前后报告 diff）"，或允许 AC-11 用 baseline failure 白名单。 |
| 5 | spec.md §风险表 第 7 行 | "AC 验证命令 dry-parse 全过（SKILL #8）" —— 缓解只写"用 shell -n 检"，但 spec 自身未给 dry-parse 证据（实测发现 AC-12 算法本身就错）。 | T-0/T-1 之前补一步"spec stage 1 末做 13 条 AC bash 命令 dry-parse"作为产物（可放 summary §当前阻塞下或 spec 末尾）。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §背景 | "21 份 review 文件（7 change × 3 阶段）" —— 每 change 4 个 review（spec + tasks + code + test）非 3 个，实际 7×4=28；本变更命中 20 是因为 5 个 closed × 4 + 0；数字描述不严谨。 | 改"5 closed × 4 review = 20 文件"或类似。 |
| 2 | spec.md §范围 in-scope 末段 | "本变更 stage 2/4/6 review 文件由 spawn 的 general-purpose 子 agent 写入" —— 实际 stage 2 review 文件即本 spec_review_v1.md + tasks_review_v1.md 共 2 文件。原文措辞"3 个 review 文件"暗示 1 个 review 文件 / stage，但 stage 2 是 2 文件，stage 4 是 1 文件，stage 6 是 1 文件，总 4 文件。 | 改"4 review 文件由 spawn 的子 agent 写入"；AC-7 数量同步检查（"≥3"应改"≥4"，但已是 MUST FIX #3 涉及范围）。 |
| 3 | spec.md §跨链路 第 7 条 "process_tasks 6 条" | 见 SHOULD FIX #2。 | 同。 |
| 4 | spec.md 候选 #12 | "若 self_check 守门通过 + dogfood 通过，候选直接落 SKILL（第 1 次实证就落，因为这是 SKILL 自己已写的硬约束，违反者已累积 7 次）" —— 表述清楚，但缺"落 SKILL 哪里、由谁动手、stage 几落"的执行细节。 | 补 follow-up：T-10 后增加 "若本变更通过，请把候选 #12 写入 `.harness/skills/request-analysis/SKILL.md` § 9 条跨链路自审"。 |

## Verdict

**REVISION REQUIRED**

理由：3 条 MUST FIX 未关闭，其中 AC-12 算法错误是 spec 文档 ↔ tasks 文档之间显式自相矛盾，AC-3 grep 漏覆盖 stage 4/6 是 spec → 实现的"AC 不可机械化判定全 spec 范围"。背景/范围数字与实证差距大也是质量信号问题。

## 后续指引

Generator 修 spec_v2 后请自检：

1. AC-12 算法：用 `bash scripts/_self_check.sh 2>&1 | tail -3` 拿到实际 baseline，把 v2 AC-12 的数字基于该 baseline 推导（不要用 v1 写的 225/238 这两个数）；同时 tasks T-11 措辞与 spec AC-12 串成一致表述。
2. AC-3 拆分：用三组 `awk` 或 `grep -A30` 分别校验 stage 2/4/6 段含目标 keyword；本地手动跑一次，看 v2 spec 改完 development-process.md 后是否 3 处都能 PASS。
3. 历史数字对齐：跑 `grep -rE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/ | wc -l` 实测当前数（应为 20），把 spec §背景 / §范围 / AC-6 / AC-9 数字按实测调整。
4. process_tasks / AC-7 时序：明确 stage 2 评 ≥2 文件 / stage 4 评 ≥3 文件 / stage 6 评 ≥4 文件的 partial AC，或 AC-7 改 stage 6 末才断言。
5. 重提 spec_v2 + tasks_v2 后开 `spec_review_v2.md` / `tasks_review_v2.md`（不要覆盖 v1）。
