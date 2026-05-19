---
change_id: web-tree-nested-ui-20260520
target: tasks.md
target_version: 3
review_version: 3
reviewer: claude-agent:web-tree-nested-ui-20260520-stage2-reviewer-v3
reviewed_at: 2026-05-19T18:30:00Z
verdict: APPROVED
---

# Tasks Review v3

## v2 MUST FIX 复检

| # | v2 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | T-2 description 示例 `.optional()` 与 AC-11 grep regex 冲突，按 T-2 实现会导致 AC-11 FAIL | RESOLVED | T-2 description 已改为：`path: z.string().default("") 或 .catch("") 形态，确保默认空串而非 undefined`；无 `.optional()` 字样；与 AC-11 grep regex `(default\(["\x27]{2}\)|catch\(["\x27]{2}\))` 一致 ✅ |
| MUST FIX-2 | T-5 estimated_stage 仍为 `ci_result`，应为 `coding` | RESOLVED | T-5 `estimated_stage: coding` ✅ |

---

## 检查清单结论（plan 模式）

| 项 | 状态 | 说明 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PASS | T-1~T-2 各 ~1h，T-3a ~1.5h，T-3b ~2.5h，T-4/T-5/T-6 各 1-2h |
| depends_on 形成 DAG，没有循环 | PASS | T-1→T-2→T-3a→T-3b→T-4→T-5→T-6 线性链，无环 |
| 评审 / 单测 / CI 阶段对应任务都存在 | PASS | process_tasks 含 P-spec-review / P-code-review / P-test-review / P-push / P-ci / P-deploy / P-user-confirm（7 节点全覆盖） |
| 没有 "做完整个系统" 类目标性任务 | PASS | 每个任务指向具体文件和操作 |
| AC 覆盖完整（每条 AC 有对应任务） | PASS | AC-1~AC-11 全部在覆盖表中有归宿；T-5 title 写 "11 AC" 与 spec v3 一致 |
| estimated_stage 与十阶段定义对齐 | PASS | T-5 已改为 `coding`；T-4 = unit_test；T-6 = ci_result；全部对齐 |

---

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-2 description | `tab 切换时保留 path（或重置到 ""），看交互期望` — "看交互期望"歧义未消除（v2 SHOULD FIX-1 遗留）。coding agent 实现时会在两种行为间随机选择。 | 待 spec 明确 tab 切换 path 行为后，T-2 description 同步改为明确语义，如 `tab 切换时重置 path 为 ""`。 |
| SHOULD FIX-2 | tasks.md T-4 description | 用例命名沿用下划线风格（`test_default_root_shows_mixed_entries`），与现有基线的 `it("...")` 字符串风格不一致（v2 SHOULD FIX-2 遗留）。 | 将 T-4 用例名改为 it/describe 字符串风格，如 `it('root shows mixed entries with folder and blob rows', ...)`。 |
| SHOULD FIX-3 | tasks.md T-4 description | mock 策略写 `mock useSearch + useSubtreeByPath（或直接 fetch fixture）`，两种策略并存（v2 SHOULD FIX-3 遗留）。 | 明确使用 `vi.mock('../lib/api/queries', ...)` mock `useSubtreeByPath`；删除"或直接 fetch fixture"歧义项。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md T-3b | `role="button" + tabIndex + onKeyDown Enter` 方案语义弱于 native `<button>`（v2 NTH-2 遗留）。 | 若 spec 加入 `<button>` 约束，T-3b 同步修正。 |
| NTH-2 | tasks.md process_tasks P-user-confirm | P-user-confirm description 无内容（v2 NTH-3 遗留）。 | 建议加一行"手测验证 HF 风树形导航 + 面包屑 + legacy 兼容"，供 stage 10 参考。 |

---

## Verdict

**APPROVED**

v2 的 2 条 MUST FIX 均已正确修复，无回归：T-2 description 已对齐 `.default("")`，T-5 estimated_stage 已改为 `coding`。v3 tasks 无新 MUST FIX。

注意：**spec v3 仍有 1 条 MUST FIX**（AC-6 期望列模糊，见 spec_review_v3），tasks 虽 APPROVED，整体 stage 2 仍需等 spec 修到 v4 并通过评审后方可进入 stage 3。

---

## 后续指引

Tasks 已通过，等 spec v4 APPROVED 后进入 stage 3（coding）。

spec generator 修 v4 时仅需改 AC-6 期望列（1 处），无需重改 tasks。v4 提交后 spawn spec reviewer v4 单独复检，tasks 不需要再跑一轮。
