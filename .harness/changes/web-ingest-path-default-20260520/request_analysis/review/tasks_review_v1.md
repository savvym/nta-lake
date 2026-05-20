---
change_id: web-ingest-path-default-20260520
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:web-ingest-path-default-20260520-stage2-reviewer-v1
reviewed_at: 2026-05-20T11:30:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论（plan 模式）

| 条目 | 状态 | 备注 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PASS | T-1～T-4 均属小粒度 |
| depends_on 形成 DAG，没有循环 | PASS | T-1→T-2→T-3→T-4 线性，无环 |
| 评审 / 单测 / CI 阶段对应任务都存在 | PARTIAL | P-spec-review / P-code-review / P-test-review 等 process_tasks 齐全；但 T-2 承担了测试编写职责却未调整为 `estimated_stage: unit_test`（见 SHOULD FIX） |
| 没有 "做完整个系统" 类目标性任务 | PASS | |
| 每个 AC 至少被 1 个 task cover | PARTIAL | AC-4（typecheck）只在 T-4 覆盖，但 T-4 `estimated_stage: ci_result`，而 AC-4 是 pnpm typecheck 属于本地 coding 期验证——stage 对应不准（见 SHOULD FIX） |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST-1 | tasks.md T-2（description + covers_ac） | T-2 的 description 说"扫测试断言含 content/ 字面，按需调整"，预计 "≤ 5 处"，但未在 spec 阶段 grep 出实际清单。实测：`apps/web/src/routes/*.test.tsx` 中与 IngestSection 默认 path **直接相关**的 content/ 断言为 **0 处**（现有 content/ 均来自 Files Section / Commits 显示 fixture，与本 change 无关）。T-2 的"≤ 5 处预计"无根据，且 description 未区分"需改断言"与"不应动的 display fixture"，容易导致 coder 误删合法 fixture（如 `repos.files-section.test.tsx:118-127` 的 legacy flat commit entry names）。此外，spec_review MUST-1 指出需**新增** IngestSection onFiles 单测——但 T-2 description 中完全没有"新增测试"这一动作，导致实现缺口。 | 重写 T-2 description：(1) 明确 grep 结果 = 0 处需改（附命令证据）；(2) 明确不动 repos.files-section.test.tsx 和 commits test 中的 display fixture；(3) 新增子步骤"为 IngestSection.onFiles 默认 path 新增 vitest 单测：模拟 FileList，断言 path === f.name"（与 spec MUST-1 对齐）。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD-1 | tasks.md T-2 `estimated_stage` | T-2 的 `estimated_stage: unit_test`，但任务同时包含 "scan test assertions + adjust"（属于 coding 期工作）和 "新增测试"（属于 unit_test 期）。当前混在一起，会导致在 coding 阶段跳过 T-2，到 unit_test 才做，中间 T-3 的依赖链受影响。如果 T-2 的扫描+调整在 coding 期做完，测试新增在 unit_test 期补，建议拆为两个任务。 | 将"扫 + 调整"步骤放 `estimated_stage: coding`；"新增 onFiles 单测"放 `estimated_stage: unit_test`（可拆为 T-2a / T-2b，或在 T-2 description 中明确两阶段执行顺序）。 |
| SHOULD-2 | tasks.md T-4 `estimated_stage` | T-4 `estimated_stage: ci_result`，但 T-4 的工作是"本地 typecheck / test / self_check 全绿"——这是 CI 之前的本地验证，属于 `coding` 或 `pre-push` 期。ci_result 阶段通常指 CI pipeline 产物，与本地 pnpm 命令混淆。 | 将 T-4 `estimated_stage` 改为 `coding`（本地验证）或单独标注为 `pre_push`（push 前验证），与 P-ci（CI pipeline）区分开。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md T-2 description | "≤ 5 处预计" 是估算，但未附 grep 命令证据。即使最终是 0 处，也应在 description 中写出 pre-flight grep 命令，方便 coder 直接运行确认。 | 在 description 加一行：`# pre-flight: grep -rE '"content/' apps/web/src/routes/*.test.tsx` 并注明 "期望输出：仅含 display fixture（files-section / commits），不应含 ingest path 断言"。 |
| NTH-2 | tasks.md 验收覆盖表 | AC-6 在覆盖表中由 T-3 覆盖，但如 spec_review MUST-3 所指，AC-6 与 AC-5 验证命令相同。若 AC-6 在 spec 修正后获得独立语义，覆盖表也需同步更新。 | 待 spec v2 修正 AC-6 后，更新验收覆盖表确认 AC-6 对应的 task。 |

---

## Verdict

**REVISION REQUIRED**

1 条 MUST FIX（与 spec_review MUST-1 强相关）：
- **MUST-1**：T-2 description 中"预计 ≤ 5 处"无根据（实测 = 0），且缺少"新增 IngestSection 单测"动作，导致 behavioral AC-3 无实现路径。

2 条 SHOULD FIX（stage 标注错误，影响阶段对应准确性）。

待 spec_review MUST-1/MUST-3 关闭后，tasks.md 对应条目也需同步更新。

---

## 复检指引（Generator 修完后自查）

1. **MUST-1**：确认 T-2 description 包含：
   - `grep -rE '"content/' apps/web/src/routes/*.test.tsx` 的预期结果说明（仅 display fixture，ingest 相关 = 0）
   - "新增 onFiles 单测" 子步骤，断言 `path === f.name`
2. **SHOULD-1**：确认 T-2（或拆分后的 T-2a/T-2b）`estimated_stage` 正确对应 coding / unit_test 两期。
3. **SHOULD-2**：确认 T-4 `estimated_stage` 不再是 `ci_result`。
4. 运行以下命令确认 DAG 无环（手工核查）：
   ```bash
   grep "depends_on" .harness/changes/web-ingest-path-default-20260520/request_analysis/tasks.md
   ```
