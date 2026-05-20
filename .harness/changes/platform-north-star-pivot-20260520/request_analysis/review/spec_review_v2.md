---
change_id: platform-north-star-pivot-20260520
review_of: request_analysis/spec.md
reviewer: claude-stage2-reviewer
version: 2
authored_at: 2026-05-20T17:30:00Z
verdict: APPROVED
---

# Spec Review v2

## v1 五条问题复核（逐条 RESOLVED / NOT / PARTIALLY + 证据）

### MUST FIX #1（awk pattern bug，影响 AC-1/2/3/4/5）— **RESOLVED**

**修复内容：** 所有受影响 AC 的 awk 范围 pattern 改为 flag-based。普通节用 `awk 'found && /^## /{exit} /^## X/{found=1} found'`，三级节用 `awk -v k="$k" 'found && /^### /{exit} $0 ~ "^### "k{found=1} found'`。

**证据：**
- spec.md 第 91-96 行 grep 验证：5 处 `found && /^## /{exit}` + 1 处 `found && /^### /{exit}`。
- 跑当前未改 design.md：
  - AC-1: `awk 'found && /^## /{exit} /^## 北极星/{found=1} found' .harness/design.md` → 输出为空（正确：当前 design.md 无北极星节）。
  - AC-3: 同样输出为空。
- 跑 fixture（模拟 stage 3 完成后状态，含北极星/永不做/三层算子/stats-first/行级血缘/迁移路径六节）：AC-1/2/3/4/5/6 全部 **PASS**。
- 边界 1（目标节是文件末尾，无 `## ` 终止）：AC-1 bullet 计数仍为 4，grep 命中 — PASS。
- 边界 2（节内含 `### ` 子标题）：终止 pattern `/^## /` 不会被 `### ` 误触发 — PASS。
- 边界 4（AC-2 `### Adapter` 内含 `#### ` 子子节）：`/^### /` 不会被 `#### ` 误触发 — PASS。
- 边界 5（AC-2 `### Operator` 是文件最后节）：直到 EOF 才退出 — PASS。

### MUST FIX #2（"6 个" → "7 个"）— **RESOLVED**

第 45 行确认为 "design.md 当前版本在 7 个具体地方与新北极星冲突"，与 C-1 ~ C-7 表对齐。

### SHOULD FIX #1（D-11 "6 条 AC" → "10 条 AC"）— **RESOLVED**

第 73 行 D-11 确认为 "10 条 AC 含 D-10 的 behavioral 调用"，与 §验收标准表 + tasks.md T-11 一致。

### SHOULD FIX #2（R-5 deprecated 锚点失效）— **RESOLVED**

第 110 行 R-5 给出具体方案：
> markdown 锚点是 `## section-name` 小写连字符自动生成；T-7 不动老 § 的二级标题文字（如 `## 1. 目标与设计原则`），只在该 § 顶端插入一个 `> ⚠ Deprecated 设计（v1）。v2 见 § <新章节链接>` quote 块。锚点不变，引用不会 404

技术上正确：GFM 锚点由标题文本决定，标题文本不变 → 锚点不变 → 老 change 引用不死链。具体格式（quote 块 + 标题不动）可直接落到 T-7 实施。

### SHOULD FIX #3（R-6 旧术语双轨并存）— **RESOLVED**

第 111 行 R-6 给出 4 步缓解：
- (a) `rules/data-not-code-pivot.md` 列旧→新术语对照表
- (b) design.md § 迁移路径表标注 5 个 processor 当前用哪些旧术语
- (c) 旧 change 文档不改动；新 change 评审 reviewer 必须查"v2 词汇"
- (d) 6 个月后再决定要不要批量回写

四步均可操作。**部分细节未传导到 tasks**（见下方新发现 SHOULD FIX #2）。

