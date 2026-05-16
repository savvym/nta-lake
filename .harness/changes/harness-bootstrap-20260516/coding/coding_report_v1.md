---
change_id: harness-bootstrap-20260516
version: 1
authored_at: 2026-05-16T19:50:00Z
branch: n/a（仓库尚未 git init；详见 §特殊门禁说明）
base_commit: n/a
head_commit: n/a
status: waiting_review
---

# Coding Report v1（追溯式）

## 一句话总览

本次"编码"产出的是 dataplat 项目的 **harness 骨架文件**（无 Python / TS 代码）。共新建 34 个仓库内 `.md` 文件 + 4 个项目记忆 `.md` 文件，并在 Stage 3 自检中**补修了两个 SKILL.md 的章节标题对齐**（详见 §偏离 spec / trade-off）。

## 改动文件清单

> 仓库未 `git init`，无 `git diff` 可对比。下面清单基于 `find .harness wiki CLAUDE.md` + 项目记忆目录直接列出，与 spec.md §受影响模块一一对应。

### A. 顶层（1 个）

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `CLAUDE.md` | new | 任何 Claude 会话进入项目时的入口；指向 Owner Agent + 列硬性约束 | T-1 |

### B. .harness/agents/（1 个）

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `.harness/agents/application-owner.md` | new | 编排中枢：角色、配置索引、十阶段调度、Generator/Reviewer 分离、6 条硬性约束 | T-2 |

### C. .harness/（导航，1 个）

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `.harness/README.md` | new | harness 自身导航 + 分层加载策略 | T-3 |

### D. .harness/rules/（3 个）

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `.harness/rules/development-process.md` | new | 十阶段流程权威定义（每阶段 4 要素 + 回退路径速查表） | T-4 |
| `.harness/rules/engineering-structure.md` | new | monorepo 目录约束（落实 design.md §11.3） | T-5 |
| `.harness/rules/coding-style.md` | new | Python/TS/SQL/Git/LLM/安全/性能 7 类风格底线 | T-6 |

### E. .harness/skills/（10 个）

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `.harness/skills/README.md` | new | Skill 索引 + 关系图 + 新 Skill 约定 | T-8 |
| `.harness/skills/request-analysis/SKILL.md` | new | 需求分析 SOP（阶段 1） | T-7 |
| `.harness/skills/coding-skill/SKILL.md` | new | 编码 SOP（阶段 3） | T-7 |
| `.harness/skills/expert-reviewer/SKILL.md` | new | 计划/产物评审 SOP（阶段 2/6） | T-7 |
| `.harness/skills/unit-test-write/SKILL.md` | new | 单测编写 SOP（阶段 5） | T-7 |
| `.harness/skills/unit-test-ci/SKILL.md` | new | CI 验证 SOP（阶段 8） | T-7 |
| `.harness/skills/deploy-verify/SKILL.md` | new | 部署验证 SOP（阶段 9） | T-7 |
| `.harness/skills/code-review/SKILL.md` | new | 代码评审 SOP（阶段 4） | T-7 |
| `.harness/skills/project-analysis/SKILL.md` | new + **mod (stage 3)** | 项目分析 SOP（支援型）；**stage 3 自检补"进入条件"标题对齐 + 新增"失败回退"章节** | T-7 |
| `.harness/skills/ci-generate/SKILL.md` | new + **mod (stage 3)** | CI 配置生成 SOP（支援型）；同上修订 | T-7 |

### F. .harness/changes/（13 个）

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `.harness/changes/README.md` | new | 变更命名、启动、子目录、关闭条件 | T-10 |
| `.harness/changes/_template/README.md` | new | 模板使用说明 | T-9 |
| `.harness/changes/_template/summary.md` | new | SSOT 模板 | T-9 |
| `.harness/changes/_template/request_analysis/spec.md` | new | spec 模板 | T-9 |
| `.harness/changes/_template/request_analysis/tasks.md` | new | tasks 模板 | T-9 |
| `.harness/changes/_template/request_analysis/review/spec_review_v1.md` | new | spec review 模板 | T-9 |
| `.harness/changes/_template/request_analysis/review/tasks_review_v1.md` | new | tasks review 模板 | T-9 |
| `.harness/changes/_template/coding/coding_report_v1.md` | new | 编码报告模板 | T-9 |
| `.harness/changes/_template/coding/review/code_review_v1.md` | new | 代码评审模板 | T-9 |
| `.harness/changes/_template/unit_test/test_report_v1.md` | new | 单测报告模板 | T-9 |
| `.harness/changes/_template/unit_test/review/test_review_v1.md` | new | 单测评审模板 | T-9 |
| `.harness/changes/_template/ci_result/ci_result_v1.md` | new | CI 结果模板 | T-9 |
| `.harness/changes/_template/deployment/deploy_verify_v1.md` | new | 部署验证模板 | T-9 |

