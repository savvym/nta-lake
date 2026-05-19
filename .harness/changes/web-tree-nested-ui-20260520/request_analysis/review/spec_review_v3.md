---
change_id: web-tree-nested-ui-20260520
target: spec.md
target_version: 3
review_version: 3
reviewer: claude-agent:web-tree-nested-ui-20260520-stage2-reviewer-v3
reviewed_at: 2026-05-19T18:30:00Z
verdict: REVISION REQUIRED
---

# Spec Review v3

## v2 MUST FIX 复检

| # | v2 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | AC-6 `numTotalTests>=4` 断言无基线，"≥ 4 新用例"约束形同虚设 | PARTIAL — 命令已修，但表格"期望"列未同步（见下方新 MUST FIX-1） | AC-6 完整命令第 2 行：`assert d['numTotalTests']>=5` ✅；但 AC 表期望列仍写 `numTotalTests ≥ 已有数+4 且 numFailedTests == 0`（模糊表述未清除）❌ |
| MUST FIX-2 | 标题 + 受影响模块 + 自审仍写 "12 AC" | RESOLVED | `## 验收标准（11 AC，**3 behavioral**…）` ✅；受影响模块 `追加 run_web_tree_nested_ui 11 AC` ✅；无任何 "12 AC" 字样 ✅ |
| MUST FIX-3 | AC-11 表格 kind 标 `behavioral`，实质 static grep；自审 "4 behavioral" 矛盾 | RESOLVED | AC-11 行：`\| AC-11 \| static \|` ✅；自审第 4 条：`AC 分层：3 behavioral（AC-6 / AC-7 / AC-10）` ✅ |

---

## 检查清单结论（plan 模式）

| 项 | 状态 | 说明 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | tree-nested-domain merge 后 UI 退化，背景清晰 |
| 问题陈述与目标可被外部读者理解 | PASS | 问题陈述具体，含代码路径与预期失败场景 |
| 范围 / 非范围都有 | PASS | In scope / Out of scope 均明确 |
| 验收标准每条都可演示且可机械化 | PARTIAL — 见 MUST FIX-1 | AC-6 期望列与命令不一致 |
| 风险有缓解措施或显式 accept | PASS | 8 条风险，每条均有缓解或 accept 声明 |
| 没有把已有架构当新提案重复 | PASS | 未重复 design.md 内容 |
| AC 表存在 kind 列 | PASS | 表头含 kind 列 |
| 至少 1 行 AC kind=behavioral（锚定 regex） | PASS | AC-6 / AC-7 / AC-10 均为 behavioral |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md §验收标准 AC-6 行"期望"列 | **AC-6 期望列与命令不一致**：AC 表期望列仍写 `numTotalTests ≥ 已有数+4 且 numFailedTests == 0`，使用了模糊的相对表述 "已有数+4"；而 AC-6 完整命令已改为硬编码 `assert d['numTotalTests']>=5`，两者含义不统一。表格是 coding agent 实现时的规范来源；保留模糊期望列会导致 coding agent 无法独立自查是否满足 AC-6（不知道"已有数"是多少）。v2 MUST FIX-1 要求修写死绝对值，命令已修但表格期望列遗漏。 | 将 AC-6 行"期望"列改为：`numTotalTests ≥ 5（baseline 1 + 新增 ≥4）且 numFailedTests == 0`，与命令保持一致。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md §风险 第 5 行 | 风险缓解写 `AC-11 显式覆盖`（指"现有 test.tsx 断言与新逻辑冲突 → AC-11 显式覆盖"），但 AC-11 实际验证的是 path 默认值（静态 grep），不是测试不冲突。真正覆盖此风险的是 AC-7 / AC-10（vitest run 全 PASS）。这是 v2 SHOULD FIX-5 的遗留。 | 将风险第 5 行缓解栏改为 `AC-7 / AC-10 显式覆盖；改测试时保留原"扁平 commit 渲染"断言为 legacy 用例`。 |
| SHOULD FIX-2 | spec.md §AC-9 描述 | AC-9 描述含 `（AC-9 也兼自递归）`，"自递归"含义模糊，未说明指 self_check 自身递归调用还是 AC 验证自身注册。v2 SHOULD FIX-2 未修。 | 删除 `（AC-9 也兼自递归）` 括号注释，或写明 "自递归" 指的是具体机制；如无独立含义直接删除。 |
| SHOULD FIX-3 | spec.md §AC-6 完整命令 | `--reporter json` 将 JSON 输出到 stdout，但 stderr 警告可能混入，导致 `json.load()` 报 `JSONDecodeError`。v2 SHOULD FIX-3 未修。 | 改用 `--reporter=json --outputFile=/tmp/web-tree-nested-vitest.json`（vitest 支持 `--outputFile`），避免 stdout 混入 stderr。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md §AC-11 完整命令 | regex 使用 `\x27` 表示单引号，在 macOS BSD grep 下不被支持。v2 SHOULD FIX-1 未修（已降 NTH）。 | 改用字符类 `["']{2}` 或明确要求实现使用 `.default("")`（双引号）避免 regex 跨平台问题。 |
| NTH-2 | spec.md §AC-11 | regex 不覆盖 `z.string().optional().default("")`（chain 顺序不同时失效）。v2 NTH-2 未修。 | 在 spec 明确"实现必须用 `.string().default("")`，不得插入 `.optional()`"，与 AC-11 regex 约束对齐。 |

---

## Verdict

**REVISION REQUIRED**

存在 1 条 MUST FIX：

- **MUST FIX-1**：AC-6 期望列仍写 `numTotalTests ≥ 已有数+4`（模糊相对值），与命令中已修的 `>=5` 不一致；表格期望列是 coding agent 的规范来源，不一致会导致实现/自查混乱。

v2 的 MUST FIX-2（"12 AC" 残留）和 MUST FIX-3（AC-11 kind 错标）均已正确修复，无回归。v3 引入的唯一问题是 v2 MUST FIX-1 的**部分修复**（命令已修、表格遗漏）。

---

## 后续指引

Generator 修完 v4 spec 后自查：

```bash
# 1. AC-6 期望列必须含写死数字 5（不含"已有数"）
grep "AC-6" .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  | grep -v "已有数" | grep -qE "numTotalTests[[:space:]]*[≥>=]+[[:space:]]*5" \
  && echo "AC-6 期望列 PASS" || echo "AC-6 期望列 FAIL"

# 2. AC-6 命令仍含 >=5
grep "numTotalTests>=5\|numTotalTests >= 5" \
  .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  && echo "AC-6 命令 PASS" || echo "AC-6 命令 FAIL"

# 3. 无 "12 AC" 残留（应已无）
! grep -q "12 AC" .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  && echo "无 12 AC PASS" || echo "仍有 12 AC FAIL"

# 4. AC-11 kind=static
grep "AC-11" .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  | grep -qv "behavioral" && echo "AC-11 kind PASS" || echo "AC-11 kind FAIL"
```

v4 修完后 spawn reviewer v4 复检。
