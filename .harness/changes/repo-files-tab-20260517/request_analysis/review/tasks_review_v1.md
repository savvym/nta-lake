---
change_id: <feature-slug>-<yyyymmdd>
target: tasks.md
target_version: 1
review_version: 1
reviewer: <name 或 agent id>
reviewed_at: <YYYY-MM-DDTHH:MM:SSZ>
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 tasks 部分。

- [ ] 每个任务粒度合理（1-3 小时）。
- [ ] depends_on 无环。
- [ ] 包含评审 / 单测 / CI 阶段对应任务（process_tasks 完整）。
- [ ] 没有 "做完整个系统" 类目标任务。
- [ ] 每条 AC 都有非 process_tasks 任务覆盖。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|

## Verdict

APPROVED / REVISION REQUIRED

## 复检指引

作者修完 tasks_v2.md 后：

1. 依赖图 DAG 校验：人工或脚本验证无环。
2. 覆盖矩阵：每条 AC 至少有一个 T-* 关联，没有孤立 AC。
3. process_tasks 完整：spec-review / code-review / test-review / ci / deploy（如适用）/ user-confirm 都在。
