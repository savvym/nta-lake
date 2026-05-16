---
change_id: harness-bootstrap-20260516
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:stage2-reviewer
reviewed_at: 2026-05-16T19:26:14Z
verdict: APPROVED
---

# Spec Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1（plan 模式 spec.md）。

- [x] 背景写明了为什么现在做（§背景：Harness Engineering 是后续所有变更的运行环境）。
- [x] 问题陈述对外部读者可理解（§问题陈述逐项列出当前空白）。
- [x] 范围 / 非范围都有（§范围 12 条 AC + §非范围 6 条显式排除）。
- [x] 每条验收标准可演示且可机械化（§验收标准表给出 shell 验证命令；已抽样实跑全部 12 条均成立）。
- [x] 风险有缓解或显式 accept（§风险表 5 条，均含缓解措施或 accept 标注）。
- [x] 没有把已有架构（`design.md` / `harness.md`）当新提案。
- [x] 待澄清问题已清零（4 项全部 `[x]`）。

## 抽样验证结论

针对 spec §验收标准表中 12 条 AC 的 shell 验证命令，本评审在仓库根目录全部实跑：

| AC | 现实结果 | 备注 |
|---|---|---|
| AC-1 | PASS | `CLAUDE.md` 含 `application-owner.md` 引用 |
| AC-2 | PASS | Owner Agent 含"配置索引 / 十阶段 / 硬性约束"三章节 |
| AC-3 | PASS | 三份 rules 均存在 |
| AC-4 | PASS | `^## 阶段 [0-9]+ ` grep 计数 = 10 |
| AC-5 | PASS | 9 个 SKILL.md + `skills/README.md` 全在 |
| AC-6 | PASS | `_template/` 下 12 个文件（≥ 10） |
| AC-7 | PASS | `changes/README.md` 含 `feature-slug` + `yyyymmdd` |
| AC-8 | PASS | `mcp/README.md` 30 行，含 Phase 0 占位语义 |
| AC-9 | PASS | 4 份 wiki 文件齐全；7 个核心术语全部 grep 命中 |
| AC-10 | PASS | 9 个 SKILL.md 全部含"进入条件 / 质量门禁 / 失败回退" |
| AC-11 | PASS | 最短文件 `wiki/README.md` 26 行（≥ 20） |
| AC-12 | PASS | 记忆目录下 4 份 .md 全部存在 |

结论：追溯式记录与现实文件状态**完全一致**，没有声称做但未做的项。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|

（无）

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §范围（行 31-44）与 §非范围（行 50-61） | "一次性追溯式例外"只在 §风险表（行 86）和 summary.md 中提及，但 §范围本体未把"本变更允许 spec 在代码之后产出"作为显式 in scope 项写出。外部读者只读 spec 容易误读为常规流程。 | 在 §范围段顶部加一行明确语句："本变更为 harness 骨架自身的引导，spec/tasks 为追溯式记录（详见 summary.md §⚠️）；该例外仅限本变更，不构成先例。" |
| 2 | spec.md §验收标准 AC-12（行 44, 80） | 路径 `~/.claude/projects/-data-home-zhhdzhang-nta-nta-lake/memory/` 是用户 + 主机绝对耦合的硬编码路径，跨机器或换用户即失效，违反"可机械化判定"中"可重复运行"的隐含要求。 | 将 AC-12 重述为：基于 `$HOME` 或显式当前用户的 Claude project memory 目录（路径含 cwd 转义规则），并补一行说明 `-data-home-zhhdzhang-nta-nta-lake` 是当前 cwd 的转义形式，跨环境需重算。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §验收标准表 AC-2（行 70） | grep 模式 `配置索引\|十阶段\|硬性约束` 是 OR 关系，任一命中即通过；但 AC-2 文字描述要求三者**同时**声明。 | 拆为三条 grep 串联（`&&`）或在描述中明确"任一命中即视为合格"。当前命令实际现实命中所有三项，不影响 verdict，留作后续优化。 |

## Verdict

APPROVED（MUST FIX 数 = 0）

> 说明：本评审采纳 summary.md §⚠️ 声明的"一次性例外"前提；追溯式 spec 与现实文件状态经 12 条 AC 全量抽样实跑核对，全部成立。SHOULD FIX 两条不阻塞推进，但建议 Generator 在进入下一阶段前补一版 spec_v2.md（或在 summary.md 显式 deferred 并写明跟进位置）。

## 复检指引

若 Generator 选择补 spec_v2.md：

1. 自检 §范围段是否新增"追溯式例外"说明一行：
   `grep -nE "追溯|例外" request_analysis/spec.md` 应在 §范围段命中。
2. 自检 AC-12 路径表述：
   `grep -n "AC-12" request_analysis/spec.md` 检查是否仍有硬编码 `-data-home-zhhdzhang-` 字串；若有，应在同段配以解释或换基于 `$HOME` / cwd 转义规则的描述。
3. 全量重跑 §验收标准表 12 条 shell 命令（在仓库根目录），全部 exit 0：
   ```bash
   cd /data/home/zhhdzhang/nta/nta-lake
   # 逐条复制 spec.md §验收标准 表中"验证方式"列的命令执行
   ```
4. 若不补 v2，在 `summary.md` §Deferred 项中追加这两条 SHOULD FIX 的 deferred 理由与跟进位置。

提交修订后开 `spec_review_v2.md`；若选择 deferred，本 review 即为最终版。