## 新发现问题

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 复现/理由 | 建议 |
|---|---|---|---|---|
| 1 | spec.md §验收标准 AC-1 第 91 行 grep `'LLM 训练数据.{0,5}工厂'` | 量词 `.{0,5}` 在 UTF-8 locale 下按字符计数（GNU grep 默认），允许最多 5 个中文字符；在 `LC_ALL=C` 下按字节计数 ≈ 1.6 个中文字符。CI 与 dev 环境 locale 不一致时 AC-1 行为可能漂移。 | `echo 'LLM 训练数据预处理工厂' \| LC_ALL=C grep -qE 'LLM 训练数据.{0,5}工厂'` vs `LC_ALL=en_US.UTF-8 grep ...` 实测在两种 locale 下都 match（GNU grep multibyte 兼容性），但其他 grep 实现（busybox）可能不一致。 | 在 AC-1 的验证命令前加 `LC_ALL=C.UTF-8` 显式声明 locale；或把 `.{0,5}` 改为更明确的 `[^|]*`（限定不跨表格列）/ `.{0,10}`（更宽松防误失败）。可选 NICE TO HAVE。 |
| 2 | spec.md §风险 R-5 / R-6 ↔ tasks.md T-7 / T-8 / T-5 不同步 | R-5 给出 deprecated 标记的具体格式（quote 块 + 不改标题），但 T-7 description 仍只写 "标 deprecated 子节 + v2 指针"，没引用 R-5 具体格式。R-6 (a)(b) 要求 `data-not-code-pivot.md` 含术语对照表 + 迁移路径标注旧术语，但 T-8 description 只说 "永不做清单 + 评审必须确认不违反"，T-5 description 只说 "name / current / new / follow-up"，对照表和旧术语标注都没纳入 task 交付物。 | 直接对照 spec R-5/R-6 与 tasks.md T-5/T-7/T-8 的 description。 | 在 stage 3 coding 开始前，把 T-5/T-7/T-8 的 description 补全（不影响 v2 spec 评审通过；只需在 coding kickoff 时口头/批注同步）；或下次 tasks 更新时一并修。 |
| 3 | spec.md §风险 R-6 (c) "reviewer 必须查 v2 词汇" 缺执行点归属 | R-6 (c) 说 "新 change 评审 reviewer 必须查是否用了 v2 词汇"，但 spec §非范围 第 121 行明确 "不动 `.harness/rules/development-process.md`"。reviewer 在哪个 checklist / SOP 里看到这条要求？目前唯一可挂的是 `rules/data-not-code-pivot.md`（T-8 产出），但 T-8 description 没明确这点。 | "reviewer 必须查" 没有执行触发点，等同于口头承诺。 | 在 T-8 description 里加一句 "rule 文件含 'stage 2 reviewer checklist' 章节，列出 reviewer 必查的 v2 词汇项"；或在 spec R-6 (c) 末尾补一句 "落地点：`data-not-code-pivot.md` 的 reviewer-checklist 子节"。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 4 | spec.md AC-2 awk pattern `$0 ~ "^### "k` 是**前缀**匹配 | 如果 design.md 有 `### AdapterRegistry` 在 `### Adapter` 之前，awk 会先匹配到 `AdapterRegistry`（其 Protocol/class 可能命中也可能不命中）。实际 design.md 不太可能有这种命名，但 pattern 不够严格。 | 改为 `$0 ~ "^### "k"$"` 或 `$0 ~ "^### "k"( \|$)"`（要求 k 后面是空格或行尾），避免前缀误匹配。 |
| 5 | spec.md R-5 缓解描述例子用 `## 1. 目标与设计原则`（二级标题） | 但 T-7 description 列出的实际要改的是 `### 1.2 设计原则` / `### 2.2 概念定义` / `### 3.1 Bronze` / `### 4.2 Processor` / `### 4.3 Recipe` —— 全部是**三级**标题。R-5 策略对二/三级都适用，例子选错只是文字 polish。 | R-5 例子括号补充："例子：## 或 ### 标题文字不动，顶端插 quote 块即可" |
| 6 | spec.md AC-1 grep `'LLM 训练数据.{0,5}工厂\|data prep'` | "data prep" 太短，可能命中 design.md 任意"prep"出现的地方（如 "data preparation"）；但限定在 § 北极星 节内 + 应该是文字概念正词命中，误报概率低。 | 收紧为 `data prep(aration)? factory` 或 `data prep(aration)?` 紧跟 "platform/factory"。可选。 |
| 7 | spec.md frontmatter `authored_at: 2026-05-20T15:00:00Z` 未更新，新增 `revised_at: 2026-05-20T15:30:00Z` | revision_log 已正确填，但 frontmatter 中 v1 与 v2 共享同一 `authored_at`，仅靠 `revised_at` 区分。其他 change 的惯例是直接更新 authored_at。 | 此项不阻塞；下次按惯例可统一。 |

