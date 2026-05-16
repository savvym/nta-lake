---
change_id: harness-bootstrap-20260516
title: 建立 .harness/ 与 wiki/ 基线骨架，作为后续所有变更的运行环境
owner: zhhdzhang
started_at: 2026-05-16T03:00:00Z
stage: push
status: done_local_only
last_updated: 2026-05-16T21:30:00Z
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
| 10 用户确认 | pending | — | — | — |

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

- Stage 7 代码推送（A 路径本地 commit）已落地：commit `9f4b484` 在 main 分支，48 files / 5860 insertions；精确 add 跳过 `.claude/settings.local.json`；远端 push skipped 留给 follow-up。
- 下一动作：**Stage 10 用户确认**（stage 8 / 9 skipped）。需要用户对本变更整体交付做最终确认；然后做本变更的 stage 10 closure commit（含本次 summary 的 stage 7 元信息回填）。
- Stage 7 落地过程中暴露**新流程缺陷**：dev-process.md §阶段 7 没显式规范 "commit 后回填 SHA 到 summary 需要二次 commit" 这条节奏——本变更将通过 stage 10 的 closure commit 顺手做这件事，并把规则建议反哺 `harness-tighten-dev-process-<yyyymmdd>` follow-up。

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

- Branch：_（仓库尚未 git init；推送阶段会处理）_
- PR：—
- Merge commit：—
- 部署版本：N/A
- 用户确认：—
- 关闭时间：—

## 复盘（变更关闭后填）

预期复盘点：

- 追溯式记录是否真的暴露出流程问题？（如果 review 顺利通过且没发现 gap，说明流程对纯文档变更友好；若发现 gap，立即修 rules / skills）
- stage 8/9 的 skip 机制清晰吗？是否需要在 `development-process.md` 中显式规范"何时允许 skip 哪些阶段"？
- 是否值得为"harness 自身的演进"开一类专门的 change 子类型（如 `harness-*`）？
