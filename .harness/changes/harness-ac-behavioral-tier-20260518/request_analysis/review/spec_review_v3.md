---
change_id: harness-ac-behavioral-tier-20260518
target: spec.md
target_version: 3
review_version: 3
reviewer: claude-agent:harness-ac-behavioral-tier-20260518-stage2-reviewer-v3
reviewed_at: 2026-05-18T09:55:00Z
verdict: APPROVED
---

# Spec Review v3

## v2 MUST FIX 复检（reviewer 实跑 spec_review_v2.md §复检指引 命令）

| # | v2 issue | 状态 | 证据（reviewer 本机实跑）|
|---|---|---|---|
| MUST #1 | summary.md L57 仍写 "18 个 closed change"，与 spec v2 闭环表自称 CLOSED 矛盾 | **CLOSED** | `grep -nE "18 个" summary.md` → 0 行；`grep -nE "19 个" summary.md` → L57 命中：`不强制覆盖历史 closed change，新 change 起强制 lint \| **19 个** closed change 全量回填工作量超本 change 承载；grandfather 旧 change 分两类（2 永久豁免 + 17 暂豁免，后续 backfill harness-ac-kind-backfill-* P1）`。reviewer 提示的"借机补成两类描述"也已采纳。 |
| MUST #2 | 双条件 (ii) 实现裸 `grep -q behavioral` 被 AC 描述文本里的 "behavioral" 字串触发，机械化保护实质失效 | **CLOSED** | 三层证据真实闭环：<br>(a) **spec.md L81** AC-4 描述：`(ii) 段内至少 1 行 AC 的 kind 单元格真值为 behavioral：grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|' <段>`，已锚定 AC 行 kind 单元格。<br>(b) **spec.md L118** AC-6 内 `grep -cE` 用同型 regex，SHOULD #5 from v2 同型缺陷 CLOSED。<br>(c) **spec.md L134** 风险表新增条目明示"不接受裸字串 `grep -q behavioral`"。<br>(d) **真实跑过 dry-run 验证**：reviewer 用 `awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md` 抽出本 spec AC 段（15 行），运行：<br>&nbsp;&nbsp;- 裸 `grep -c behavioral` = **8**（v2 缺陷）<br>&nbsp;&nbsp;- v3 锚定 regex `grep -cE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|'` = **2**（命中行恰为 AC-4 + AC-8）<br>(e) **提示词要求的反例打靶 dry-run**：reviewer 临时构造一份"AC 表有 kind 列 + 所有 AC kind 单元格 = static + AC 描述里 4 处出现 `behavioral` 字串"的 spec，运行：<br>&nbsp;&nbsp;- 裸 `grep -c behavioral` = **4**（v2 旧实现会假 PASS）<br>&nbsp;&nbsp;- v3 锚定 regex 命中 = **0**（v3 正确 FAIL，机械化保护真守门）<br>核心命题（lint 真守门）已实证闭环。 |
| SHOULD #1 | AC-7 for loop 前缺 `test -f` 前置 | **CLOSED** | spec.md L119 AC-7 验证：`test -f .harness/skills/request-analysis/SKILL.md && for cid in ...; do grep -q "$cid" ... \|\| exit 1; done && ...`，已加 `test -f` 前置；与 AC-1/AC-2/AC-3 模式一致，符合 SKILL §6 "反向 grep + test -f" 精神。 |
| SHOULD #2 | AC-5 `grep -A 60` 偏大，可能把 stage 10 吞下 | **CLOSED** | spec.md L117 AC-5 改为 `S9=$(awk '/^## 阶段 9/{p=1;next} p && /^## 阶段 /{exit} p' ...) && echo "$S9" \| grep -qE ...`，状态机模式与 AC-6 / AC-7 一致；`grep -A 60` 已完全消失（reviewer 实跑 `grep -n "grep -A 60" spec.md` = 仅匹配 v2 闭环表自引用 1 处）。 |
| SHOULD #3 | summary.md L57 decision row "18 个" 残留（同 MUST #1）| CLOSED via MUST #1 | 同上。 |
| SHOULD #4 | v1 闭环表 awk 行数描述只写 37 单一样本 | **CLOSED** | spec.md L32 改为 "最少 13 行（repo-api-mvp）/ 最大 102 行（commit-api-mvp）/ 19 spec 全覆盖 AC 表段无假阳性"，证据范围扩到 19 个 closed spec。 |
| SHOULD #5 | AC-6 内 `grep -c behavioral` 同型缺陷 | CLOSED via MUST #2 | spec.md L118 AC-6 `grep -cE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|'`，与新双条件实现统一。 |
| NICE #1 | 19 ID 硬编码未来失效 | CLOSED | spec.md L26 v3 闭环表注："T-1b 注释明示本 change 自身**不豁免**（dogfood，自带 ≥2 behavioral AC）；未来新 change 也不豁免；硬编码仅 19 历史 ID"。诚实路径优于把"制定者"加豁免名单。 |
| NICE #2 | 引用段路径片段相对 | 接受 NICE，不修 | 不阻塞。 |

