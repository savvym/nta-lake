---
change_id: platform-north-star-pivot-20260520
review_of: request_analysis/spec.md
reviewer: claude-stage2-reviewer
version: 1
authored_at: 2026-05-20T16:30:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 机械化检查清单

| # | 检查项 | 结果 | 说明 |
|---|---|---|---|
| M-1 | frontmatter 合法（change_id / version / authored_at / status / ac_kind_lint） | PASS | 五字段完整，格式规范 |
| M-2 | ac_kind_lint: exempt 合规性（git diff 无业务代码路径） | PASS | diff 12 个文件全在 `.harness/changes/platform-north-star-pivot-20260520/` 下，属 `.harness/*` 合法路径 |
| M-3 | AC-1 当前在未改 design.md 的状态下失败 | PASS | `awk '/^## 北极星/,/^## [^#]/' .harness/design.md \| grep -qE '数据加工厂\|data prep'` → 输出为空，返回非 0；符合"改后才 PASS"预期 |
| M-4 | C-1 ~ C-7 冲突在 design.md 真实存在 | PASS | 逐条验证：C-1(L18) / C-2(L69) / C-3(L119,132,145) / C-4(L192) / C-5(L264) / C-6(L294) / C-7(L331) 全部有据可查，无漏报/误报 |
| M-5 | spec 六个必要章节完整 | PASS | 背景/问题陈述/范围/非范围/验收标准/风险均存在 |
| M-6 | AC-1 awk 范围命令运行正确 | **FAIL** | `awk '/^## 北极星/,/^## [^#]/'` 存在根本性缺陷（见 MUST FIX #1） |
| M-7 | AC-3 awk 范围命令运行正确 | **FAIL** | 与 AC-1 同根因，`## 永不做` 头部匹配 `[^#]` 导致立即终止 |
| M-8 | AC-4 / AC-5 awk 范围命令运行正确 | **FAIL** | `## stats-first` / `## 行级血缘` 同根因 |
| M-9 | AC-2 awk 范围命令（### 级别）运行正确 | **FAIL** | `### Adapter` 满足 `/^### [^#]/`，同根因，范围立即终止 |
| M-10 | 后续 change 列表有 follow-up id | PASS | 7 个 follow-up 命名规范，排序合理 |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 复现命令 / 理由 | 建议修复 |
|---|---|---|---|---|
| 1 | spec.md §验收标准 AC-1 / AC-2 / AC-3 / AC-4 / AC-5，第 80-84 行 | **awk 范围 pattern 根本性错误**：`/^## 北极星/,/^## [^#]/` 中，开始行 `## 北极星` 自身也满足终止 pattern `/^## [^#]/`（因为 `[^#]` 能匹配空格/中文），导致 awk 在第一行就触发范围结束，整个正文被吞掉，只输出标题行。AC-1 的 bullet 计数永远为 0，AC-3/4/5 的内容 grep 永远失败。AC-2 的 `### Adapter` 与 `/^### [^#]/` 同理。 | `tmpfile=$(mktemp); printf '## 北极星\n- bullet 1\n- bullet 2\n\n## 下一节\n' > $tmpfile; awk '/^## 北极星/,/^## [^#]/' $tmpfile \| grep -cE '^- '` → 输出 `0`（预期 ≥ 2） | 把终止 pattern 改为不匹配同级中文节标题的形式，例如 `awk 'found && /^## /{exit} /^## 北极星/{found=1} found'`；或用 sed 截取。需对 AC-1/2/3/4/5 全部修正。 |
| 2 | spec.md §问题陈述，第 34 行 | 正文写"在 **6 个**具体地方与新北极星冲突"，但下方表格列了 C-1 ~ C-7 共 **7 条**。数字不一致会让实现者困惑是否漏了某条。 | 直接对照正文与表格 | 把正文"6 个"改为"7 个"，或说明哪条可合并 |

### SHOULD FIX

