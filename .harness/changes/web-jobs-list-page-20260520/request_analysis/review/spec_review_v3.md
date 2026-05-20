---
change_id: web-jobs-list-page-20260520
target: spec.md
target_version: 3
review_version: 3
reviewer: claude-agent:web-jobs-list-page-20260520-stage2-reviewer-v3
reviewed_at: 2026-05-20T15:00:00Z
verdict: APPROVED
---

# Spec Review v3

## v2 MUST FIX 复检

| # | v2 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | AC-8 表描述仍写"≥ 4"，AC-8 完整命令末尾仍 `-ge 4`；与 T-4 已升为 ≥5 不一致，守门形同虚设 | **RESOLVED** | spec v3 AC-8 表描述改为"≥ 5 + 全 PASS（admin / user 403 / status 过滤 / limit+offset 分页 / 400 非白名单 status）"；AC-8 完整命令末尾已改为 `-ge 5`（spec v3 第 86 行 + 第 109 行）|

## v2 SHOULD FIX 复检

| # | v2 issue | 状态 | 证据 |
|---|---|---|---|
| SHOULD FIX-1 | §跨链路自审第 6 条仍写"含 @router.get 锚定 path `"/"`"，与已选择 `""` 矛盾 | **RESOLVED** | spec v3 §跨链路自审第 6 条已改为"✅ AC-3 grep 精确（含 @router.get 锚定 path ""——v2 起统一为空串）"（spec v3 第 131 行） |

## 检查清单结论

| 条目 | 状态 | 说明 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | 现状/痛点/用户选定三段清晰 |
| 问题陈述与目标可被外部读者理解 | PASS | 5 个问题点逐条列出 |
| 范围 / 非范围都有 | PASS | 非范围已补 JobORM 新列约束 |
| 验收标准每条都可演示且可机械化 | PASS | AC-8 描述和命令已升为 ≥5，与 T-4 对齐 |
| 风险有缓解措施或显式 accept | PASS | 风险表 7 行均有缓解 |
| 没有把已有架构当新提案重复 | PASS | 未重复 design.md |
| AC 表存在 `kind` 列 | PASS | 含 kind 列 |
| 至少 1 行 AC kind=behavioral | PASS | AC-7 / AC-8 均为 behavioral |
| ac_kind_lint 非 exempt | PASS | frontmatter 无 exempt |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md AC-8 完整命令（v2 NTH-1 遗留） | AC-8 完整命令虽已升为 `-ge 5`，但命令中 `grep -cE 'test_jobs_list\.py::'` 若 0 命中时 shell exit code 为 1，整条命令会提前失败，count 未被传给 `[ ... -ge 5 ]`；NTH-1 建议的 `\|\| true` 修法仍未落地。当前 `-ge 5` 下 0 命中直接 exit 1，表面像"test 数不足"但实为 grep 退出码误导。 | 在该 `grep -cE ... ` 后加 `\|\| true`，使 0 命中时数字 0 传入 `[` 判断，保持错误语义清晰 |
| NTH-2 | spec.md AC-5 描述（v2 NTH-2 遗留） | started_at 或 completed_at 为 null 时"用时"无法计算；null guard 未在 spec 说明。 | AC-5 中补"当 started_at 或 completed_at 为 null 时用时列显示 —" |

## Verdict

**APPROVED**

v2 报告的 1 条 MUST FIX（AC-8 描述/命令 ≥4 与 T-4 下限 ≥5 不一致）已在 spec v3 正确修复：表描述改为"≥ 5"并补全第 5 个用例描述，命令末尾从 `-ge 4` 改为 `-ge 5`。v2 SHOULD FIX（自审第 6 条 path `"/"`）亦已修正为 `""`。无新增 MUST FIX。

## 后续指引

APPROVED → 进入 stage 3（tasks 编写）或继续 tasks_review_v3（如 tasks.md 同步需修订）。

两条 NTH 可在 coding 阶段由开发者顺手修，不阻塞推进。若 NTH-1 问题在 CI 中出现误报，应优先修复。
