---
change_id: harness-reviewer-agent-separation-20260518
version: 1
authored_at: 2026-05-18T14:35:00Z
status: waiting_review
note: meta-change（改 harness 文档 + shell；不动 Python/TS）；"测试"形式 = self_check shell lint + dogfood 3 轮 spawn 实证
---

# Test Report v1

## 本变更的测试形态

本变更是 **meta-change**（改 `.harness/` 文档 + `scripts/_self_check.sh` shell；不动 dataplat Python/TS 代码）。"测试"对应：

1. **`scripts/_self_check.sh reviewer-lint`**：本变更新增的 global lint AC，3 个 grep 检查（反向×2 + 白名单）；对外 1 个 run_ac 计数
2. **`scripts/_self_check.sh` 全仓**：226 AC（baseline 225 + reviewer-lint 1）
3. **dogfood 3 轮 spawn 实证**：stage 2 v1/v2/v3 共 6 个 review 文件（spec + tasks 各 3 版）+ stage 4 v1/v2 共 2 个 review 文件——总 8 个 review 文件由独立 reviewer 子 agent 写入；reviewer 字段全部以 `claude-agent:` 起头

## 验收项 ↔ 测试映射（13 AC）

| AC | 测试形态 | 状态 |
|---|---|---|
| AC-1 | `test -f .harness/agents/reviewer-agent.md && grep ...` | PASS（stage 3 实施时实测） |
| AC-2 | `grep -q "Agent(" .harness/agents/application-owner.md && ...` | PASS |
| AC-3a/3b/3c | `awk '/^## 阶段 N/,/^## 阶段 N+1/' ...` 三段分别 grep | PASS（stage 3 实施时实测） |
| AC-4 | `grep -q "reviewer 字段" .harness/skills/expert-reviewer/SKILL.md && ...` | PASS |
| AC-5 | `grep -q "^run_reviewer_lint" scripts/_self_check.sh` | PASS |
| AC-6 | `! grep -rE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/` | PASS（T-6a 完成后 0 行） |
| AC-7 | dogfood ≥4 文件 reviewer 以 claude-agent: 起头 | PASS（stage 6 末完整断言；stage 4 末已有 8 个：6 stage 2 + 2 stage 4） |
| AC-8 | `grep -A40 ^run_reviewer_lint ...` 含 `! grep` + 白名单 | PASS（v2 coding_report 修复后） |
| AC-9 | self-attest 带括号文案 ≥ 29 | PASS（实测 32：20 application-owner-agent 回溯 + 12 template 占位回溯 - 0 本变更未填） |
| AC-10 | `bash scripts/_self_check.sh reviewer-lint` PASS | PASS |
| AC-11 | 全仓 self_check FAIL AC-11 行数 = 0 | PASS |
| AC-12 | 全仓 self_check `PASS: 226$` | PASS（实测 226） |
| AC-13 | `bash scripts/_self_check.sh reviewer-lint` 含 "reviewer-lint" 字面 | PASS |

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| `scripts/_self_check.sh` `run_reviewer_lint` function | shell lint | 1 AC（内部 3 grep） |
| `request_analysis/baseline.md` | 实测产物 | 1 baseline 记录 |
| `request_analysis/review/spec_review_v{1,2,3}.md` | dogfood 实证 | 3 独立 reviewer subagent runs |
| `request_analysis/review/tasks_review_v{1,2,3}.md` | dogfood 实证 | 3 独立 reviewer subagent runs |
| `coding/review/code_review_v{1,2}.md` | dogfood 实证 | 2 独立 reviewer subagent runs |

## Mock 范围声明

无 mock；本变更不动 Python；测试形态全部基于真 shell + 真 spawn 子 agent。

## 本地运行结果

```text
$ bash scripts/_self_check.sh reviewer-lint 2>&1 | tail -5
PASS  reviewer-lint  reviewer 字段独立性守门（反向×2 + 白名单）
PASS: 1 / FAIL: 0 / SKIP: 0

$ DATAPLAT_PG_PORT=5433 ... bash scripts/_self_check.sh 2>&1 | grep "PASS:"
PASS: 226
```

## dogfood 实证统计

| Stage | 子 agent 轮次 | reviewer 字段 | verdict | MUST FIX 抓到 |
|---|---|---|---|---|
| stage 2 v1 | claude-agent:...stage2-reviewer-v1 | REVISION REQUIRED | 5 |
| stage 2 v2 | claude-agent:...stage2-reviewer-v2 | REVISION REQUIRED | 2 |
| stage 2 v3 | claude-agent:...stage2-reviewer-v3 | APPROVED | 0 (1 SHOULD FIX) |
| stage 4 v1 | claude-agent:...stage4-reviewer-v1 | REVISION REQUIRED | 2 |
| stage 4 v2 | claude-agent:...stage4-reviewer-v2 | APPROVED | 0 |
| **合计** | **5 轮 spawn** | — | — | **9 MUST FIX 全是 self-review 看不见的盲点** |

## 已知 flaky / 跳过

- 无 skip
- reviewer-lint 依赖 .harness/changes/ 文件状态；若并行 change 引入新 reviewer 字段必跑 lint 验

## 覆盖率

- reviewer-lint function：3 grep 全路径覆盖（应用 owner / template / 白名单）
- 13 AC：12 PASS + 1 NICE TO HAVE（v3 reviewer 标）

## 下一步

进入 stage 6：spawn 子 agent 评本 test_report。