**v2 2 个 MUST FIX + 5 个 SHOULD FIX 复检结论**：全部真闭环（9/9）。v3 闭环表与本 reviewer 实跑证据吻合，未发现"声明 CLOSED 但产物未真改"的同型问题（这正是 v2 MUST #1 的失败模式）。

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 + request-analysis SKILL 跨 AC 自审 9 条）

### plan 模式 spec.md 6 条

- [x] 背景：清晰承接 pipeline-orchestrator stage 9 三 bug；与 problem statement 同向。
- [x] 问题陈述与目标可被一个外部读者理解。
- [x] 范围 / 非范围：6 条非范围显式列出，含 v1→v2 决策翻转（_template 加列）有 strike-through 历史保留。
- [x] 验收标准每条都可演示且可机械化——AC-4 / AC-6 双条件 (ii) 已 regex 锚定；AC-7 / AC-5 全配 `test -f` 前置；AC-8 不写死 PASS 数。
- [x] 风险有缓解措施或显式 accept——7 条风险均配缓解；reviewer 字段约束已机械化（双条件断言 + fixture 反例打靶）。
- [x] 没把已有架构当新提案。

### 跨 AC 一致性自审 9 条

| # | 条目 | 状态 | 评语 |
|---|---|---|---|
| 1 | 四链路一致（schema/hash/idempotency/fixture） | n/a | 无 DB schema / hash |
| 2 | 事务边界三处一致 | n/a | 无事务 |
| 3 | AC 验证命令一行式 | PASS | AC-4 拆出 fixture；AC-5/AC-6/AC-7/AC-8 合理多步 grep 链。 |
| 4 | 风险缓解 ↔ AC 测试 | PASS | 7 条风险均映射到 AC-3/AC-4/AC-6/AC-8 测试。 |
| 5 | commit parents 检查 | n/a | 无 commit 写入；`grep -nE "parents=\[\]" spec.md` = 0 |
| 6 | 反向 grep + test -f + 不吞 stderr | PASS | spec 无 `! grep`、无 `2>/dev/null`；所有 grep 都配 `test -f`。 |
| 7 | process_tasks 6 条 | PASS | tasks.md 含 6 条 P-* process_tasks。 |
| 8 | AC 验证命令 dry-parse | PASS | reviewer 本机用 `bash -n -c "<cmd>"` 对 AC-4 / AC-5 / AC-6 / AC-7 命令 dry-parse，4/4 PASS（无 SyntaxError）。 |
| 9 | summary.md 占位符残留 | PASS | `grep -cE "<feature-slug>\|<YYYY-MM-DDTHH:MM:SSZ>\|<复述\|<bullet list>" summary.md` = 0；MUST #1 同步解决了"18→19"。 |

### v3 regex 边界场景 dry-run（提示词要求复审）

reviewer 本机构造边界 spec 跑 v3 regex `^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|`：

