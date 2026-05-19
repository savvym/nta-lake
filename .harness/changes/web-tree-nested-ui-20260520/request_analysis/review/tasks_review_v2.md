---
change_id: web-tree-nested-ui-20260520
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-agent:web-tree-nested-ui-20260520-stage2-reviewer-v2
reviewed_at: 2026-05-19T18:00:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | T-3 超大任务（6 子功能，5-8h），超出 1-3h 粒度上限 | RESOLVED | v2 拆为 T-3a（数据层，~1.5h）+ T-3b（表现层，~2.5h），两者 depends_on 关系正确（T-3b depends_on T-3a）；DAG 更新为 T-1→T-2→T-3a→T-3b→T-4→T-5→T-6 |
| MUST FIX-2 | AC-9 在任务拆解中无 task ID 归宿 | RESOLVED | v2 重定义 AC-9（self_check 含 run_web_tree_nested_ui），由 T-5 的 `covers_ac: [AC-9]` 承接；覆盖表中 AC-9 → T-5 已补全 |

---

## 检查清单结论（plan 模式）

| 项 | 状态 | 说明 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PASS | T-1~T-2 各 ~1h，T-3a ~1.5h，T-3b ~2.5h，T-4/T-5/T-6 各 1-2h |
| depends_on 形成 DAG，没有循环 | PASS | T-1→T-2→T-3a→T-3b→T-4→T-5→T-6 线性链，无环 |
| 评审 / 单测 / CI 阶段对应任务都存在 | PASS | process_tasks 含 P-spec-review / P-code-review / P-test-review / P-push / P-ci / P-deploy / P-user-confirm |
| 没有 "做完整个系统" 类目标性任务 | PASS | 每个任务指向具体文件和操作 |
| AC 覆盖完整（每条 AC 有对应任务） | PARTIAL - 见 MUST FIX-1 | T-5 title 写 "11 AC" 但 spec v2 AC 数为 11；T-2 description 与 AC-11 要求的 .default("") 存在冲突（见 MUST FIX-1） |
| estimated_stage 与十阶段定义对齐 | PARTIAL - 见 MUST FIX-2 | T-5 estimated_stage 仍为 ci_result，但 T-5 是 coding 阶段产物（v1 SHOULD FIX-1 未修） |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | tasks.md T-2 description vs. 覆盖表 AC-11 | **T-2 description 与 AC-11 验证命令存在直接冲突**：T-2 description 写 `path: z.string().optional() 或 路由生成代码格式`（`.optional()` 是字面示例），而 AC-11 验证命令 `grep -qE 'path\s*:\s*z\.string\(\)\.(default\(["\x27]{2}\)|catch\(["\x27]{2}\))'` 要求 `.string()` **直接**接 `.default("")` 或 `.catch("")`——`z.string().optional().default("")` 不匹配此 regex（因为中间有 `.optional()`）。如果 coding agent 按 T-2 描述实现 `.optional()`，AC-11 将在 self_check 时 FAIL。tasks 引导了与 AC 验证不相容的实现路径。 | 将 T-2 description 中的示例改为 `path: z.string().default("")`（不得加 .optional()），与 AC-11 grep regex 保持一致；同时删除"或 路由生成代码格式"的歧义备注（若有不同格式须在 spec 明确而非在 tasks 留悬）。 |
| MUST FIX-2 | tasks.md T-5 estimated_stage: ci_result | **T-5 estimated_stage 标错（v1 SHOULD FIX-1 升级为 MUST FIX）**：T-5 是向 `scripts/_self_check.sh` 写入 11 个 AC block 的代码改动，属于 **coding 阶段**产物；`ci_result` 是阶段 8（CI 跑完看结果），不是写代码的阶段。如果 coding agent 按此 estimated_stage 理解，会把 T-5 推迟到 CI 才做，导致 stage 3 提交时 `_self_check.sh` 缺少新 block，`bash scripts/_self_check.sh current web-tree-nested-ui-20260520` 全部 SKIP（因为没有 run_web_tree_nested_ui 函数），无法在 stage 7/8 守门。v1 SHOULD FIX-1 未修，本轮升级为 MUST FIX。 | 将 T-5 的 `estimated_stage` 改为 `coding`；T-5 的 `depends_on: [T-4]` 保留（需先有测试覆盖才能确认 block 内容正确）。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-2 description | T-2 description 仍保留 `tab 切换时保留 path（或重置到 ""），看交互期望` — "看交互期望"歧义未消除（v1 SHOULD FIX-2 未修）。v2 spec 也未明确此行为（v1 spec SHOULD FIX-4 未修）。coding agent 实现 T-2 时会在两种行为间随机选择。 | 待 spec v3 明确 tab 切换 path 行为后，T-2 description 同步删除"看交互期望"歧义语，改为明确语义（如"tab 切换时重置 path 为 ''"）。 |
| SHOULD FIX-2 | tasks.md T-4 description | T-4 用例命名沿用 `test_default_root_shows_mixed_entries` 下划线风格（v1 SHOULD FIX-3 未修）。现有基线 `repos.files-section.test.tsx` 用 `it("...")` describe/it 字符串风格，新用例风格与基线不一致会产生代码风格割裂。 | 将 T-4 用例名改为 it/describe 字符串风格，如 `it('root shows mixed entries with folder and blob rows', ...)`。 |
| SHOULD FIX-3 | tasks.md T-4 description | T-4 mock 策略写 `mock useSearch + useSubtreeByPath（或直接 fetch fixture）`，两种策略并存（v1 SHOULD FIX-4 未修）。现有基线用 `vi.mock` 整体 mock hook，引入 fetch fixture/MSW 需要额外基础设施。 | 明确使用 `vi.mock('../lib/api/queries', ...)` mock `useSubtreeByPath` 返回受控 fixture；删除"或直接 fetch fixture"歧义项。 |
| SHOULD FIX-4 | tasks.md T-5 title | T-5 title 写 "11 AC"，与 spec v2 AC 表 11 行一致——但 spec 标题仍写 "12 AC"（spec MUST FIX-2）。建议 spec 修正后 T-5 title 数字与 spec 保持一致确认（若 spec 改为 "11 AC" 则 T-5 title 已正确；不是 tasks 自身问题，但需二次确认）。 | spec v3 修正数字后，检查 T-5 title 与 spec 标题数字一致。 |
| SHOULD FIX-5 | tasks.md 覆盖表 | 覆盖表中 AC-11 → T-2，但 T-2 description（修前）提供的实现路径（`.optional()`）会让 AC-11 FAIL。MUST FIX-1 修后，T-2 description 改为 `.default("")` 即可让覆盖表准确。此条 SHOULD FIX 在 MUST FIX-1 修复后自然消解，单独列出以免遗漏。 | MUST FIX-1 修后目视确认覆盖表 AC-11 → T-2 路径的一致性。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md DAG | T-5 depends_on T-4（串行），但 T-5（写 _self_check.sh）与 T-3a/T-3b 互相独立，理论上 T-5 只要 T-4 完成即可，不需要等 T-3b（现有 DAG 已是 T-4 后）。若改 estimated_stage 为 coding，T-3a/T-3b/T-4/T-5 中 T-3a→T-3b→T-4→T-5 已是最优串行，无需额外并行。仅供参考，不影响正确性。 |
| NTH-2 | tasks.md T-3b | T-3b 写 `保证可访问性（role="button" + tabIndex + onKeyDown Enter）`。v1 spec SHOULD FIX-3 提到用 `<button>` 元素替代 `div onClick`；T-3b 仍用 `role="button" + tabIndex` 方案（等效但语义弱于 native `<button>`）。若 spec v3 加入 `<button>` 约束，T-3b 需同步修正。 |
| NTH-3 | tasks.md process_tasks P-user-confirm | P-user-confirm description 无内容（只有 status: pending）。根据 spec AC-9 + AC-10（手测 stage 10），建议在 description 加一行 "手测验证 HF 风树形导航 + 面包屑 + legacy 兼容；确认 AC-9 behavoral UI 表现"，供 stage 10 参考。 |

