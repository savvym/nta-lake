---
change_id: harness-bootstrap-20260516
version: 1
authored_at: 2026-05-16T03:05:00Z
status: draft
---

# Spec：建立 .harness/ 与 wiki/ 基线骨架

## 背景

`nta-lake` 仓库是新建项目，目标系统是面向 LLM 训练的数据管理平台（dataplat，详见 `.harness/design.md`）。复杂工程在仅靠 Prompt / Context 层的提示难以让 AI Coding 稳定推进；用户引入 Harness Engineering（参见 `.harness/harness.md`）作为方法论，要求把团队经验、工程规范、流程编排、质量门禁外部化、文件化、可执行化。

本变更是**所有后续变更得以运行的前置条件**：没有 `.harness/` 骨架，谈不上"按十阶段流程开发 dataplat"。

## 问题陈述

当前仓库除两份方法论 / 设计文档外完全空白：

- 没有 Application Owner Agent 来编排流程。
- 没有 Rules 文件来约束代码 / 流程的硬底线。
- 没有 Skills 描述各阶段的可复用 SOP。
- 没有 Changes 模板让团队按统一格式开变更档案。
- 没有 Wiki 沉淀架构与领域术语。
- 没有顶层 `CLAUDE.md` 让任何 Claude 会话能自动进入受控流程。

需要一次性把骨架补齐，并把"按流程"作为不可绕过的硬约束写进 rules，让后续即便 AI 单独行动也无法跳过流程。

## 范围

> **流程例外声明**：本变更为 harness 骨架自身的引导，spec/tasks 为追溯式（retroactive）记录——骨架文件在 spec 写定之前已落地。该例外**仅限本变更**，不构成先例；从下一变更（`bootstrap-monorepo-<yyyymmdd>`）起严格按十阶段顺序推进。详细背景见 [summary.md §⚠️ 一次性流程例外说明](../summary.md)。

In scope（每条都对应可机械化验证）：

- **AC-1**：仓库根存在 `CLAUDE.md`，且其中包含指向 `.harness/agents/application-owner.md` 的链接 / 路径。
- **AC-2**：`.harness/agents/application-owner.md` 存在，且声明了 Rules / Skills / Wiki / MCP 的配置索引、十阶段调度指令、硬性约束。
- **AC-3**：`.harness/rules/` 下存在三份 rules：`development-process.md`、`engineering-structure.md`、`coding-style.md`。
- **AC-4**：`development-process.md` 中包含完整的十阶段定义，每阶段都有 Entry Criteria / Skill Injection / Quality Gate / Rollback Route 四要素。
- **AC-5**：`.harness/skills/` 下存在 9 个 SKILL.md 及一个索引 `README.md`，覆盖 `request-analysis` / `coding-skill` / `expert-reviewer` / `unit-test-write` / `unit-test-ci` / `deploy-verify` / `code-review` / `project-analysis` / `ci-generate`。
- **AC-6**：`.harness/changes/_template/` 下存在完整变更模板（summary.md + 各阶段子目录与占位文件），且 `_template/README.md` 注明使用方式。
- **AC-7**：`.harness/changes/README.md` 描述了变更命名约定、目录结构、关闭条件。
- **AC-8**：`.harness/mcp/README.md` 存在并标注 Phase 0 占位 + 启用门槛。
- **AC-9**：`wiki/README.md`、`wiki/architecture.md`、`wiki/domain-glossary.md`、`wiki/adr/README.md` 存在；`domain-glossary.md` 至少定义 Repository / Layer / Asset / Source Adapter / Processor / Lineage / Commit / Blob 这些核心术语。
- **AC-10**：每个 SKILL.md 都包含"进入条件 / 输入 / 步骤 / 产出 / 质量门禁 / 失败回退"或等价章节，且门禁段含至少一条可机械化判定的条件。
- **AC-11**：每个 rules / SKILL / agent / wiki 文件均不为空（≥ 20 行有效内容）。
- **AC-12**：当前用户的 Claude project memory 目录下存在 `MEMORY.md` 索引及 `project_overview.md` / `harness_constraints.md` / `feedback_doc_language.md` 三份记忆文件。
  - 路径规则：`$HOME/.claude/projects/<cwd-escaped>/memory/`，其中 `<cwd-escaped>` 是当前仓库绝对路径按 Claude Code 的目录转义规则（`/` → `-`，开头追加 `-`）得到。当前仓库的转义形式为 `-data-home-zhhdzhang-nta-nta-lake`；跨机器 / 换用户须按此规则重算。

