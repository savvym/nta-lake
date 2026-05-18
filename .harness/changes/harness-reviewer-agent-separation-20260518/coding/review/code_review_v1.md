---
change_id: harness-reviewer-agent-separation-20260518
target: coding/main（实际 git diff working-tree）
target_head: working-tree
review_version: 1
reviewer: claude-agent:harness-reviewer-agent-separation-stage4-reviewer-v1
reviewed_at: 2026-05-18T04:50:34Z
verdict: REVISION REQUIRED
---

# Code Review v1

## 范围与作者声明对照

coding_report v1 §改动文件清单声明：reviewer-agent.md new + 4 文件 edit + 30 行 sed 历史回溯（5 closed change 20 行 application-owner-agent + 4 change 10 行 template 占位符），合计本变更目录 + 6 类外部文件 ≈ "17 个文件改动"。

git status 实际改动（去除 `??` 新加目录）：

| 类别 | 文件 | 是否声明 |
|---|---|---|
| 本变更新建 | `.harness/agents/reviewer-agent.md` | 是 |
| edit | `.harness/agents/application-owner.md` | 是 |
| edit | `.harness/rules/development-process.md` | 是 |
| edit | `.harness/skills/expert-reviewer/SKILL.md` | 是 |
| edit | `scripts/_self_check.sh` | 是 |
| 历史回溯 | `.harness/changes/{adapter-firecrawl,llm-gateway-mvp,llm-qa-gen,processor-framework,sdk-cli-mvp}/(coding,request_analysis,unit_test)/review/*.md` 20 行 | 是（T-6a） |
| 历史回溯 | `.harness/changes/{repo-files-tab,web-mvp-pages,web-write-flows,sdk-cli-mvp}/.../review/*.md` 10 行 | 是（T-6b） |
| **未声明** | `Makefile` 1 行（`pnpm --filter web dev` → `pnpm --filter web dev --host`） | **否** |
| 本变更新建产物 | `.harness/changes/harness-reviewer-agent-separation-20260518/**` | 不在 stage 3 改动范围（spec 已说明） |

**MUST FIX #1**：Makefile 改动未在 coding_report 声明，与 spec §范围（in scope 列表）无关，违反 development-process.md 阶段 3 Quality Gate "改动文件清单与 tasks.md 任务对得上"。要么把它从 working-tree stash 出去（不入本 change commit），要么在 coding_report 显式声明并解释（开 follow-up 或归入 dev-quality 类 NICE 改动）。

## AC ↔ 实现复检（13 AC 逐条 PASS/FAIL）

实测 spec_v3 §13 AC：

| AC | 期望 | 实测 | 结论 |
|---|---|---|---|
| AC-1 | reviewer-agent.md 存在 + "角色" + 禁止/不允许/MUST NOT | grep 全命中 | PASS |
| AC-2 | owner.md 含 `Agent(` + subagent_type + general-purpose | 全命中（§7.5） | PASS |
| AC-3a | dev-process stage 2 段含独立 reviewer / 不许 self-review / spawn | 命中 | PASS |
| AC-3b | stage 4 同 | 命中 | PASS |
| AC-3c | stage 6 同 | 命中 | PASS |
| AC-4 | SKILL 含 "reviewer 字段" + claude-agent: + self-attest | 全命中（§reviewer 字段填写规约） | PASS |
| AC-5 | `^run_reviewer_lint` 函数存在 | 命中 | PASS |
| AC-6 | 全仓无 `reviewer: application-owner-agent` 行 | 命中 | PASS |
| AC-7 | 本变更 review 目录 reviewer 字段以 `claude-agent:` 起头 ≥4 | 实测 7（spec_review_v1/v2/v3 + tasks_review_v1/v2/v3 + 本 code_review_v1） | PASS |
| AC-8 | `run_reviewer_lint` 后 40 行含 `! *grep` 且含 `self-attest`/`claude-agent` | **`! grep` 不命中**（实现用 `if grep ...; ... exit 1` 形态等价，但 spec AC 文本明确要求 `! *grep` regex 匹配） | **FAIL** |
| AC-9 | 30 行 self-attest 含 ASCII `(.+)` 文案 ≥29 | 32 PASS（34 总；2 行全角括号「（…）」不计入） | PASS |
| AC-10 | reviewer-lint 跑 PASS、无 `^FAIL` | 实测 PASS=1 / FAIL=0 | PASS |
| AC-11 | 全仓 self_check 输出 `^FAIL.*AC-11` 行数 = 0 | PASS=226 / FAIL=0 | PASS |
| AC-12 | 全仓 `^PASS: 226$` | 实测 `PASS: 226` ✅ | PASS |
| AC-13 | `bash scripts/_self_check.sh reviewer-lint` 输出含 "reviewer-lint" | 输出含 `=== global :: reviewer-lint ===` | PASS |

