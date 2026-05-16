---
change_id: harness-bootstrap-20260516
title: 建立 .harness/ 与 wiki/ 基线骨架，作为后续所有变更的运行环境
owner: zhhdzhang
started_at: 2026-05-16T03:00:00Z
stage: push
status: in_progress
last_updated: 2026-05-16T21:15:00Z
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
| 7 代码推送 | pending（仓库尚未 git init） | — | — | — |
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

## 当前阻塞

- Stage 6 单测评审 APPROVED。SHOULD FIX #1/#2 + NICE #3/#4 已就地修：test_report 补 3 条 §已知问题（AC-8/AC-10 OR、AC-5 硬编码 9、AC-9 spec 内部 7vs8 术语不一致）+ §偏离 #3 反向引用 stage 4 B 路径决策；脚本头注 bash ≥ 3.2 兼容要求。
- 下一动作（决策点）：**Stage 7 代码推送**——但仓库尚未 `git init`，P-push.blocked_by 一直挂着。需要在本 change 内执行 `git init` 并做首个 commit，还是开独立 `harness-git-init-<yyyymmdd>` 子变更？
- Stage 8 / 9 仍 skipped（无 CI / 无部署面）。

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