## 非范围

显式排除以下事项，避免 scope creep 与边界混淆：

- **不创建 `apps/` `packages/` `worker/` `plugins/` 等 dataplat 代码骨架**。
  - 理由：单独开 `bootstrap-monorepo-<yyyymmdd>` 变更承载；把代码骨架混进来会让本变更过大，且违背"先 Dry Run 流程"的本意。
- **不接入 CI**。
  - 理由：CI 是 dataplat 代码层面的依赖；本变更只动文档。CI 由 `ci-generate` Skill 在 `bootstrap-monorepo` 变更中产出。
- **不写 `.claude/settings.json` hooks**。
  - 理由：用户在开题时明确选择"Markdown + CLAUDE.md 集成"档位，不动 settings。
- **不接入任何 MCP server**。
  - 理由：Phase 2+ 才需要；当前仅留占位 README。
- **不做 `.harness/agents/` 多 Agent 拆分**（如单独的 reviewer-agent / coder-agent）。
  - 理由：第一版只定义 Application Owner 一个编排中枢；具体执行/评审通过子会话或子 Agent 工具实现，无需独立角色文件。
- **不在本变更中产出 ADR**。
  - 理由：尚未做任何架构决策；首批 ADR 应随 `bootstrap-monorepo` 一起诞生。

## 验收标准

> 已在"范围"段以 `AC-N` 列出。下表给出每条 AC 的验证方式与期望，是后续阶段 8 / shell 自检脚本的依据。

