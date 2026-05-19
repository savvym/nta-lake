---
change_id: web-tree-nested-ui-20260520
target: spec.md
target_version: 4
review_version: 4
reviewer: claude-agent:web-tree-nested-ui-20260520-stage2-reviewer-v4
reviewed_at: 2026-05-19T19:10:00Z
verdict: APPROVED
---

# Spec Review v4

## v3 MUST FIX 复检

| # | v3 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | AC-6 期望列仍写 `numTotalTests ≥ 已有数+4`（模糊相对值），与命令中已修的 `>=5` 不一致 | RESOLVED | spec.md 第 107 行 AC-6 期望列：`numTotalTests ≥ 5（baseline 1 + 新增 ≥ 4）且 numFailedTests == 0` ✅；第 119 行命令：`assert d['numTotalTests']>=5` ✅；两处均用绝对值 5，"已有数" 字串已清零 ✅ |

---

## 检查清单结论（plan 模式）

| 项 | 状态 | 说明 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | tree-nested-domain merge 后 UI 退化，背景清晰 |
| 问题陈述与目标可被外部读者理解 | PASS | 问题陈述含代码路径与预期失败场景，外部读者可理解 |
| 范围 / 非范围都有 | PASS | In scope / Out of scope 均明确 |
| 验收标准每条都可演示且可机械化 | PASS | AC-6 期望列已与命令一致；所有 11 条 AC 均可机械化验证 |
| 风险有缓解措施或显式 accept | PASS | 8 条风险，每条均有缓解或 accept 声明 |
| 没有把已有架构当新提案重复 | PASS | 未重复 design.md 内容 |
| AC 表存在 kind 列 | PASS | 表头含 `kind` 列 |
| 至少 1 行 AC kind=behavioral（锚定 regex） | PASS | AC-6 / AC-7 / AC-10 均为 `behavioral`，AC 表第 107/109/111 行可用 awk+regex 锚定确认 |

---

## 问题列表

### MUST FIX

无。

### SHOULD FIX

> 以下为 v3 遗留 SHOULD FIX，未修。不阻塞 APPROVED，但 generator 应在 summary.md 写明 deferred 理由。

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md §风险 第 5 行 | 风险缓解写 `AC-11 显式覆盖`，但 AC-11 验证的是 path 默认值（静态 grep），不是测试不冲突。真正覆盖此风险的是 AC-7 / AC-10。（v3 遗留，未修） | 将风险第 5 行缓解栏改为 `AC-7 / AC-10 显式覆盖；改测试时保留原"扁平 commit 渲染"断言为 legacy 用例` |
| SHOULD FIX-2 | spec.md §AC-9 描述 | `（AC-9 也兼自递归）` 含义模糊。（v3 遗留，未修） | 删除该括号注释，或写明"自递归"指的是具体机制 |
| SHOULD FIX-3 | spec.md §AC-6 完整命令 | `--reporter json` 将 JSON 输出到 stdout，stderr 警告可能混入导致 `json.load()` 报 `JSONDecodeError`。（v3 遗留，未修） | 改用 `--reporter=json --outputFile=/tmp/web-tree-nested-vitest.json`，避免 stdout 混入 stderr |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md §AC-11 完整命令 | regex 使用 `\x27` 表示单引号，macOS BSD grep 不支持。（v3 遗留，已降 NTH，未修） | 改用字符类 `["']{2}` 或要求实现使用 `.default("")` 双引号避免跨平台问题 |
| NTH-2 | spec.md §AC-11 | regex 不覆盖 `z.string().optional().default("")`（chain 顺序不同时失效）。（v3 遗留，未修） | 在 spec 明确"实现必须用 `.string().default("")`，不得插入 `.optional()`" |

---

## Verdict

**APPROVED**

v3 唯一 MUST FIX（AC-6 期望列模糊相对值残留）已在 v4 正确修复：

- spec.md 第 107 行 AC-6 期望列由 `numTotalTests ≥ 已有数+4` 改为 `numTotalTests ≥ 5（baseline 1 + 新增 ≥ 4）且 numFailedTests == 0`，与第 119 行命令 `assert d['numTotalTests']>=5` 完全一致。
- "已有数" 字串已从表格消除（全文 grep 无命中）。
- v3 的 MUST FIX-2（"12 AC" 残留）、MUST FIX-3（AC-11 kind 错标）均维持已修状态，无回归。

3 条 SHOULD FIX 和 2 条 NTH 均为 v3 遗留、不阻塞流程，generator 应在 summary.md 记录 deferred 处置。

---

## 后续指引

APPROVED → 进入 **stage 3（编码）**：

- Generator 按 tasks.md 实现 AC-1 ～ AC-11。
- 实现完成后 generator 写 `coding/coding_report.md` + 提 stage 4 reviewer spawn。
- SHOULD FIX-1/2/3 建议在 coding 阶段顺手修（尤其 SHOULD FIX-3 影响 AC-6 命令可靠性），或在 summary.md 中显式 deferred。

```bash
# 复检指引（供未来 reviewer 参考）
# AC-6 期望列无"已有数"，含绝对值 5
grep "AC-6" .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  | grep -v "已有数" | grep -qE "numTotalTests[[:space:]]*[≥>=]+[[:space:]]*5" \
  && echo "AC-6 期望列 PASS" || echo "AC-6 期望列 FAIL"

# AC-6 python 命令含 >=5
grep -q "numTotalTests'\]>=5\|numTotalTests\"]>=5" \
  .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  && echo "AC-6 命令 PASS" || echo "AC-6 命令 FAIL"
```
