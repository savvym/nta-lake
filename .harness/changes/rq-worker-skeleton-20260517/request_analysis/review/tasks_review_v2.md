---
change_id: rq-worker-skeleton-20260517
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-stage2-reviewer-v2
reviewed_at: 2026-05-17T14:25:00Z
verdict: APPROVED
---

# Tasks Review v2

## 复核背景

tasks v1 已在 v1 review 给 APPROVED（MUST FIX 数 = 0），4 条 SHOULD FIX 为优化项。本轮 spec v2 修订聚焦 AC-4 验证命令 syntax 修复 + SKILL 第 8 条反哺，**未触及 tasks.md 内容**（spec v2 frontmatter `revisions` 段未提任何 tasks 字段变更）。

## 副作用扫描

reviewer 关注：spec v2 的 AC-4 验证命令修订是否引入 tasks 侧需要联动调整的项。

| 维度 | spec v2 修订 | tasks.md 影响 |
|---|---|---|
| AC-4 命令措辞 | `for m in [...]: assert ...` → `assert all(... for m in [...])` | tasks.md T-4 列 JobsService 5 方法签名 + AC-4 引用关系不变 — **无影响** |
| SKILL 第 8 条反哺 | request-analysis SKILL 新增 dry-parse 自审 | tasks.md 本身不需要为 SKILL 反哺新加任务（反哺直接落在 SKILL.md，stage-2 reviewer 即时验证）— **无影响** |
| 其他 AC 命令 | 未改动 | tasks 覆盖矩阵不变 — **无影响** |

## 重新机械化复跑（与 v1 review 同基线）

```text
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md → 6（PASS）
AC ↔ Task 覆盖矩阵 13/13（PASS，逐条与 v1 review L37-L52 一致）
依赖 DAG 无环（PASS，与 v1 review L18-L23 一致）
```

tasks.md 内容相比 v1 无修改 → 上述结论自动继承。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks v1 review SHOULD FIX-1~-4 | tasks v2 未改动（spec v2 frontmatter 未声明 tasks 联动），故 v1 review SHOULD FIX 全部仍开放：T-5 禁止 import 全局 engine 措辞 / T-8 Redis db 隔离 fixture / T-10 depends_on 收窄 / T-11 depends_on 收窄 | 不阻塞 stage-3；作者可在 stage-3 实施期或下次 tasks 修订时一并消化。提示：T-11 depends_on 写"T-1~T-10 v1 完"与本轮 stage-2 复核现实矛盾（reviewer 当下未等代码就在评审），建议尽早收窄 |

### NICE TO HAVE

无新增。

## Verdict

**APPROVED**（MUST FIX 数 = 0；与 v1 一致）

tasks v2 无副作用 — spec v2 修订未触发任何 tasks 联动需求。SHOULD FIX 全部继承 v1，仍为优化项，不阻塞通过。可进入 stage 3。