| ID | 描述 | 验证方式 | 期望 |
|---|---|---|---|
| AC-1 | CLAUDE.md 存在且引用 Owner Agent | `test -f CLAUDE.md && grep -q "application-owner.md" CLAUDE.md` | exit 0 |
| AC-2 | Owner Agent 存在且含核心章节 | `test -f .harness/agents/application-owner.md && grep -qE "配置索引\|十阶段\|硬性约束" .harness/agents/application-owner.md` | exit 0 |
| AC-3 | 三份 rules 存在 | `for f in development-process engineering-structure coding-style; do test -f .harness/rules/$f.md \|\| exit 1; done` | exit 0 |
| AC-4 | 十阶段定义完整 | `grep -cE "^## 阶段 [0-9]+ " .harness/rules/development-process.md` | ≥ 10 |
| AC-5 | 9 个 SKILL.md + 索引存在 | `find .harness/skills -name SKILL.md \| wc -l` | == 9；且 `.harness/skills/README.md` 存在 |
| AC-6 | 变更模板完整 | `find .harness/changes/_template -type f \| wc -l` | ≥ 10；含 summary.md + 各阶段 _v1.md |
| AC-7 | changes/README.md 含命名约定 | `grep -qE "feature-slug.*yyyymmdd" .harness/changes/README.md` | exit 0 |
| AC-8 | mcp/README.md 占位说明清晰 | `test -f .harness/mcp/README.md && grep -qE "Phase 0\|占位" .harness/mcp/README.md` | exit 0 |
| AC-9 | wiki 四份文件存在且含核心术语 | `for f in README architecture domain-glossary adr/README; do test -f wiki/$f.md \|\| exit 1; done; for term in Repository Asset "Source Adapter" Processor Lineage Commit Blob; do grep -q "$term" wiki/domain-glossary.md \|\| exit 1; done` | exit 0 |
| AC-10 | 每个 SKILL.md 含必填章节 | `for f in .harness/skills/*/SKILL.md; do grep -qE "进入条件\|质量门禁\|失败回退" $f \|\| exit 1; done` | exit 0 |
| AC-11 | 文件非空 | `find .harness wiki CLAUDE.md -name "*.md" -type f -exec wc -l {} + \| awk '$1 < 20 {print; bad=1} END {exit bad}'` | 无输出且 exit 0 |
| AC-12 | 项目记忆已写入 | `MEMDIR="$HOME/.claude/projects/$(pwd \| sed 's\|/\|-\|g')/memory"; test -f "$MEMDIR/MEMORY.md" && for f in project_overview harness_constraints feedback_doc_language; do test -f "$MEMDIR/$f.md" \|\| exit 1; done` | exit 0（在仓库根目录运行；`<cwd-escaped>` 按 §范围 AC-12 路径规则计算） |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 追溯式记录让评审流于形式 | 中 | 流程公信力下降 | 在 summary.md 中显式声明一次性例外；AC 全部对应可机械化验证；要求 stage 2 Reviewer 跑完整自检脚本 |
| Rules / Skills 写得过早，与真实使用脱节 | 中 | 后续变更频繁打回修 harness | 接受，把"修 harness"作为正常变更类型；并在 `bootstrap-monorepo` 复盘时强制评估骨架适配度 |
| 用户后续要求加 settings.json hooks，被 spec 显式排除挡住 | 低 | 临时返工 | 改 spec 而不是绕过 spec；开 `harness-add-hooks-<yyyymmdd>` 子变更 |
| 文档过多导致 Agent 上下文过载 | 中 | 每次会话占用大量 token | 已按 `.harness/README.md` 的分层加载策略设计：常驻仅 CLAUDE.md + Owner Agent；其他按需读。评审应抽查"Owner Agent 是否真的只索引而不堆细节" |
| 中文文档对未来非中文协作者不友好 | 低 | 协作摩擦 | 接受当前选择（用户明示）；如有需要单独开 `harness-i18n` 变更补英文版 |

## 受影响模块

- `CLAUDE.md`（新建）
- `.harness/agents/application-owner.md`（新建）
- `.harness/rules/{development-process,engineering-structure,coding-style}.md`（新建）
- `.harness/skills/{...}/SKILL.md`（9 个新建 + 1 个 README 新建）
- `.harness/changes/README.md` + `_template/` 全套（新建）
- `.harness/mcp/README.md`（新建）
- `wiki/{README,architecture,domain-glossary,adr/README}.md`（新建）
- `$HOME/.claude/projects/<cwd-escaped>/memory/`（新建；当前实例下解析为 `~/.claude/projects/-data-home-zhhdzhang-nta-nta-lake/memory/`，详见 §范围 AC-12 路径规则）

## 不受影响但易混淆的模块

- `.harness/design.md` 与 `.harness/harness.md`：**只读参考**，本变更**不**修改它们。
- `apps/` `packages/` `worker/` `plugins/` 等目录：**本变更完全不触碰**，由 `bootstrap-monorepo` 处理。

## 待澄清问题

> 提交评审前必须清零或显式 deferred。

- [x] 文档语言：中文为主（用户已确认）。
- [x] Skills 数量：9 个全量铺出（用户已确认）。
- [x] Owner Agent 集成方式：Markdown + CLAUDE.md，不动 settings.json（用户已确认）。
- [x] 是否同时铺 dataplat 代码骨架：不铺（用户已确认）。

## 引用

- `.harness/harness.md`：方法论原文笔记。
- `.harness/design.md`：dataplat 目标系统设计 v0.2。
- 用户在 2026-05-16 的开题对话中的四项选择（已记入 [[project-overview]]）。
