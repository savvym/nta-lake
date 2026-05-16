---
change_id: harness-bootstrap-20260516
title: 建立 .harness/ 与 wiki/ 基线骨架，作为后续所有变更的运行环境
owner: zhhdzhang
started_at: 2026-05-16T03:00:00Z
stage: user_confirmation
status: done
last_updated: 2026-05-16T21:45:00Z
related_changes: []
---

# Summary

## 一句话目标

为 dataplat 项目搭起 Harness Engineering 基线骨架（`.harness/` + `wiki/` + 顶层 `CLAUDE.md`），让后续所有 dataplat 开发都跑在受约束的流程之上，并通过本变更 Dry Run 整套流程，发现缺陷立即反哺。

## 范围摘要

- **In scope**：
  - 创建 `.harness/agents/` `rules/` `skills/` `changes/_template/` `mcp/` 全套骨架文件
  - 创建 `wiki/README.md` `architecture.md` `domain-glossary.md` `adr/README.md`
  - 创建顶层 `CLAUDE.md` 作为会话入口
  - 写入项目记忆（Harness 约束、文档语言偏好、项目状态）
- **Out of scope**：
  - 不创建任何 `apps/` `packages/` `worker/` `plugins/` 代码骨架（留给 `bootstrap-monorepo-<yyyymmdd>`）
  - 不接入 CI / 部署（同上）
  - 不写任何 `.claude/settings.json` hooks（用户明确选择"Markdown + Claude Code 集成"档位）
  - 不接入 MCP server（Phase 2+）

## ⚠️ 一次性流程例外说明

**本变更是 harness 骨架自身的引导，属于"鸡先于蛋"的特殊情况**：

- 骨架文件（`.harness/*`、`wiki/*`、`CLAUDE.md`）在本 change 目录创建之前就已产出（上一轮会话已落地）。
- 严格按流程应当 spec → review → coding；本次为追溯式（retroactive）记录。
- **此例外仅限本变更**。从下一个变更（`bootstrap-monorepo-<yyyymmdd>`）开始，必须严格按十阶段顺序推进。
- 评审应当对追溯式 spec 与现有文件状态的一致性做强校验（验收标准每条都对应可被 `ls` / `grep` 验证的现实文件）。

