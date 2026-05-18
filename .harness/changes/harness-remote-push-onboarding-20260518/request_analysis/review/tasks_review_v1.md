---
change_id: harness-remote-push-onboarding-20260518
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:harness-remote-push-onboarding-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T23:55:00Z
verdict: REVISION REQUIRED
must_fix_count: 0
should_fix_count: 1
nice_to_have_count: 1
---

# Tasks Review v1

> 同 spec_review_v1.md，本 reviewer 是独立 sub-agent（claude-sonnet-4-6），未参与 tasks 撰写。

---

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 tasks.md）

- [x] 每个任务粒度合理（T-1~T-7 各约 5-15 min；T-8 约 10 min 含 self_check 等待；全部 < 45 min total）
- [x] depends_on 形成 DAG 无环（T-1..T-7 depends_on: []，T-8 depends_on: [T-1..T-7]；无环，终点 T-8）
- [x] 评审 / 单测 / CI / 部署 process_tasks 存在（stage-2/4/6/7/8/9/10；`grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md` = 6）
- [x] 无"实现整个系统"类目标性任务（每个 T-* 单一职责，范围明确）

---

## DAG 验证（实跑）

```text
T-1 (AC-1)  ──┐
T-2 (AC-2)  ──┤
T-3 (AC-3)  ──┤
T-4 (AC-4)  ──┼──→ T-8 (AC-8, behavioral, self_check 全跑)
T-5 (AC-5)  ──┤
T-6 (AC-6)  ──┤
T-7 (AC-7)  ──┘
```

无环。T-8 正确等待所有实现任务完成。

---

## 验收覆盖矩阵核验

| AC | kind | 关联任务 | 覆盖 |
|---|---|---|---|
| AC-1 | static | T-1 | PASS |
| AC-2 | static | T-2 | PASS |
| AC-3 | static | T-3 | PASS |
| AC-4 | static | T-4 | PASS |
| AC-5 | static | T-5 | PASS |
| AC-6 | static | T-6 | PASS |
| AC-7 | static | T-7 | PASS |
| AC-8 | behavioral | T-8 | PASS |

每条 AC 至少 1 个非 process_tasks 任务覆盖，behavioral AC-8 由 T-8 实现覆盖。

---

## process_tasks 完整性

| P-task | stage | status | 合规 |
|---|---|---|---|
| P-spec-review | stage-2 | pending | PASS |
| P-code-review | stage-4 | self-attest | PASS（micro change；spawn cost > value；类比 harness-reviewer-model-sonnet 模式） |
| P-test-review | stage-6 | skipped | PASS（纯文档/配置，无代码，无单测；spec 明示） |
| P-push | stage-7 | pending | PASS |
| P-ci | stage-8 | self-attest | PASS（本项目策略明示不引入 GitHub Actions） |
| P-deploy | stage-9 | pending | PASS（T-8 = stage 9 验证） |
| P-user-confirm | stage-10 | pending | PASS |

stage-4/6/8 self-attest/skipped 均有 notes 说明理由，符合 development-process §跨阶段约束 §4（"可以让某些阶段产物极简"）。

---

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-3 description（§产出物 加一项）| T-3 建议在 development-process.md stage 7 §产出物加入 "`git push origin main（无 remote 项目时跳过；本仓库 origin = git@github.com:savvym/nta-lake.git）`"——其中 "无 remote 项目时跳过" 与本 change 核心目标（清算 "无 remote" 措辞）语义矛盾；"本仓库 origin = ..." 是实例信息，不适合写入通用规则文档（development-process 是通用流程规则，不应绑定具体仓库地址）。 | 改为 "`git push origin main`（本项目为单作者直 push main；PR 流程作为 future change）"。去掉 "无 remote 项目时跳过" 及仓库地址。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | tasks.md T-8 description 中 self_check 命令 | T-8 description 中运行命令与 spec AC-8 一致（含 `tail -3`）。若 spec MUST FIX-1 修复后 AC-8 验证命令改为 `grep -qE "^FAIL: 0$"`，建议同步更新 T-8 description 中的示例命令，保持一致性。 | T-8 description 中 `tail -3 | grep -q "FAIL: 0"` 改为 `grep -qE "^FAIL: 0$"`。 |

---

## Verdict

**REVISION REQUIRED**

理由：tasks.md 自身无 MUST FIX，但 spec_review_v1 有 1 条 MUST FIX（AC-8 验证命令 `tail -3 | grep -q "FAIL: 0"` 假阴性），该 MUST FIX 也波及 T-8 description 中的示例命令（NICE-1）。spec 修完 v2 后，tasks.md 也应同步更新 T-3 description（SHOULD FIX-1）和 T-8 description（NICE-1）。tasks_review 与 spec_review 一并在 spec v2 / tasks v2 提交后做 v2 复检。

---

## 后续指引（generator 修 tasks_v2 前自查）

```bash
cd /data/home/zhhdzhang/nta/nta-lake/.claude/worktrees/harness-remote-push

TASKS=.harness/changes/harness-remote-push-onboarding-20260518/request_analysis/tasks.md

# SHOULD FIX-1：确认 T-3 description 不含"无 remote 项目时跳过"
grep -n "无 remote 项目时跳过" "$TASKS"  # 期望 0 行

# NICE-1：确认 T-8 description 已同步 spec AC-8 修复
grep -n "tail -3" "$TASKS"  # 期望 0 行（修复后）
grep -n "grep -qE.*FAIL: 0" "$TASKS"  # 期望 1 行（修复后）

# process_tasks 完整性验证
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" "$TASKS"  # 期望 ≥ 6

# DAG 终点验证：T-8 depends_on 含所有实现任务
grep -A 3 "id: T-8" "$TASKS"  # 期望 depends_on: [T-1, T-2, T-3, T-4, T-5, T-6, T-7]
```
