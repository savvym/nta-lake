---
change_id: harness-bootstrap-20260516
target: coding/coding_report_v1.md
target_head: n/a（仓库未 git init）
review_version: 1
reviewer: claude-agent:stage4-reviewer
reviewed_at: 2026-05-16T19:51:33Z
verdict: APPROVED
---

# Code Review v1

> 本变更为**纯 markdown 文档**变更，无 Python / TS / SQL 代码。`code-review` SKILL 中"性能 / 可观测性 / N+1 / 异步 / 类型 / 并发"等章节均 **N/A**（详见 §风格 / 性能 / 可观测性）。本评审聚焦：范围对照、章节自洽、术语一致、未授权目录、Stage 3 自检触发的两份 SKILL 修订是否合理。

## 范围与作者声明对照

- coding_report 声明的改动文件：38（仓库内 34 + 项目记忆 4）
- 实测（自跑 `find .harness wiki -name '*.md' -not -path '*/changes/harness-bootstrap-20260516/*' -not -name 'harness.md' -not -name 'design.md'` + CLAUDE.md + 4 份记忆）：**34 + 4 = 38**，与报告一致。
- 子分类核对：A(1) + B(1) + C(1) + D(3) + E(10) + F(13) + G(1) + H(4 wiki) = 34 ✓；项目记忆 4 份齐全（`$HOME/.claude/projects/-data-home-zhhdzhang-nta-nta-lake/memory/` 下 MEMORY / project_overview / harness_constraints / feedback_doc_language）。
- 10 个抽样内部链接 + 10 个抽样路径全部 `test -f` 通过；scope 内未发现 scope creep。
- 顶层只有 `CLAUDE.md` / `.harness/` / `wiki/` / `.claude/`（仅 `settings.local.json`，**详见 SHOULD FIX #1**）；spec §非范围 6 条全部尊重（无 apps/packages/worker/plugins，无 hooks）。

> 一致性结论：✓。报告未隐瞒、未夸大。

## 正确性 / 安全 / 架构问题

### MUST FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|

（无）

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `.claude/settings.local.json`（全文 8 行） | 仓库存在一个 `settings.local.json`，含 `Bash(awk ...)` / `Bash(python3 *)` permission allow。这是 Claude Code 自动写入的 local 缓存，但 spec §非范围明确"不写任何 `.claude/settings.json` hooks"——虽然 hooks ≠ permissions 严格意义上不违反 spec，但 `.claude/` 目录已实际进入仓库，未来若 commit 容易把用户机器特定的 permissions 带入版本控制。 | 在 follow-up（`bootstrap-monorepo`）中补 `.gitignore` 把 `.claude/settings.local.json` 排除；或在 `engineering-structure.md` 显式约定 `.claude/` 不入库。本变更不阻塞。 |
| 2 | `.harness/changes/_template/README.md`（全文 38 行）+ `.harness/changes/README.md:20` | 模板使用方法用 `cp -r _template <new-change-id>`——这会把 `_template/README.md` 一并复制到新 change 目录，导致每个新 change 都带一份解释"如何用模板"的孤儿 README，且不会被作者察觉。 | 在 changes/README.md §启动一个新变更 的 cp 命令后追加一行 `rm <new-change-id>/README.md`；或把 `_template/README.md` 改名为 `.harness/changes/_template_README.md`（置于上级目录）；或在 `_template/README.md` 顶行加 "复制后立即删除本文件" 提示。 |
| 3 | `.harness/skills/expert-reviewer/SKILL.md:88` 与 `.harness/skills/code-review/SKILL.md:88-95` | 前者写"复检脚本指引"，后者写"复检指引"——本 review 模板使用"复检指引"，术语三处不齐，未来作者照抄会产生不一致章节名。 | 统一为"复检指引"（短一致），并在 expert-reviewer SKILL §4 同步。 |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `CLAUDE.md` 第 28 行 / `.harness/skills/` 链接 | 链接到目录而非具体 README.md（其他 5 条都精确到 `.md`），实际 IDE 中可点开，但纯 grep 验证会漏。 | 改为 `.harness/skills/README.md`，与其他行风格一致。 |
| 2 | `wiki/domain-glossary.md:69` 与表行 177 重复声明"Source Adapter 别用 Ingester/Connector" | 一次正文 + 一次表格——可读性 OK，但维护时易漂移。 | 留作 follow-up；不阻塞。 |
| 3 | `.harness/agents/application-owner.md` 整体 149 行 | Owner Agent 是常驻上下文文件，149 行偏长；其中 §2 项目背景速览 + §3.4 MCP 占位 + §8 不确定时——这些细节都已分散在 `.harness/design.md` / `.harness/mcp/README.md` / `wiki/` 中，可考虑下一轮瘦身。 | 留作 follow-up；当前不阻塞。 |