---

## Verdict

**REVISION REQUIRED**

存在 2 条 MUST FIX：

- **MUST FIX-1**：T-2 description 示例 `.optional()` 与 AC-11 grep regex 要求的 `.default("")` 直接冲突，按 T-2 实现会导致 AC-11 FAIL
- **MUST FIX-2**：T-5 estimated_stage 仍为 `ci_result`（v1 SHOULD FIX-1 未修），应为 `coding`；若保持 ci_result，stage 3 提交时 _self_check.sh 缺 block，守门失效

v1 的 2 条 MUST FIX 均已修复，但 v2 引入了 1 条新 MUST FIX（T-2 与 AC-11 冲突），另 v1 SHOULD FIX-1 升级为 MUST FIX。

---

## 后续指引

Generator 修完 v3 tasks 后，自查：

```bash
# 1. 确认 T-5 estimated_stage = coding
grep -A5 "id: T-5" .harness/changes/web-tree-nested-ui-20260520/request_analysis/tasks.md \
  | grep "estimated_stage:" | grep -q "coding" && echo "T-5 stage PASS" || echo "T-5 stage FAIL"

# 2. 确认 T-2 description 不含 .optional() 示例（应已改为 .default("")）
grep -A20 "id: T-2" .harness/changes/web-tree-nested-ui-20260520/request_analysis/tasks.md \
  | grep -q 'optional()' && echo "T-2 optional WARNING" || echo "T-2 description OK"

# 3. 确认覆盖表所有 AC 均有 task 归宿
awk '/^## 验收覆盖/{p=1;next} p && /^## /{exit} p' \
  .harness/changes/web-tree-nested-ui-20260520/request_analysis/tasks.md \
  | grep "| AC-"
# 目视确认 AC-1 ~ AC-11 全部出现，无空格行

# 4. 确认 DAG 注释与 depends_on 一致
grep "depends_on:" .harness/changes/web-tree-nested-ui-20260520/request_analysis/tasks.md
grep "^T-" .harness/changes/web-tree-nested-ui-20260520/request_analysis/tasks.md
```

v3 修完后重新 spawn reviewer v3 复检，需同时确认 spec v3 的 MUST FIX-1/2/3 已关闭，tasks v3 的 MUST FIX-1/2 已关闭。注意 spec 与 tasks 应在同一版本轮次提交，不要分开评审。
