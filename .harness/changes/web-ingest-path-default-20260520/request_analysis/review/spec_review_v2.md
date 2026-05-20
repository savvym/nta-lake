---
change_id: web-ingest-path-default-20260520
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-agent:web-ingest-path-default-20260520-stage2-reviewer-v2
reviewed_at: 2026-05-20T12:00:00Z
verdict: APPROVED
---

# Spec Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST-1 | AC-3 空转——behavioral AC 无任何 IngestSection.onFiles 行为覆盖 | RESOLVED | v2 拆出 AC-3a（新增 `repos.ingest-section.test.tsx`，JSON reporter 验证 numTotalTests≥1 + 0 fail）+ AC-3b（全 vitest 回归）；范围 § 已明确 "新增 IngestSection 单测" 且 AC-3a 给出可机械化的验证命令 |
| MUST-2 | AC-2 grep 语义过窄（漏匹配 `"content/xxx"` 形态）+ prose 与 6 处合理 display fixture 矛盾 | RESOLVED | v2 整体删除 AC-2；改以 IngestSection 单测断言（AC-3a）替代 grep；6 处 display fixture 保留合理性在范围 § AC-3a 注脚中显式声明 |
| MUST-3 | AC-5 与 AC-6 验证命令完全相同，AC-6 形同重复 | RESOLVED | v2 删除 AC-6，AC 数从 6→5；AC-5 描述追加"兼自递归"；frontmatter revision_notes 中有明确说明 |

## 检查清单结论（plan 模式）

| 条目 | 状态 | 备注 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | tree-nested-domain 合并后副作用明确 |
| 问题陈述与目标可被外部读者理解 | PASS | 清晰 |
| 范围 / 非范围都有 | PASS | in scope / out of scope 俱全，且 AC-3a 注脚显式说明 display fixture 保留 |
| 验收标准每条都可演示且可机械化 | PASS | AC-1/AC-3a/AC-3b/AC-4/AC-5 均有可执行验证命令；AC-3a 用 JSON reporter + python3 断言精确 |
| 风险有缓解措施或显式 accept | PASS | blob-dir 冲突风险已精化为"同一批次同名文件才触发"，跨 commit 已明确不冲突 |
| 没有把已有架构当新提案重复 | PASS | |
| AC 表存在 `kind` 列 | PASS | 5 行均含 kind 列 |
| 至少 1 行 AC kind=behavioral（锚定 regex） | PASS | AC-3a / AC-3b / AC-4 均为 behavioral（3 行）|

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD-1 | spec.md §验收标准 表头 + 跨链路自审 #4 | 表头写"5 AC，**2 behavioral**：AC-3b / AC-4；AC-3a 也 behavioral 一并算 3 条"——同一句话先说"2 behavioral"后又说"算 3 条"，自相矛盾。跨链路自审 #4 写"AC 分层：2 behavioral"，实际上 behavioral 共 3 条（AC-3a / AC-3b / AC-4）。虽然不影响 AC 本身机械化正确性，但会混淆 coder 对回归保护强度的判断。 | 统一改为"3 behavioral（AC-3a / AC-3b / AC-4）"；同步更新自审 #4。 |
| SHOULD-2 | spec.md 跨链路自审 #8 | "process_tasks 6 节点齐"——实测 tasks.md 含 7 个 process_tasks 节点（P-spec-review / P-code-review / P-test-review / P-push / P-ci / P-deploy / P-user-confirm），自审计数与实际不符。 | 改为"process_tasks 7 节点齐"。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md AC-3a 验证命令 | `grep -E '^{' /tmp/ingest.raw > /tmp/ingest.json` 依赖 vitest JSON reporter 输出第一个非空行以 `{` 开头。若 vitest 版本或 pnpm 输出环境有 ANSI 前缀行，`grep '^{'` 可能抓不到。建议改为 `grep -E '^\{"' /tmp/ingest.raw`（要求 key 也以引号开头，更鲁棒）或在命令注释中说明 vitest 版本要求。 | 加注释说明 vitest 版本前提，或改用更窄的 pattern `grep -E '^\{"'`。 |

## Verdict

**APPROVED**

v1 三条 MUST FIX 全部 RESOLVED（AC-3a 补行为覆盖、AC-2 删除重构、AC-5/AC-6 合并）。现有 AC 5 条均可机械化验证，behavioral 分层满足（3 行 behavioral）。发现 2 条 SHOULD FIX（表头/自审 behavioral 计数前后矛盾、process_tasks 计数错误）和 1 条 NTH（AC-3a grep 命令轻微脆弱），均不阻塞实现正确性与回归保护。

## 后续指引

APPROVED → generator 可进入 stage 3 编码实现。建议在 coding 阶段顺手修复：
1. spec.md 表头/自审 behavioral 计数统一为 3（SHOULD-1）
2. spec.md 自审 #8 计数改为 7（SHOULD-2）
若不修，需在 `summary.md` deferred 条目中记录。