**结论**：13 AC 中 12 PASS，1 FAIL（AC-8）。AC-8 失败原因：spec_v3 AC-8 `grep -A40 "^run_reviewer_lint" scripts/_self_check.sh | grep -qE "! *grep"` 实测无匹配，因为 generator 把反向 grep 写成 `if grep -rE "..." >/dev/null 2>&1; then ... exit 1; fi` 形态（语义等价但 regex 不匹配 `! grep`）。

## 正确性 / 安全 / 架构

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | working-tree Makefile:35 | 改动未在 coding_report 声明，违反 stage 3 Quality Gate "改动 ↔ tasks 对得上" | 从本 change commit 剔除（git restore --staged + checkout），或在 coding_report 显式声明并归入 follow-up；并复跑全仓 self_check 确认不影响 |
| 2 | scripts/_self_check.sh:1147-1158 vs spec_v3 AC-8 | 实现用 `if grep ...; exit 1` 形态写反向断言，spec AC-8 grep regex `! *grep` 不匹配 → AC-8 FAIL | 二选一：(a) 把 `run_reviewer_lint` 内反向 #1/#2 改为 `! grep -rE ... \|\| { ...; exit 1; }` 形态，让 `! grep` 字面出现；或 (b) 在 spec_v4 修 AC-8 regex 为 `! *grep\|if .*grep`（同时确保 AC-8 仍能验证反向语义存在） |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | scripts/_self_check.sh:1161 白名单 regex `(claude\|self-attest)` 不强制 ASCII 半角 `(` 括号 | 实测仓内 2 行用全角「（…）」过 lint，但 AC-9 ASCII `\(.+\)` 不计入；守门对全角失效，违反 owner.md §7.5 "所有 self-attest 必须含括号文案"（隐式 ASCII） | 把白名单 regex 改为 `(claude\|self-attest \()` 强制 ASCII `(`；或显式在 SKILL §reviewer 字段填写规约 注明括号字符集；并把现存 2 行全角改 ASCII |
| 2 | coding_report §偏离段 "白名单从 `claude-agent:` 扩到 `claude`" | regex `(claude\|self-attest)` 实际放过 `reviewer: claude`（裸 claude，无 hyphen）；但仓内当前无此值 — 是潜在退化窗口 | 把 regex 收紧为 `(claude-\|self-attest \()`（强制 hyphen 后缀），保历史 `claude-agent:` / `claude-stage{N}-reviewer` 都过，又拦裸 claude |
| 3 | coding_report §改动文件清单 "30 行 sed in-place" 表述 | 实测 20 + 10 = 30 历史回溯行（spec_v3 §背景与 AC-9 数字一致），但 §改动文件清单写 "review 字段回溯 sed in-place" 缺具体行号/文件列表，违反审计性 | 在 coding_report 列实际触及文件列表（git status 输出 31 行 `M .harness/changes/...`）和每个文件触及行号 |
| 4 | coding_report 未列 Makefile | 与 MUST FIX #1 同因 | 同上 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | scripts/_self_check.sh:1143 run_ac 描述 "（反向×2 + 白名单）" | 内部其实是 3 个 grep 顺序检查，描述清晰但若以后扩到 4 grep 描述会过时 | 改为 "（反向 + 白名单 + 配额）" 或不写具体计数 |
| 2 | reviewer-agent.md §9 历史与版本演进 v0.2-0.4 是 follow-up 占位 | 价值高但本变更未开 follow-up change 链接 | 在 summary.md 末段 link 到未来 change-id 模式或开占位 changes/ 目录 |