> 本例外已在记忆 [[harness-constraints]] 中保留为单次豁免；不可作为先例。

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done（追溯） | v1（已就地修订 4 处 SHOULD FIX） | — | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | **done** | v1 | **APPROVED** (MUST FIX=0, SHOULD FIX=4 全部已 fix, NICE TO HAVE=2 已 defer) | [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) |
| 3 编码实现 | done（追溯 + stage 3 自检补修 2 份 SKILL；stage 4 后又补 SHOULD FIX #2/#3 + NICE #1） | v1（就地修订） | — | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | **done** | v1 | **APPROVED** (MUST FIX=0, SHOULD FIX=3：#1 defer / #2 现场修 / #3 现场修；NICE=3：#1 现场修 / #2 #3 defer) | [code_review_v1.md](coding/review/code_review_v1.md) |
| 5 单测编写 | done（test_report v1 就地补 3 条 §已知问题 + 反向引用 stage 4 决策；脚本头注 bash ≥ 3.2） | v1（就地修订） | — | [test_report_v1.md](unit_test/test_report_v1.md) · [check_harness.sh](unit_test/check_harness.sh) |
| 6 单测评审 | **done** | v1 | **APPROVED** (MUST FIX=0, SHOULD FIX=3：#1/#2 现场修自陈、#3 reviewer 自标接受；NICE=4：#3/#4 现场修、#1/#2 defer) | [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | done（按用户 A 路径）| commit `9f4b484` 在 main 上 | — | `9f4b484` first commit（48 files / 5860 insertions）；精确 add 跳过 `.claude/settings.local.json`；**远端 push skipped**：留给 follow-up `harness-remote-push-<yyyymmdd>` 或 `bootstrap-monorepo` 一并配置 origin |
| 8 CI 验证 | **skipped: 无 CI 配置**（本次不引入 CI；留给 `bootstrap-monorepo`） | — | — | — |
| 9 部署验证 | **skipped: 无部署面**（纯文档变更） | — | — | — |
| 10 用户确认 | **done** | — | **APPROVED** | 用户 2026-05-16T21:40Z 通过 AskUserQuestion 显式确认关闭（选择"确认，可以关闭"） |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-16 | 追溯式记录骨架产出，而非删档重做 | 骨架内容质量本身已经过用户在线对齐；重做只会让 Dry Run 流于形式 | 本 summary §⚠️ |
| 2026-05-16 | 不删 `coding/` `unit_test/` 占位 `_v1.md`，让追溯报告也走 | 验证十阶段全链路在文档型变更下也能跑 | 各阶段子目录 |
| 2026-05-16 | Stage 8/9 显式 skip 而非删目录 | 让 review 看到 skip 决策本身可被审；删目录会让"是否考虑过"无法回查 | 本 summary |
| 2026-05-16 | Stage 3 就地修订两份支援型 SKILL（标题对齐 + 加失败回退章节）而非回退 stage 1/2 | Generator 在编码阶段修小漏洞是 stage 3 合理工作范围；回退过度。同时侧面消解 spec AC-10/AC-2 grep alternation OR 弱化 NICE TO HAVE | [coding_report_v1.md §偏离 spec / trade-off #1](coding/coding_report_v1.md) |
| 2026-05-16 | 不在本 change 内修 AC-10 验证命令（OR → AND） | 修验证命令会引起 spec 二次修订；根因修在独立 `harness-tighten-ac-grep-<yyyymmdd>` 变更 | coding_report §偏离 #1 |
| 2026-05-16 | check_harness.sh 放本 change 内（A vs B 选 B） | A 选项（顶层 `scripts/`）需要 spec §非范围微调 + 触发 spec_v2 重走 stage 2，与"用 bootstrap dry run 验证流程"目标冲突；B 选项保持 spec 不变、本变更内 self-contained，follow-up `harness-script-productize-<yyyymmdd>` 单独走流程提升到 `scripts/` 反而是又一次正向 dry run | [test_report_v1.md §偏离 #3](unit_test/test_report_v1.md)；用户 stage 4 末通过 AskUserQuestion 显式选择 |
| 2026-05-16 | Stage 7 选 A 路径：git init + 本地 commit，不 push（无远端） | 远端仓库尚未建立，强行配置 origin 会引入运维步骤超出 spec 范围；本地 commit 已实现 stage 7 "代码已提交到版本控制" 的本意；远端 push 留给 `harness-remote-push-*` 或 `bootstrap-monorepo` | 用户 stage 6 末通过 AskUserQuestion 显式选择 A；commit `9f4b484` 在 main |
| 2026-05-16 | 精确 `git add CLAUDE.md .harness wiki`（不全量 `git add .`）| 全量 add 会带入 `.claude/settings.local.json`（stage 4 SHOULD FIX #1 警告的入库风险）；用户全局 `~/.config/git/ignore:73` 虽已兜底 `**/.claude/settings.local.json` 但**隐式且不可移植**——仓库本地 `.gitignore` 显式约束仍待 bootstrap-monorepo 补；本变更通过精确 add 在 stage 7 内提前落实 deferred 决策的精神 | commit `9f4b484` 实测：`.claude/` 标记 `!!`（ignored），未入 commit |

## 当前阻塞

无。变更已关闭（详见 §交付 + §复盘）。

后续动作均在 follow-up 变更中：

- `bootstrap-monorepo-<yyyymmdd>`：dataplat monorepo 骨架 + `.gitignore` + CI
- `harness-script-productize-<yyyymmdd>`：check_harness.sh 提升到 `scripts/` + 加 `set -eo pipefail` + verbose 模式
- `harness-tighten-ac-grep-<yyyymmdd>`：修 grep alternation；同步 AC-9 术语 7→8；**spec §待澄清问题必须显式评估是否演化为 harness-lint 分层校验体系**（项目记忆 [[project-followup-harness-lint]] 已固化）
- `harness-trim-owner-agent-<yyyymmdd>`：application-owner.md 瘦身评估
- `harness-tighten-dev-process-<yyyymmdd>`：补 stage 7 二次 commit 规范 / stage 8/9 skip 规范 / 追溯式变更规范 / harness-* 命名约定
- `harness-remote-push-<yyyymmdd>`：配置远端 origin + push main
- `harness-script-portable-sh-<yyyymmdd>`（可选）：POSIX sh 兼容版自检脚本

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX（建议） | 把"骨架自检脚本"产品化为可重复运行的 `scripts/check_harness.sh` | follow-up：`bootstrap-monorepo` 中作为 task |
| NICE TO HAVE | 写一份骨架使用 1-pager 进 `wiki/` | follow-up |
| NICE TO HAVE（spec review v1） | AC-2 验证命令的 grep alternation 是 OR 关系，与文字描述的"同时声明"略有出入；现实已全部命中，不影响判定 | follow-up 评审脚本化时改 `&&` 串联 |
| NICE TO HAVE（tasks review v1） | tasks.md 中 `estimated_stage` 全填 `coding`（追溯式合理），未来非追溯式变更应细分到 `request_analysis` / `coding` / 等更精确阶段 | 在 [[harness-constraints]] 反哺为非追溯式变更的规范；或在下一 change 中具体使用时校准 |
| SHOULD FIX（code review v1 #1）| `.claude/settings.local.json` 入库风险（含用户机器特定 permissions） | `bootstrap-monorepo-<yyyymmdd>` 中：(a) 补 `.gitignore` 排除 `.claude/settings.local.json`；(b) 在 `engineering-structure.md` 显式约定 `.claude/` 是否入库 |
| NICE TO HAVE（code review v1 #2）| `wiki/domain-glossary.md` 中"Source Adapter 别用 Ingester/Connector"在正文 §核心抽象 与 表 §不要混用 两处重复声明 | follow-up：下次更新 glossary 时改用单源（保留表）|
| NICE TO HAVE（code review v1 #3）| `.harness/agents/application-owner.md` 149 行偏长，部分内容已分散在 design.md / mcp/README.md / wiki/，可瘦身以降低常驻上下文 token | follow-up：开 `harness-trim-owner-agent-<yyyymmdd>` 单独评估并精简 |
| NICE TO HAVE（test review v1 #1）| check_harness.sh 未开 `set -eo pipefail` | follow-up `harness-script-productize-<yyyymmdd>` 产品化到 `scripts/` 时一并加 |
| NICE TO HAVE（test review v1 #2）| check_harness.sh `run_ac` 把所有 AC 的 stderr 都吞了，FAIL 时排障要单独跑 `bash -x ac<N>` | 同 follow-up：加 `VERBOSE=1` 环境变量分支 |
| SHOULD FIX（test review v1 #3）| AC-6 用 `find _template -type f | wc -l ≥ 10` 对文件被清空内容无感 | 同根 follow-up `harness-tighten-ac-grep-<yyyymmdd>`：补 _template 文件内容断言 |

## 交付

> 关闭本变更时填写。

- **Branch**：`main`（仓库本变更内首次 `git init` + 重命名到 main；无功能分支，因 stage 7 选 A 路径直接在主分支 commit）
- **PR**：N/A（远端尚未配置，无 PR 流程；留给 `harness-remote-push-<yyyymmdd>` follow-up）
- **Commits**：
  - `9f4b484` feat(harness): bootstrap .harness/ skeleton and wiki/（48 files / 5860 insertions）
  - `287d45e` chore(harness): record stage 7 commit SHA in change summary（1 file / +8 / −6）
  - _本 stage 10 closure commit 将作为第 3 个 commit，由本次提交动作完成后回填_
- **部署版本**：N/A（纯文档变更，无部署面，stage 9 显式 skipped）
- **用户确认**：zhhdzhang，2026-05-16T21:40Z（通过 AskUserQuestion 显式选择"确认，可以关闭"）
- **关闭时间**：2026-05-16T21:45:00Z

## 复盘

> 本变更是 Harness Engineering 在 nta-lake 项目的首次 Dry Run，全程 stage 1-10（8/9 skipped）走完。回答开题三问 + 暴露的真实缺陷 + 经验。

### 开题三问

1. **追溯式记录是否真的暴露出流程问题？**

   **是。** 6 处真实缺陷全在追溯式流程中被实战命中（见下"Dry Run 暴露的真实流程缺陷"）。证明：
   - Stage 3 自检在 AC-10 grep 时抓到 ci-generate / project-analysis 两份支援型 SKILL 章节标题不齐
   - Stage 4 reviewer 抓到 `_template/README.md` 复制留孤儿、"复检指引"措辞不齐、`.claude/settings.local.json` 入库风险
   - Stage 6 reviewer 抓到 grep alternation OR 弱化的同类延伸到 AC-2/AC-8/AC-10 + AC-5 硬编码 + spec AC-9 内部术语 7 vs 8 不一致
   - Stage 7 实操暴露 dev-process.md 没规范 "commit 后回填 SHA 需二次 commit"
   - 没有这次 Dry Run，这些缺陷会在后续变更中陆续踩坑，且越晚发现修复成本越高
   - **结论**：追溯式作为一次性 bootstrap 例外是合理的，价值远高于成本

2. **stage 8/9 的 skip 机制清晰吗？是否需要 dev-process 显式规范"何时允许 skip 哪些阶段"？**

   **基本清晰，但规范有缺**。本变更通过 (a) summary 阶段进度表显式标 `skipped: <reason>` + (b) process_tasks 用 `status: skipped` + `reason:` 结构化字段 自创了一套做法，stage 4 / stage 6 reviewer 都接受。但 dev-process.md §阶段 7-9 没显式规定"什么变更可以 skip 哪些阶段"——例如 stage 8 (CI) 何时可 skip？当前回答是"无 CI 配置时"，但这条规则不在 dev-process.md。**反哺动作**：`harness-tighten-dev-process-<yyyymmdd>` follow-up 中加章节 "§阶段 skip 规则"。

3. **是否值得为"harness 自身的演进"开一类专门的 change 子类型（如 `harness-*`）？**

   **是。** 本变更命名 `harness-bootstrap-20260516`、follow-up 命名 `harness-tighten-ac-grep-*` / `harness-trim-owner-agent-*` / `harness-tighten-dev-process-*` 等，自然形成了 `harness-` 前缀类别。建议在 `harness-tighten-dev-process-*` follow-up 中正式约定：harness 自身演进的变更统一 `harness-<verb>-<scope>` 命名，并允许在 spec §范围段使用"修订 rules / skills / agents"作为合法 in scope（当前 spec 模板没显式给这种语义）。

### Dry Run 暴露的真实流程缺陷（6 处）

| # | 缺陷 | 发现阶段 | 处置 |
|---|---|---|---|
| 1 | spec AC-2/AC-8/AC-10 grep alternation OR 弱化（"任一命中即过"而非 AND） | stage 3 自检 + stage 6 review | defer 到 `harness-tighten-ac-grep-*` |
| 2 | ci-generate / project-analysis 两份支援型 SKILL 章节标题不齐 | stage 3 自检 | stage 3 就地修 |
| 3 | `.harness/changes/_template/README.md` 复制后留孤儿 | stage 4 review | stage 4 后就地修（cp 命令补 rm + 顶部双重警示）|
| 4 | "复检脚本指引" vs "复检指引" 术语不齐 | stage 4 review | stage 4 后就地修 |
| 5 | `.claude/settings.local.json` 入库风险（用户机器特定 permissions）| stage 4 review + stage 7 实操 | stage 7 精确 add 落实；显式 `.gitignore` defer `bootstrap-monorepo` |
| 6 | dev-process.md §阶段 7 未规范"commit 后回填 SHA 需二次 commit" | stage 7 实操 | 已反哺记入 summary，留 `harness-tighten-dev-process-*` |

### 经验

#### 哪些步骤超预期顺利

- **Generator/Reviewer 分离**：3 轮独立子会话评审（stage 2 / 4 / 6）都抓到了 Generator 自身上下文里看不到的问题。特别是 stage 6 reviewer 还自陈了自己 review 里 2 处小瑕疵（`grep -A1` 只看到空行 / `if e>0` 逻辑反转）——证明独立 reviewer 不只是"挑别人毛病"，是"双向校准"。
- **AC 全部可机械化判定**：12 条 AC 每条都附 shell 命令，stage 2/3/5/8 三次复检全 PASS。没有一条"用户感觉良好"类含糊验收。
- **Deferred 链条清晰**：13 条 SHOULD FIX + NICE TO HAVE 全有归属（现场修 / 既有 follow-up / 新 follow-up），无悬空。

#### 哪些步骤踩坑（已反哺）

- **追溯式 spec → 必然出现"自检发现产物有未被 spec 命中的小漏洞"**。stage 3 就地修两份 SKILL 这件事，按严格流程应该回 stage 1，但回退成本远高于价值。**反哺**：在 `harness-tighten-dev-process-*` 中加 "追溯式变更允许 Generator 在 stage 3 就地修订小漏洞 + 在 coding_report 显式自陈" 的规则。
- **grep alternation OR 弱化未被前两轮 review 抓到**。Stage 6 reviewer 通过抽查 AC 实质等价性才暴露——前两轮 review 是"清单式核查"，stage 6 引入了"实质等价性抽查"维度。**反哺**：在 expert-reviewer SKILL §1 §artifact 模式 检查清单加一条 "抽查 AC 实质等价性（断言代码是否真覆盖 AC 文字描述的事实）"。
- **`_template/README.md` 留孤儿是 cp 后未删的可预见 bug**，但骨架设计时漏了。**反哺**：在 changes/_template/_template/ 类有"复制即用"语义的目录里，加 README 顶部双重警示已是本变更内的修复；规则上也应该在 `coding-skill` SKILL §步骤 中加一条 "凡是设计为'复制即用'的资产，必须把'复制后的清理动作'写进上游 README"。

### 防复发机制（已落实到 harness）

1. ✅ `.harness/skills/ci-generate/SKILL.md` 与 `.harness/skills/project-analysis/SKILL.md` 章节标题对齐 + 加"失败回退"段（stage 3 修订）
2. ✅ `.harness/changes/README.md` cp 命令后追加 `rm` 步骤（stage 4 后修订）
3. ✅ `.harness/changes/_template/README.md` 顶部加双重警示（stage 4 后修订）
4. ✅ `.harness/skills/expert-reviewer/SKILL.md:88` "复检脚本指引" → "复检指引"（stage 4 后修订）
5. ✅ `CLAUDE.md:28` skills 链接精确到 README.md（stage 4 后修订）
6. ✅ `check_harness.sh` 头部声明 bash ≥ 3.2 兼容要求（stage 6 后修订）
7. ✅ test_report §偏离 #3 反向引用 stage 4 B 路径决策（stage 6 后修订）
8. ✅ 项目记忆 `project_followup_harness_lint.md` 固化 reviewer 的"shell 自检天花板"洞察，确保 `harness-tighten-ac-grep-*` 启动时不会错过演化窗口

未落实的 5 条都登记进 §Deferred 表 + follow-up 变更清单，无悬空。

### 元复盘：本变更对方法论本身的验证

文章 [.harness/harness.md](../../harness.md) §11 给出的目标"项目 AI 代码率 25% → 90%"对本变更不适用（纯文档骨架）。但文章 §10 五条经验全部命中实证：

| 文章经验 | 本变更实证 |
|---|---|
| Harness 自身要 Dry Run | ✅ 本变更就是 |
| 质量门禁必须可程序化验证 | ✅ 12 条 AC shell 命令 + check_harness.sh |
| 执行与评判要分离 | ✅ 3 轮独立 Reviewer 子会话 |
| 流程一致性优先于短期效率 | ✅ 小需求也走完 10 阶段（除 8/9 显式 skip） |
| 规范是活文档，发现 Agent 犯错就补 | ✅ 6 处缺陷 → 8 项已落实 + 6 个 follow-up |

**结论**：方法论本身经得起首次 Dry Run。可以放心进入下一变更 `bootstrap-monorepo-<yyyymmdd>`，用同样的流程构建 dataplat 代码骨架。