| # | 位置 | 问题 | 理由 | 建议 |
|---|---|---|---|---|
| 3 | spec.md §范围 D-11，第 62 行 | D-11 描述"**6 条 AC** 含 D-10 的 behavioral 调用"，但 §验收标准实际有 10 条 AC（AC-1 ~ AC-10），tasks.md T-11 也写"10 条 AC 全部转 bash run_ac 调用"。D-11 的"6"明显是笔误。 | 数字与实际产物矛盾 | 把 D-11 里"6 条 AC"改为"10 条 AC" |
| 4 | spec.md §风险，第 93-98 行 | 漏识别一条**高概率风险**：T-7 要把老章节标为"deprecated 设计（v1）"但"不删原文"以保留锚点。Markdown 锚点由标题文本自动生成——若在标题内加注"(deprecated v1)"，原锚点（如 `#12-设计原则`）即刻失效，与缓解方案矛盾。缓解方案未说明具体的 "保留锚点" 实现路径（是加 HTML `<a name="...">` 还是保持标题不变只在正文下加 deprecated 说明？）。 | 若锚点变了，21 个老 change 引用 404 风险无法被缓解 | 在 §风险 新增一条，并在 §范围 D-1/T-7 中说明"标 deprecated"的具体操作（例如：在节标题下方首行加 `> **[DEPRECATED v1]** v2 见 § <新节名>`，标题本身不变，锚点不受影响） |
| 5 | spec.md §风险，第 93-98 行 | 漏识别另一条风险：21 个已闭环 change 的 spec.md 里大量引用"Asset""Processor""Commit.parents[]"等旧概念词汇，本 change 不修这些文件，但新写 design.md 后两套术语共存，下一个 change 的 reviewer 读这些老 spec 时可能用旧心智评审新代码。 | 一致性/认知风险 | 在 §风险 新增一条，缓解方案可以是"D-8 rule 文件 + stage 2 评审 checklist 明确要求 reviewer 以新 design.md 为准" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 6 | spec.md §验收标准 AC-9，第 88 行 | AC-9 的 behavioral 描述期望"脚本在**当前** design.md 上 exit 0"，但脚本（T-10）要在 design.md 新结构写完后才有意义；"当前"容易被误读为"改动前的 design.md"。 | 把 AC-9 期望改为"脚本在**改写后**的 design.md 上 exit 0，且脚本在未修改的 design.md 上 exit 1（有明确指引）"，明确"改前失败、改后通过"的双向断言 |
| 7 | spec.md §范围 D-7，第 58 行 | D-7（§与业界的关系）在范围内列了，但 §验收标准没有对应 AC，tasks.md T-6 `covers_ac: []`。这是唯一一个 D-N 范围项没有 AC 覆盖的情况。 | 可新增 `AC-11 static`：`awk '/^## 与业界的关系/,/^## [^#]/' .harness/design.md \| grep -qE 'data-juicer\|The Stack\|Dolma\|lakeFS'`（使用修正后的 awk 写法） |

## 评审重点结论

### A. 北极星定位 vs 现 design.md 冲突识别
全部 7 条 C-N 均在 design.md 有对应真实锚点，无漏报/误报。4 轮决策日志的沉淀与 §范围 / §非范围 / §验收标准 的结论高度自洽，逻辑一致。

### B. 范围与非范围边界
D-1 ~ D-11 互不冲突，对"偶然碰非范围"的边界管控清晰（§交叉引用清单明确列出不动文件）。§非范围 的 7 项均明确点名了后续 follow-up change id，无"隐含延后"。

### C. AC 质量 — 关键缺陷
`ac_kind_lint: exempt` 本身合规，但 AC 命令质量存在系统性缺陷：AC-1/2/3/4/5 的 awk 范围 pattern 全部因"开始行匹配终止 pattern"而立即终止，导致这 5 条 AC 在改完 design.md 后仍然会返回错误值。这是 MUST FIX 级别问题，**不修复将导致 stage 5 T-12 全线 FAIL，stage 8 CI 无法通过**。

### D. 风险识别
现有 4 条风险均合理，但漏了两条中级风险："deprecated 标记锚点失效"和"老 change 旧术语双轨并存"（见 SHOULD FIX #4/#5）。

### E. 决策日志真实性
4 条决策的结论在 spec 内部自洽（例如"砍 branch/merge"→ §非范围 + § 永不做清单；"三层算子"→ D-3/D-4/D-5；"row-embedded source_ref"→ D-5 行级血缘）。reviewer 无法复核原始对话，但内部逻辑无矛盾。

## Verdict

**REVISION REQUIRED**

MUST FIX 2 条，其中 M-1（awk 命令缺陷）影响 AC-1/2/3/4/5 共 5 条验收标准，若不修复 stage 5 将全线 FAIL。

## 后续指引

作者需修改 spec.md（不需要新建 v2 文件，直接在 v1 上改并更新 `version: 2` / `authored_at`）：

1. **MUST FIX #1**：把 AC-1/AC-2/AC-3/AC-4/AC-5 里所有 `awk '/^## X/,/^## [^#]/'` 改为不会在标题行自我终止的写法。推荐模式：
   ```bash
   awk 'found && /^## /{exit} /^## 北极星/{found=1} found' .harness/design.md
   ```
   AC-2 的 `### Adapter` 改为：
   ```bash
   awk "found && /^### /{exit} /^### Adapter/{found=1} found" .harness/design.md
   ```
2. **MUST FIX #2**：把第 34 行"6 个具体地方"改为"7 个具体地方"。
3. **SHOULD FIX #3**：把 D-11 里"6 条 AC"改为"10 条 AC"。
4. **SHOULD FIX #4/#5**：在 §风险 补充锚点变更风险和术语双轨并存风险，并在 T-7 description 中说明 deprecated 标记的具体格式（标题行不变，正文首行加 blockquote 注释）。

修完后提交 `spec_review_v2.md`（reviewer 重点复核 AC-1/2/3/4/5 命令的修正结果）。