### G. .harness/mcp/（1 个）

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `.harness/mcp/README.md` | new | Phase 0 占位 + 启用门槛 | T-11 |

### H. wiki/（4 个）

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `wiki/README.md` | new | wiki 入口 + 与 design.md 关系 | T-12 |
| `wiki/architecture.md` | new | 架构总览（Phase 0：以 design.md 摘要 + 漂移记录占位） | T-12 |
| `wiki/domain-glossary.md` | new | 领域术语表（Repository / Asset / Adapter / Processor / Lineage 等） | T-12 |
| `wiki/adr/README.md` | new | ADR 模板 + 工作流 | T-12 |

### I. 项目记忆（仓库外 4 个）

| 路径（`$HOME/.claude/projects/<cwd-escaped>/memory/`） | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `MEMORY.md` | new | 记忆索引 | T-13 |
| `project_overview.md` | new | dataplat 项目状态、技术栈、用户选择 | T-13 |
| `harness_constraints.md` | new | 流程硬约束 feedback | T-13 |
| `feedback_doc_language.md` | new | 中文为主的偏好 feedback | T-13 |

**改动文件总数：34（仓库内）+ 4（项目记忆）= 38。**

## 与 tasks.md 的映射

| Task ID | 状态 | commits | 备注 |
|---|---|---|---|
| T-1 | done | — | CLAUDE.md |
| T-2 | done | — | application-owner.md |
| T-3 | done | — | .harness/README.md |
| T-4 | done | — | development-process.md |
| T-5 | done | — | engineering-structure.md |
| T-6 | done | — | coding-style.md |
| T-7 | done（含 stage 3 自检的两份 SKILL 修订） | — | 9 个 SKILL.md |
| T-8 | done | — | skills/README.md |
| T-9 | done | — | _template/ 全套 12 个文件 |
| T-10 | done | — | changes/README.md |
| T-11 | done | — | mcp/README.md |
| T-12 | done | — | wiki/ 全套 |
| T-13 | done | — | 4 份项目记忆 |

commits 字段全部为空——见 §特殊门禁说明。

## 偏离 spec / trade-off

### 1. Stage 3 自检发现的两份 SKILL 标题对齐修订

**事实**：`ci-generate/SKILL.md` 与 `project-analysis/SKILL.md` 原稿用"何时使用"标题（支援型 Skill 的语义化措辞），且没有独立的"失败回退"章节。Stage 3 等价校验时按 spec AC-10 的精确 grep（`进入条件 / 质量门禁 / 失败回退`）扫描，**这两个 SKILL 命中 FAIL**。

**stage 2 review 的盲区**：reviewer 抽样了 AC-10 命令但显示 PASS，说明 grep 在所有 9 个 SKILL 上的整体退出码是 0——回看 reviewer 命令是 `for f ... do grep -qE "..." $f || exit 1; done`，命令本身是正确的，但 reviewer 把 `-qE` 当成"任一命中"——实际 `-qE "A|B|C"` 是 OR 关系，三个之中任一存在就通过。两个支援型 SKILL 里有"质量门禁"段，命中 OR 即过——这是 AC-10 spec 验证命令本身的逻辑漏洞，与 spec review v1 NICE TO HAVE #1（AC-2 同类问题）是同根。

**处理**：

- 不开新 review；按 stage 3 的合理工作范围，**在编码阶段就地补齐两份 SKILL** 的"进入条件"与"失败回退"章节，保持流程一致性。
- 这恰好把 NICE TO HAVE（spec review v1）从"将来再修"提前到"现在已修"——AC-10 验证命令的 OR 弱化问题在本 change 内通过统一所有 SKILL 章节标题来侧面消解。

**等待 stage 4 reviewer 判断**：

- 此修订是否属于 stage 3 合理工作范围（我的判断：是——产出本身的小漏洞修在 stage 3，回退 stage 1 过度）。
- 是否应当在本 change 中**进一步**修 AC-10 验证命令（把 `-qE "A|B|C"` 拆成 `grep -q A && grep -q B && grep -q C`），把根因彻底铲掉。我倾向**不**做——会引起 spec 二次修订；改 AC-10 命令的事单独开 `harness-tighten-ac10-<yyyymmdd>` 变更走完整流程，更合规。

### 2. 不涉及 dataplat 业务代码