## 机械化检查清单

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| M-1 | frontmatter 含 `revision_log` 列出 5 条 fix | PASS | spec.md 第 13-22 行 |
| M-2 | §问题陈述 第 45 行 "7 个" | PASS | grep "7 个具体地方" 命中 |
| M-3 | §范围 D-11 第 73 行 "10 条 AC" | PASS | grep "10 条 AC" 命中 |
| M-4 | §风险 R-1 ~ R-6 编号完整 | PASS | grep 显示 R-1/R-2/R-3/R-4/R-5/R-6 全部存在 |
| M-5 | AC-1/3/4/5/6 awk 改为 flag-based `^## ` 终止 | PASS | grep 计数: 5 处 |
| M-6 | AC-2 awk 改为 flag-based `^### ` 终止 | PASS | grep 计数: 1 处 |
| M-7 | AC-1 grep 已放宽为正则 `LLM 训练数据.{0,5}工厂\|data prep` | PASS | spec.md 第 91 行确认 |
| M-8 | fixture（stage 3 完成模拟）跑全部 6 个 awk-based AC | PASS | 自构 fixture，AC-1/2/3/4/5/6 全 PASS |
| M-9 | 当前未改 design.md 跑 AC-1/3 应失败 | PASS | awk 输出为空，AC 整体返回非零 |
| M-10 | 边界：目标节是文件末尾 | PASS | 自构 fixture 验证，无截断 |
| M-11 | 边界：节内含 `### ` 子标题 | PASS | `^## ` 终止 pattern 不被 `### ` 误触发 |
| M-12 | 边界：AC-2 三层算子内含 `#### ` 子子节 | PASS | `^### ` 终止 pattern 不被 `#### ` 误触发 |
| M-13 | 边界：AC-2 Operator 是文件最后节 | PASS | 输出到 EOF 自然结束 |
| M-14 | R-5 markdown 锚点假设技术正确性 | PASS | GFM 锚点由标题文本生成，标题不变则锚点不变 |
| M-15 | git diff --stat origin/main..HEAD 仅含 `.harness/*` 路径 | PASS | 12 个文件全在 `.harness/changes/...` 下 |

## Verdict

**APPROVED**

v1 所有 5 条问题均 RESOLVED，证据充分。awk 新 pattern 在所有可预见的边界情况（节是文件末尾、节内含子标题、节内含子子节、节后接同级节）下均行为正确，已用自构 fixture 跑过全部 6 个 awk-based AC 全 PASS。

新发现 3 条 SHOULD FIX 不阻塞通过：
- #1 locale 漂移是潜在脆性，主流环境无问题。
- #2 R-5/R-6 → tasks 不同步可在 stage 3 coding kickoff 时口头/批注同步，不需要回退 stage 1。
- #3 R-6 (c) 执行点归属属于"实施细节优化"，建议在 T-8 实施时补一句即可。

4 条 NICE TO HAVE 均为文字打磨/严格化建议，不影响 spec 质量。

## 后续指引

1. **进入 stage 3 coding**，按 tasks.md T-1 → T-12 顺序执行。
2. **coding kickoff 时口头 / 在 coding/coding_report_v1.md 里注明**：
   - T-7 实施按 R-5 具体格式：标题文字不动，顶端插 `> ⚠ Deprecated 设计（v1）。v2 见 § <新章节链接>` quote 块。
   - T-8 实施时在 `data-not-code-pivot.md` 加 "stage 2 reviewer checklist" 子节，列出旧→新术语对照表（落实 R-6 (a)/(c)）。
   - T-5 迁移路径表加一列 "currently 使用旧术语"（落实 R-6 (b)）。
3. **AC-2 前缀匹配（NICE #4）** 可在 T-11 写 self_check block 时收紧为 `"^### "k"( \|$)"`，避免 follow-up change 触雷。
4. **进入 stage 4 code review 时**，reviewer 额外验证：
   - 老 § 顶端的 deprecated quote 块格式与 R-5 一致。
   - `data-not-code-pivot.md` 含术语对照表 + reviewer checklist 子节（除 AC-7 要求外的额外检查）。
5. tasks.md v1 已 APPROVED，无需重新评审。