## 风格 / 性能 / 可观测性

> 纯文档变更——以下 code-review SKILL 章节均 **N/A**：
>
> - **性能**（N+1、大对象 read）：N/A，无代码。
> - **可观测性**（log / metric / span）：N/A，无运行时。
> - **异步**（async/await、race）：N/A。
> - **类型完整性 / Pydantic / SQLAlchemy 抽象**：N/A。
> - **N+1 / 分页 / 虚拟滚动**：N/A。
>
> 适用的等价校验改为以下文档型项目：

- **frontmatter 合法性**：自跑 PyYAML 解析 36 份含 frontmatter 的 .md，全部 PASS。
- **AC-10 章节存在性**：9 个 SKILL.md 全部含"进入条件 / 质量门禁 / 失败回退"——逐文件 grep 确认（包括 Stage 3 就地修订的 ci-generate / project-analysis）。
- **AC-11 文件非空**：最短 wiki/README.md = 26 行 ≥ 20。
- **AC-1..12 全量重跑**：12 条全部 PASS（与 stage 2 review v1 一致）。
- **术语一致性**（依据 `wiki/domain-glossary.md` §不要混用）：grep 全仓 `Ingester|Connector|Workflow`，命中仅在 glossary 表内做反例声明，本变更新建文件无违例；"数据集"一词出现仅在 `.harness/design.md`（本变更只读不动），合规。
- **链接有效性**：10 条抽样 + glossary 内部相对路径全部存在。

## 跨改动观察

1. **十阶段 Skill 命名与 SKILL frontmatter 一致**：`expert-reviewer.applicable_stage = 阶段 2/6`、`code-review = 阶段 4`、`ci-generate = 支援型`，与 `development-process.md` §阶段 N Skill Injection 一一对得上——未发现阶段 ↔ Skill 错位。
2. **"Generator/Reviewer 分离" 在多处文档中表述一致**：CLAUDE.md / Application Owner §4.3 / dev-process §阶段 2/4/6 / code-review SKILL / expert-reviewer SKILL 全部点到"独立子会话/不共享上下文"——这是本骨架最关键的不变量，没有发现破窗。
3. **Stage 3 自检发现的两份 SKILL 修订是实质性补全**（不是文字 rename）：
   - `ci-generate/SKILL.md` 的"进入条件"段：5 条触发场景（项目从零搭 CI / CI 不能产出结构化字段 / 增加新子项目 / CI 太慢 / 阶段 8 多次回退指向 CI 配置），语义就是"何时进入"，比单纯 rename 更具操作性。
   - `project-analysis/SKILL.md` 的"进入条件"段：4 条触发场景（新成员上手 / 大重构前 / 跨 change 一致性审计 / debug 复杂链路），同样实质。
   - 两份新加的"失败回退"段都给出 5 条具体场景的回退路径，与其他 SKILL 风格一致，非凑章节。

## Deferred SHOULD FIX

> 以下三条 SHOULD FIX 在本变更内不强制修，转 follow-up：

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX #1 | `.claude/settings.local.json` 入库风险 | `bootstrap-monorepo-<yyyymmdd>` 中补 `.gitignore` 与 engineering-structure 显式约束 |
| SHOULD FIX #2 | `_template/README.md` 复制后会留孤儿文件 | 在本 change 的 stage 5 / 后续 `harness-template-cleanup-<yyyymmdd>` 修——若想最小代价，在 `changes/README.md` cp 命令后追加 `rm` 即可，可在本 change 内一行修订；不强制 |
| SHOULD FIX #3 | "复检指引" vs "复检脚本指引" 术语不齐 | 同上，单行 grep 替换；不强制 |