| 输入行 | 命中 | 合理性 |
|---|---|---|
| `\| AC-1 \| behavioral \| ...`（标准两空格） | ✓ | 正常路径 |
| `\| AC-2\|behavioral\| ...`（无空格） | ✓ | `[[:space:]]*` 允许 0 空格 |
| `\| AC-3 \|  behavioral  \| ...`（多空格） | ✓ | 多空格亦覆盖 |
| `\| AC-4 \| **behavioral** \| ...`（加粗） | ✓ | `(\*\*)?` 可选加粗 |
| `\| AC-5a \| behavioral \| ...`（带 a 后缀） | ✓ | `[a-z]?` 兼容拆分子 AC 标识 |
| `\| AC-6 \| Behavioral \| ...`（大写首字母） | ✗ | **合理拒绝**：SKILL 规约 kind 取值是小写 `behavioral`；大小写敏感强制规约一致性 |
| `\| AC-7 \| static \| ... behavioral ...`（描述含字串） | ✗ | **核心打靶 PASS**：v3 不被描述文本误导 |

**边界场景全覆盖**；唯一未覆盖的"大写 `Behavioral`"是规约一致性的故意选择（SKILL 应统一小写），不构成缺陷。提示词担心的"单空格分隔单元格"已被 `[[:space:]]*` 自然覆盖。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md L113 AC-1 描述 + L114 AC-2 描述 + L115 AC-3 描述 | 这 3 条 AC 描述中各自含 "behavioral" 字串（"判定指引含 behavioral 三层"、"至少 1 条 behavioral AC" 等），即便 v3 regex 已锚定 AC 行不再受字串误导，但作为 dogfood 模范，未来 reviewer 看本 spec 时可能误以为"AC 描述里禁用 behavioral 字串"。建议在 SKILL 编辑指令（T-1a）里加一句"AC 描述允许提及 behavioral 概念，但 lint 只看 AC 行的 kind 单元格"避免读者困惑。 | 不阻塞 verdict；可在 T-1a 实施时顺便加。 |
| 2 | spec.md L82 + L134 风险表表述 | "不接受裸字串 `grep -q behavioral`" 已在风险表明示，但 SKILL.md 实施时应在"AC 分层规约"段落里也加一句"lint 实现细节：必须锚定 AC 行 kind 单元格 regex 而非全段字串搜索"，作为未来人类 reviewer / generator 复用本规约时的硬约束。 | 不阻塞；T-1a 实施时建议补。 |

## v2 → v3 增量缺陷扫描

- v3 修订集中在 spec.md L19 闭环表 + L81 AC-4 (ii) + L118 AC-6 + L134 风险表，以及 tasks.md T-4 (ii) + T-6 第三种 fixture-bad。**未发现 v2 已 CLOSED 项被 v3 反向破坏**。
- summary.md L57 唯一改动（18→19 + 两类拆分），与 spec L57 / AC-7 / 决策栏完全对齐，dogfood 闭环。
- 闭环表 SHOULD #4 描述准确性提升（13~102 行覆盖范围），证据更厚实。

## Verdict

**APPROVED**

理由（按 SKILL §3 唯一判据 = 未关闭 MUST FIX 数）：

- v2 2 MUST FIX 全闭环：MUST #1 summary.md 已改 19；MUST #2 双条件 (ii) 改锚定 AC 行 regex，reviewer 本机三层证据验证（本 spec 实测、反例 dry-run、边界场景）全部符合预期，机械化保护**真守门**。
- v2 5 SHOULD FIX 全闭环（含 SHOULD #5 即 AC-6 同型修复）。
- v3 未引入新 MUST FIX；2 条 NICE TO HAVE 不阻塞。
- 跨 AC 自审 9 条全 PASS（dry-parse 无 SyntaxError、占位符残留 = 0、process_tasks 齐全）。

dogfood 闭环坚实：本 change 自身 spec.md 用 v3 锚定 regex 计数 behavioral 行 = 2，恰好命中 AC-4 + AC-8；用 v2 缺陷 regex 会算成 8，差异即本 change 核心价值。

## 后续指引

- spec.md APPROVED → 进入 stage 3 编码实现（按 tasks.md T-1a → T-1b/T-1c/T-2/T-4/T-5 顺序展开）。
- 2 条 NICE TO HAVE 建议在 T-1a 实施编辑 SKILL.md 时顺手做掉（不阻塞 stage 3 启动）。
- T-6 fixture 必须包含"全 static + 描述含 behavioral 字串"的 fixture-bad-static-but-mention-behavioral 反例（v3 已写入 description），coding 阶段不可省略——这是本 change 机械化保护的最后一道门。
- summary.md 更新：stage 1 done v3 APPROVED；stage 2 done；进入 stage 3 in_progress。
