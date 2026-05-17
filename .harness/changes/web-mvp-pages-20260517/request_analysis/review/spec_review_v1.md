---
change_id: <feature-slug>-<yyyymmdd>
target: spec.md
target_version: 1
review_version: 1
reviewer: <name 或 agent id>
reviewed_at: <YYYY-MM-DDTHH:MM:SSZ>
verdict: REVISION REQUIRED        # APPROVED | REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1。

- [ ] 背景写明了为什么现在做。
- [ ] 问题陈述对外部读者可理解。
- [ ] 范围 / 非范围都有。
- [ ] 每条验收标准可演示且可机械化。
- [ ] 风险有缓解或显式 accept。
- [ ] 没有把已有架构当新提案。
- [ ] 待澄清问题已清零或显式 deferred。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §验收标准 AC-2 | "性能更好" 无可机械化判据 | 改为具体阈值，如 "P95 延迟 < 200ms"，并加测试 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| | | | |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| | | | |

## Verdict

REVISION REQUIRED（MUST FIX 数 > 0）

## 复检指引

作者修完 spec_v2.md 后：

1. 自检：`grep -E "性能更好|更清晰|体验提升" spec_v2.md` 结果为空。
2. 自检：每条 AC 都能填进下面表格的"验证方式"列。
3. 自检：待澄清问题段为空或全部已 deferred 并加注理由。

提交 v2 后开 `spec_review_v2.md`。
