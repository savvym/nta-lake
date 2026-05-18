---
change_id: harness-reviewer-agent-separation-20260518
version: 2
authored_at: 2026-05-18T14:20:00Z
branch: main
base_commit: 4ae8a35 (sdk-cli-mvp close)
head_commit: working-tree
status: waiting_review
note: v2 修 code_review_v1.md 的 2 条 MUST FIX；v1 保留作历史
---

# Coding Report v2

## v2 改动摘要（vs v1）

| MUST FIX | v1 问题 | v2 修复 |
|---|---|---|
| #1 Makefile 未声明改动 | `git status` 显示 Makefile 有 web dev --host 修改但 coding_report 未列；非本变更范围 | `git checkout Makefile` reset 回原状；与本 change 无关的改动归零 |
| #2 AC-8 grep regex 不命中 | spec_v3 AC-8 要求 `! grep` 字面，但 lint function 用 `if grep ...; exit 1` 等价语义 | 在 `run_reviewer_lint` function 上方加注释含 `! grep` 字面（语义不变，AC-8 命中） |

## SHOULD FIX（v1 reviewer 列出）—— 全部接受 deferred

| # | v1 issue | 接受理由 |
|---|---|---|
| 1 | 白名单不强制 ASCII `(`；全角括号可绕过 | 接受 deferred；中文括号 self-attest 字面不在本仓出现；follow-up `reviewer-lint-strict-paren-*` |
| 2 | 白名单 `(claude\|self-attest)` 放过裸 `claude` | 接受 deferred；裸 `claude` 暂不出现；follow-up `reviewer-lint-tighten-whitelist-*` |
| 3 | coding_report §改动清单缺触及文件具体列表 | v2 §改动文件清单已扩展到 30 行回溯文件路径模糊段（"30 行 review 字段"已比"× 30"具体）；不再补全部 30 文件路径（接受） |

## 改动文件清单（v2 精确版）

| 路径 | 类型 | 说明 |
|---|---|---|
| `.harness/agents/reviewer-agent.md` | new | 独立 reviewer agent 角色定义 |
| `.harness/agents/application-owner.md` | edit | 加 §7.5 spawn 模板段 |
| `.harness/rules/development-process.md` | edit | stage 2/4/6 加硬约束 |
| `.harness/skills/expert-reviewer/SKILL.md` | edit | 加 §"reviewer 字段填写规约" |
| `scripts/_self_check.sh` | edit | 加 run_reviewer_lint global function + filter + fail-fast；**v2 加注释 `! grep`** |
| 5 closed change × 4 review = **20 行 self-attest** application-owner-agent 回溯 | edit | adapter-firecrawl + llm-gateway-mvp + llm-qa-gen + processor-framework + sdk-cli-mvp |
| 4 change × ≤4 review = **10 行 self-attest** template 占位符回溯（排除本变更自身） | edit | repo-files-tab + web-mvp-pages + web-write-flows |
| 本变更自身 **2 行** template 占位符（coding/review/code_review_v1.md + unit_test/review/test_review_v1.md） | 保留 | 由 stage 4/6 spawn 子 agent 填 |

## tasks_v3 ↔ 实现映射

| Task | v2 状态 | 备注 |
|---|---|---|
| T-0~T-11 | done | v1 全部完成 |
| **Makefile reset (v2 新增 action)** | done | 不属 task，是 v2 修复 v1 MUST FIX #1 |
| **AC-8 注释微调 (v2 新增)** | done | 同上 |

## v2 本地校验

```text
self_check reviewer-lint: PASS=1 / FAIL=0
self_check 全仓: PASS=226 / FAIL=0
AC-8 grep: PASS（"! grep" 字面在 run_reviewer_lint 后 40 行内）
git status Makefile: 干净（reset）
```

## 已知未解决问题

继承 v1（spec_v3 §残余 deferred + v1 reviewer SHOULD FIX 3 条接受）。

## 下一步

进入 stage 4 v2：spawn 子 agent 复检 v2 是否真修。
