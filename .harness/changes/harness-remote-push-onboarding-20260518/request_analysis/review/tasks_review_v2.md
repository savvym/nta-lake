---
change_id: harness-remote-push-onboarding-20260518
target: tasks.md
target_version: 2
review_version: 2
prior_review: request_analysis/review/tasks_review_v1.md
reviewer: claude-agent:harness-remote-push-onboarding-20260518-stage2-reviewer-v2
reviewed_at: 2026-05-19T00:30:00Z
verdict: APPROVED
must_fix_count: 0
should_fix_count: 0
nice_to_have_count: 1
---

# Tasks Review v2

> 评审者声明：本 reviewer 是独立 sub-agent（claude-sonnet-4-6），未参与本 change tasks 撰写。本次是复检导向评审，仅核 v1 SHOULD FIX 闭环 + 检 v2 新引入 bug。本次模型：**sonnet**（claude-sonnet-4-6），符合 reviewer-agent.md §8 默认规约。

---

## v1 SHOULD FIX 复检

| # | v1 问题 | v2 状态 | 证据 |
|---|---|---|---|
| SHOULD FIX-1 | T-3 description 含 "无 remote 项目时跳过" + `git@github.com:savvym/nta-lake.git` | **CLOSED** | `grep -nE "savvym\|无 remote 项目时跳过" tasks_v2.md` 实跑 = **0 行**；T-3 description 改为 `§产出物 加 "git push origin main"` 通用形式，并附注 "rules 是项目通用文档，不写具体 remote URL" |
| NICE-1（v1）| T-8 description 中 self_check 命令与 spec AC-8 一致（含 `tail -3`），建议同步修复 | **部分闭环** | T-8 description 去掉了 `tail -3`（`grep -n "tail -3" tasks_v2.md` = 0 行），但 T-8 description 仍保留 `期望：tail 含 "FAIL: 0"` 措辞（见详情） |

---

## v2 新 bug 检查

### T-8 description 残留 "tail" 措辞（NICE TO HAVE）

tasks_v2 T-8 description（L126-130）：

```yaml
description: |
  DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat \
    DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 \
    bash scripts/_self_check.sh
  期望：tail 含 "FAIL: 0"，全链路 PASS。
  AC-8 验证；通过即可 close。
```

T-8 description 中的验证命令（`bash scripts/_self_check.sh`）未含 `tee /tmp/...log; grep -qE "^FAIL: 0\$"` 管道，且 `期望：tail 含 "FAIL: 0"` 仍引用 "tail" 概念，与 spec_v2 AC-8 修复后的验证命令（`tee + grep -qE`）未完全对齐。

影响评估：

- T-8 是任务描述（execution hint），不是验收标准本身
- spec AC-8 才是权威验证命令（已正确修复）
- 执行时参考 spec AC-8，T-8 description 误导性有限
- 不会导致验收失败（coding agent 通常以 spec AC 为准）

结论：**NICE TO HAVE**（不升级为 MUST FIX / SHOULD FIX）。与 v1 NICE-1 的"建议同步"为同一问题，v2 仍未彻底修完，但不阻塞。

---

## v1 MUST FIX 复检

v1 tasks_review 无 MUST FIX，此节 N/A。

---

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 tasks.md）

- [x] 每个任务粒度合理（T-1~T-7 各约 5-15 min；T-8 约 15-30 min；全部 < 60 min total）
- [x] depends_on 形成 DAG 无环（T-1..T-7 depends_on: []，T-8 depends_on: [T-1..T-7]；无环，终点 T-8）
- [x] 评审 / 单测 / CI / 部署 process_tasks 存在（stage-2/4/6/7/8/9/10；6 required stages 覆盖）
- [x] 无"实现整个系统"类目标性任务（每个 T-* 单一职责）

---

## DAG 验证（v2 未变）

```text
T-1 (AC-1)  ──┐
T-2 (AC-2)  ──┤
T-3 (AC-3)  ──┤
T-4 (AC-4)  ──┼──→ T-8 (AC-8, behavioral, self_check 全跑)
T-5 (AC-5)  ──┤
T-6 (AC-6)  ──┤
T-7 (AC-7)  ──┘
```

无环，终点 T-8。

---

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | tasks_v2.md T-8 description L130 | `期望：tail 含 "FAIL: 0"` 仍含 "tail" 概念；T-8 execution hint 命令仅为 `bash scripts/_self_check.sh` 未含 `tee + grep -qE` 验证步骤，与 spec_v2 AC-8 修复后命令不完全对齐 | 将 `期望：tail 含 "FAIL: 0"` 改为 `期望：FAIL: 0（用 tee /tmp/dataplat-selfcheck-all.log 捕获后 grep -qE "^FAIL: 0\$" 验证，参见 spec AC-8）`；或直接在 description 里给出完整验证命令 |

---

## Verdict

**APPROVED**

理由：

1. **SHOULD FIX-1 真闭环**：`grep -nE "savvym|无 remote 项目时跳过" tasks_v2.md` = 0 行，T-3 description 已清除矛盾措辞和实例 URL。
2. **DAG / process_tasks / AC 覆盖矩阵**未回退，与 v1 一致。
3. **v2 无新引入 MUST/SHOULD 级 bug**：唯一发现为 NICE TO HAVE 级 T-8 description "tail" 措辞残留，不阻塞 coding 进入。
4. tasks_v2 整体质量满足进入 stage 3（coding）要求。

---

## 后续指引

```bash
cd /data/home/zhhdzhang/nta/nta-lake/.claude/worktrees/harness-remote-push

TASKS=.harness/changes/harness-remote-push-onboarding-20260518/request_analysis/tasks.md

# SHOULD FIX-1 闭环确认
grep -nE "savvym|无 remote 项目时跳过" "$TASKS"
# 期望：0 行

# process_tasks 完整性
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" "$TASKS"
# 期望：≥ 6

# DAG 终点验证
grep -A 3 "id: T-8" "$TASKS"
# 期望：depends_on: [T-1, T-2, T-3, T-4, T-5, T-6, T-7]
```

coding agent 执行 T-8 时，以 **spec AC-8** 的完整验证命令为准（含 `tee + grep -qE "^FAIL: 0\$"`），不以 T-8 description 简化版为准。

---

## 本次用模型

**sonnet**（claude-sonnet-4-6）。符合 reviewer-agent.md §8 默认规约。
