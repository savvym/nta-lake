---
change_id: web-ingest-path-default-20260520
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-agent:web-ingest-path-default-20260520-stage2-reviewer-v2
reviewed_at: 2026-05-20T12:00:00Z
verdict: APPROVED
---

# Tasks Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST-1 | T-2 description 缺"新增 IngestSection 单测"动作；"≤ 5 处预计"无根据；未区分 display fixture 与 ingest 断言 | RESOLVED | v2 将 T-2 拆为 T-2a（新增 `repos.ingest-section.test.tsx`，mock 策略 + 断言逻辑均有描述，covers_ac:[AC-3a]）+ T-2b（确认 6 处 display fixture 保留不动，附 grep 命令，covers_ac:[AC-3b]）；"≤ 5 处"估算已删除 |

## 检查清单结论（plan 模式）

| 条目 | 状态 | 备注 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PASS | T-1 单行改动 < 30 min；T-2a 新建测试文件约 1-2h；T-2b grep 确认 < 15 min；T-3 self_check 改动约 1h；T-4 本地验证约 30 min |
| depends_on 形成 DAG，没有循环 | PASS | T-1 → T-2a + T-2b（并行）→ T-3 → T-4；无环 |
| 评审 / 单测 / CI 阶段对应任务都存在 | PASS | P-spec-review / P-code-review / P-test-review / P-push / P-ci / P-deploy / P-user-confirm 7 个 process_tasks 齐全 |
| 没有 "做完整个系统" 类目标性任务 | PASS | 所有 task 均为具体操作 |
| 每个 AC 至少被 1 个 task cover | PASS | AC-1→T-1；AC-3a→T-2a+T-4；AC-3b→T-2b+T-4；AC-4→T-4；AC-5→T-3 |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD-1 | tasks.md T-4 `estimated_stage: ci_result` | v1 SHOULD-2 未修：T-4 执行的是 `pnpm --filter web typecheck` + `pnpm --filter web test -- --run` + `bash scripts/_self_check.sh current`，全部是 push **之前**的本地验证；`ci_result` 阶段通常指 CI pipeline 产物（P-ci），两者混淆会导致 coder 误以为 T-4 在 push 之后才做，推迟了本地红线验收。 | 将 T-4 `estimated_stage` 改为 `coding`（或 `pre_push`），与 P-ci 区分。 |
| SHOULD-2 | tasks.md T-2b `covers_ac: [AC-3b]` | T-2b 本身只做"grep 确认 6 处 display fixture 仍在"，并不执行 vitest；AC-3b（vitest run 全 PASS）实际由 T-4 运行验证。T-2b 是 AC-3b 的前置条件（不误删 fixture），而非直接覆盖者，语义上偏宽。 | 将 T-2b covers_ac 改为空（表示前提条件任务）或加注"prerequisite for AC-3b"；AC-3b 覆盖留给 T-4。如流程规约要求每 AC 至少一个 task 直接 cover，可保留但加注释说明语义。 |
| SHOULD-3 | tasks.md T-2b description（grep 计数脆弱性） | T-2b 用 `grep -rE 'content/' apps/web/src/routes/*.test.tsx` 断言结果恰好为 6 行。但 T-2a 创建的 `repos.ingest-section.test.tsx` 可能包含字符串 `'content/'`（例如在注释 "should NOT produce 'content/a.pdf'" 或负向断言 `expect(path).not.toBe('content/a.pdf')` 中）。若如此，T-2b 的 grep 数将超过 6，误报失败。 | 将 T-2b 的 grep 命令加文件范围排除：`grep -rE 'content/' apps/web/src/routes/*.test.tsx --exclude='repos.ingest-section.test.tsx'`，仅统计原有文件；或在 description 说明"如新建文件含 content/ 字样，基准数需相应调整"。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md 验收覆盖表 | 验收覆盖表未列 T-2a 与 T-2b 的 explicit 行，只有 T-4 列在 AC-3a/AC-3b 行。建议补全：`AC-3a | T-2a, T-4`；`AC-3b | T-2b（前提）, T-4（执行）`，让覆盖表与正文 covers_ac 字段一致。 | 更新验收覆盖表，与 tasks YAML covers_ac 对齐。 |

## Verdict

**APPROVED**

v1 唯一 MUST FIX（T-2 缺新单测动作）RESOLVED：T-2a 明确新建单测文件并给出 mock 策略与断言方向，T-2b 显式确认 display fixture 保留逻辑。DAG 正确，AC 覆盖完整。3 条 SHOULD FIX（T-4 stage 标注延续 v1 未修、T-2b covers_ac 语义偏宽、T-2b grep 计数对新文件不鲁棒）不阻塞实现，但建议 coder 在 coding 阶段顺手修复，特别是 SHOULD-3（T-2b grep 脆弱性可能在 unit_test 阶段引发假阳性）。

## 后续指引

APPROVED → generator 可进入 stage 3 编码实现（T-1）。
- 强烈建议 coding 阶段同步修复 T-4 `estimated_stage` 至 `coding`（SHOULD-1）
- 建议 T-2a 创建测试文件时注意不在文件中出现裸 `content/` 字符串（SHOULD-3），或在 T-2b 的 grep 命令中排除新文件
- 若 SHOULD 项不修，需在 `summary.md` deferred 条目注明

## 复检指引（Generator 修完后自查）

若 generator 主动修复 SHOULD-3，可运行：
```bash
grep -rE 'content/' apps/web/src/routes/*.test.tsx --exclude='repos.ingest-section.test.tsx'
# 预期：仍为 6 行（repos.files-section.test.tsx 4 行 + commits.*.test.tsx 2 行）
```
若新文件含 `content/` 字样，用上述排除命令或调整基准数说明。