spec 已明确这是非范围（apps/packages/worker/plugins 都不动）。本 change 全是 markdown。**因此 stage 3 Quality Gate 中的"本地 ruff / mypy / pnpm lint / pnpm typecheck"均 N/A**，用文档型等价校验替代（详见 §本地校验）。

### 3. spec / tasks 自身的"代码"也是骨架的一部分

`_template/` 下的 12 个模板文件本身就是骨架产物。但 stage 3 自检里给 spec/tasks/review 模板做章节匹配会自相矛盾（模板本身有占位 `<...>`），所以 AC-6 的判定**只看模板文件存在性和总数**（≥ 10），不看内部内容——这是 spec 写定时的故意宽松。stage 4 reviewer 可考虑是否要求模板内容也加结构性校验。

## 特殊门禁说明

| Stage 3 Quality Gate（development-process.md §阶段 3） | 本次状态 | 等价替代 |
|---|---|---|
| coding_report_v{latest}.md 存在 | ✓ | — |
| 报告中"改动文件列表" 与 `git diff --name-only main...HEAD` 一致 | **N/A：仓库未 git init** | 改动清单用 `find` 列出 34 个仓库内文件 + 4 个项目记忆文件，每条精确对应 spec.md §受影响模块；任何一致性偏差请 stage 4 reviewer 用 `find` 重跑核对 |
| 本地 `ruff check` / `mypy` / `pnpm lint` / `pnpm typecheck` 全部 0 错误 | **N/A：纯文档变更** | 用 (a) frontmatter YAML 合法性、(b) 每文件 ≥ 20 行（AC-11）、(c) AC-10 章节存在性、(d) 12 条 AC shell 命令全部 exit 0 作为等价校验 |
| 未引入未在 spec/tasks 中授权的目录或顶层依赖 | ✓ | 顶层仅 `CLAUDE.md` + `.harness/` + `wiki/`，未授权目录 grep 结果"无" |
| 所有改动属于本 change 的 scope | ✓ | 全部文件路径都在 spec §受影响模块列出的目录之内 |

## 本地校验结果

```text
=== A. 顶层未授权目录检查 ===
顶层项: CLAUDE.md, .harness, wiki
未授权项: (无)

=== B. frontmatter YAML 合法性（python yaml.safe_load 全部解析）===
ALL frontmatter blocks parse OK

=== C. AC-11 自检：所有骨架 .md ≥ 20 行 ===
(无 FAIL 输出)
最短文件: wiki/README.md = 26 行

=== D. AC-10 自检：每个 SKILL.md 含三项必备章节 ===
(无 FAIL 输出)
注：stage 3 自检最初命中 2 个 FAIL（ci-generate / project-analysis），
   已就地修订，再跑通过；详见 §偏离 spec / trade-off #1。

=== E. spec.md §验收标准表 12 条 AC 全量重跑（同 stage 2 review 的复检）===
AC-1: PASS    AC-2: PASS    AC-3: PASS    AC-4: PASS
AC-5: PASS    AC-6: PASS    AC-7: PASS    AC-8: PASS
AC-9: PASS    AC-10: PASS   AC-11: PASS   AC-12: PASS
```

## 已知未解决问题（评审决定是否阻塞）

| 问题 | 影响 | 建议处理 |
|---|---|---|
| 仓库未 `git init`，无法走 stage 7（push）与传统意义上的 PR 评审 | stage 7-8 链路在本 change 内无法实跑 | stage 5 单测评审通过后，**先在本 change 内做 `git init` + 单一 commit**，再决定 push 时机；或新开 `harness-git-init-<yyyymmdd>` 子变更。倾向前者，因为后者会让本 change 永远悬空在 stage 7 |
| spec AC-10/AC-2 的 grep alternation OR 弱化（已在 Deferred 表记录） | spec 验证命令理论上有漏判风险（已被 stage 3 实战命中） | 本 change 内已通过对齐 SKILL 标题侧面消解；根因修在独立的 `harness-tighten-ac-grep-<yyyymmdd>` 变更里 |
| stage 4-6 / stage 10 都还没跑 | 本 change 远未关闭 | 按流程逐阶段推进 |

## 下一步

进入 **Stage 4 编码评审**：加载 `.harness/skills/code-review/SKILL.md`，由**独立 Reviewer 子会话**对：

1. 改动文件清单与 spec §受影响模块的一致性
2. 两份 SKILL 标题对齐修订是否合理、是否应进一步修 AC-10 命令
3. 文档质量（命名、链接有效性、章节自洽）
4. 未授权目录 / 依赖检查

写 `coding/review/code_review_v1.md`。