## 对两个关键 trade-off 的判断

1. **Stage 3 就地修订两份 SKILL（不回退 stage 1/2）**：**同意**。理由：
   - 修订内容是"补齐章节标题对齐 + 补失败回退章节"，属于编码阶段产物本身的小漏洞，没有触及 spec / tasks 的范围或验收标准本身（AC-5 / AC-10 内容定义未变）。
   - 回退 stage 1 会让追溯式变更陷入"为了修文档章节名回退 spec"的无意义循环——脱离价值。
   - 修订后再跑 AC-10 / AC-11 / frontmatter 均 PASS——证据完整。
2. **不在本 change 内修 AC-10 / AC-2 的 grep alternation OR 弱化**：**同意**。理由：
   - 改 spec 验收命令属于 spec 实质变更，按 development-process.md §跨阶段约束 #2/#3，应当增版本（spec_v2.md）并补 spec_review_v2.md；本变更已 stage 3，若回去补会显著拖长追溯式 dry run 的回路。
   - 现实命中：12 条 AC 全部 PASS，OR 弱化未造成漏判（且 stage 3 反而靠这个弱化被实战暴露，Generator 已侧面消解）。
   - Generator 已明确登记 follow-up（`harness-tighten-ac-grep-<yyyymmdd>`），不属于隐瞒。
   - 留作独立变更走完整流程，反而是本 harness "用骨架修骨架"的正向 dry run，价值高于一次性附带改。

## Verdict

**APPROVED**（MUST FIX 数 = 0）

> SHOULD FIX 3 条已在 §Deferred 表记录跟进位置；NICE TO HAVE 不阻塞。Generator 可继续推进 stage 5（单测编写——shell 自检脚本路径），并在 summary.md 阶段 4 行补 v1 / verdict / report 路径。

## 复检指引

若 Generator 修了任何 SHOULD FIX 后想做 v2：

```bash
cd /data/home/zhhdzhang/nta/nta-lake

# 1. 重跑 12 条 AC（spec.md §验收标准表逐条），全部 exit 0
#    略——见 spec_review_v1.md §复检指引 与 coding_report_v1.md §本地校验

# 2. 复核改动清单仍为 38（仓库 34 + 记忆 4）
find .harness wiki -type f -name "*.md" \
  -not -path "*/changes/harness-bootstrap-20260516/*" \
  -not -name "harness.md" -not -name "design.md" | wc -l   # 期望 33（.harness 内 + wiki，含 _template）
test -f CLAUDE.md && echo +1                                # 共 34
ls $HOME/.claude/projects/-data-home-zhhdzhang-nta-nta-lake/memory/*.md | wc -l   # 期望 4

# 3. 若修了 SHOULD FIX #2：验证 changes/README.md cp 命令后含 rm，或 _template 内无 README.md
grep -A1 "cp -r .harness/changes/_template" .harness/changes/README.md

# 4. 若修了 SHOULD FIX #3：术语统一
grep -rn "复检脚本指引" .harness/   # 期望无命中

# 5. frontmatter 全量复跑
python3 -c 'import os,yaml,sys; bad=[];
for d in [".harness","wiki"]:
 for r,_,fs in os.walk(d):
  if "/changes/harness-bootstrap-20260516" in r and "_template" not in r: continue
  for f in fs:
   if not f.endswith(".md"): continue
   p=os.path.join(r,f); c=open(p).read()
   if c.startswith("---\n"):
    e=c.find("\n---\n",4)
    try: yaml.safe_load(c[4:e]) if e>0 else bad.append((p,"unclosed"))
    except Exception as ex: bad.append((p,str(ex)))
[print("FAIL",p,m) for p,m in bad]; sys.exit(1 if bad else 0)'
```

修订后请开 `code_review_v2.md`；若选择不补、全部 SHOULD FIX 走 deferred，本文件即为最终版。