## 风格 / 性能 / 可观测性

- scripts/_self_check.sh:1144 `run_ac` 内的 `bash -c '...'` 嵌套单引号 + `set -e` 风格合规；`coding-style.md` 无 shell 章节，sanity OK
- reviewer-agent.md 文档风格中文为主、英文 schema/字段值保留（符合 user feedback_doc_language 偏好）
- self_check fail-fast `if [ "$FAIL" -gt 0 ]; then exit 1; fi`：当且仅当 reviewer-lint 自己 FAIL 才 exit；不影响后续 block 累计计数，对外 1 个 run_ac → AC-12 baseline+1=226 数字闭环正确

## 跨改动观察

- **dogfood 闭环**：spec/tasks v1→v2→v3 + spec_review/tasks_review v1→v3 共 6 文件，reviewer 字段全部 `claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v{M}`，符合命名约定；本 stage 4 reviewer 字段同
- **历史回溯安全性**：git diff 抽查 adapter-firecrawl/code_review_v1.md 仅替换 `reviewer:` 行级，未误伤正文（review 正文中 application-owner-agent 字面未出现于 reviewer: 行的 grep 实测干净）
- **AC-12 baseline 漂移风险**：实测 226 = 225 baseline + 1 reviewer-lint；若并行 change 引入新 AC 行此数字会过期，但 spec_v3 已显式串行 + baseline.md 落产物

## Deferred SHOULD FIX

若 verdict 最终 APPROVED 而 SHOULD FIX #1/#2/#3 不修，必须在 summary.md `Deferred` 段列入并指向跟进 change-id（建议 `harness-reviewer-lint-tighten-<yyyymmdd>`）。

## Verdict

**REVISION REQUIRED**

理由：2 条 MUST FIX 未关闭。Makefile 未声明（MUST FIX #1）违反 stage 3 QG，AC-8 FAIL（MUST FIX #2）违反 spec ↔ 实现一致性、spec_v3 §13 AC 中有 1 条不通过。

## 后续指引

generator 修 v2：

1. 处理 Makefile：要么 `git checkout Makefile` 剔除（推荐，与本 change 无关），要么 coding_report_v2 显式声明 + tasks_v3 加补 task + 跑全仓 self_check 验证不回归
2. 处理 AC-8：option (a) 修 self_check.sh 让 `! grep` 字面出现；option (b) 修 spec_v4 + 重 spawn stage2 reviewer v4 评 spec_v4 → 修 AC-8 regex；推荐 (a) 成本更低
3. （强烈建议同改）SHOULD FIX #1 全角括号白名单漏洞：改 regex `(claude\|self-attest \()` + 把现存 2 行全角改 ASCII + 重跑全仓 self_check
4. 复检命令：
   - `git status --short | grep -v "^??"` ↔ coding_report_v2 §改动清单逐行对账
   - `bash -c 'grep -A40 "^run_reviewer_lint" scripts/_self_check.sh | grep -qE "! *grep"'` ↔ AC-8 PASS
   - `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh 2>&1 | grep -qE "^PASS: 226$"` ↔ AC-12 PASS
5. 提交 v2 后 spawn code_review_v2 reviewer 子 agent（reviewer 字段 `claude-agent:harness-reviewer-agent-separation-stage4-reviewer-v2`）；本文件保留作历史
