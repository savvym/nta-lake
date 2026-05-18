---
change_id: harness-reviewer-agent-separation-20260518
version: 3
authored_at: 2026-05-18T13:35:00Z
note: v3 同步 spec_v3.md MUST FIX 修复；v1/v2 保留作历史
---

# Tasks v3

## v3 改动摘要（vs v2）

| 改动 | 说明 |
|---|---|
| T-5 加硬约束 | `run_reviewer_lint` 内部即便多 grep，对外只 1 个 run_ac 调用 |
| T-6b 加排除本变更 | `--exclude-dir=harness-reviewer-agent-separation-20260518` |
| T-6b 实测行数 | 20 + (12-2 本变更未填) = 30 行；AC-9 `-ge 29` margin 1 |
| T-11 引用 baseline.md | 实测产物 → 期望 226 = 225+1 |
| 新 T-0 | "stage 2 末更新 summary §阶段进度 v1→v2→v3 + frontmatter last_updated" |

## T-0 [stage-2 末] 更新 summary §阶段进度 + frontmatter

- summary.md §阶段进度表：阶段 1 行加 "v1/v2/v3"；阶段 2 行加 review_v1+v2 链接（v3 由 stage 2 v3 reviewer 决定是否再评）
- frontmatter `last_updated: 2026-05-18T13:40:00Z`
- depends_on: spec_v3, tasks_v3, baseline.md 已写
- estimated_stage: stage-2 末
- covers_ac: 无 AC 直接覆盖（summary 维护是 SKILL #9 第 6 次实践）

## T-1 `.harness/agents/reviewer-agent.md` 新建

- 不变 (见 v2)
- depends_on: 无 / estimated_stage: stage-3 / covers_ac: AC-1

## T-2 `.harness/agents/application-owner.md` 加 spawn 模板段

- 不变 (见 v2)
- depends_on: T-1 / estimated_stage: stage-3 / covers_ac: AC-2

## T-3 `.harness/rules/development-process.md` stage 2/4/6 加硬约束

- 不变 (见 v2)
- depends_on: 无 / estimated_stage: stage-3 / covers_ac: AC-3a, AC-3b, AC-3c

## T-4 expert-reviewer SKILL 加 reviewer 字段规约

- 不变 (见 v2)
- depends_on: T-1, T-2, T-3 / estimated_stage: stage-3 / covers_ac: AC-4

## T-5 self_check global reviewer lint（**对外 1 个 run_ac**）

- 在 `scripts/_self_check.sh` 加 `run_reviewer_lint` function
- 实现：function 内部跑 3 个 grep（反向×2 + 白名单），**对外只调 1 次 `run_ac`**（说"reviewer-lint" + 总 PASS/FAIL）
- **硬约束（v3 新加）**：function 内部不允许多 run_ac 调用；保 self_check 计数 +1 而不是 +3
- 位置：所有 block 之前（case `""` 第 1 行）；FAIL 立 exit 1
- 加 filter `reviewer-lint` 入口
- depends_on: T-1~T-4 / estimated_stage: stage-3 / covers_ac: AC-5, AC-8, AC-10

## T-6a 历史回溯：20 行 application-owner-agent → self-attest

- 不变 (见 v2)
- depends_on: T-5 / estimated_stage: stage-3 / covers_ac: AC-6, AC-9

## T-6b 历史回溯：template 占位符 → self-attest（**排除本变更**）

- 命令：`grep -rlE "^reviewer:[[:space:]]+<" .harness/changes/ --exclude-dir=_template --exclude-dir=harness-reviewer-agent-separation-20260518`
- 实测排除本变更后剩 **10 行**（4 changes：repo-files-tab 4 + web-mvp-pages 4 + web-write-flows 2 - 2 不在本变更名下 = 10）
- 每行改为 `reviewer: self-attest (template 占位符未填；早期 change 部分 review 文件未填字段；详见 harness-reviewer-agent-separation-20260518 §背景)`
- 本变更自身的 2 行不动（stage 4/6 spawn 子 agent 时会填）
- depends_on: T-5 / estimated_stage: stage-3 / covers_ac: AC-6, AC-9

## T-7 [process action] stage 2 spawn 子 agent 评 spec + tasks（dogfood）

- 已在 stage 2 跑了 3 轮（v1 → v2 → v3）；reviewer 字段：
  - v1: `claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v1`
  - v2: `claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v2`
  - v3: `claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v3` (如果决定再评 spec_v3)
- depends_on: T-1, T-2 / estimated_stage: stage-2 / covers_ac: AC-7 partial

## T-8 [process action] stage 4 spawn 子 agent 评 coding（dogfood）

- 不变 (见 v2)
- depends_on: T-1, T-2, T-7 / estimated_stage: stage-4 / covers_ac: AC-7 partial

## T-9 [process action] stage 6 spawn 子 agent 评 test（dogfood）

- 不变 (见 v2)
- depends_on: T-1, T-2, T-8 / estimated_stage: stage-6 / covers_ac: AC-7 full

## T-10 lint + type 不回归

- 用全仓 self_check 输出 grep FAIL AC-11 行数 = 0
- depends_on: T-1~T-6 / estimated_stage: stage-3 / covers_ac: AC-11

## T-11 注册 + 跑全仓 self_check（226 = baseline+1）

- baseline = 225（实测产物 `request_analysis/baseline.md`）
- 本变更加 1 个 global reviewer-lint AC → 期望 `PASS: 226`
- 跑 `bash scripts/_self_check.sh reviewer-lint` 套娃断言含 "reviewer-lint" 字面（AC-13）
- depends_on: T-5, T-6a, T-6b, T-7~T-9 / estimated_stage: stage-3 / covers_ac: AC-12, AC-13

## §process_tasks（**6 条**——同步 spec v3 §跨链路 7）

- T-7：[process action] stage 2 dogfood spawn 评
- T-8：[process action] stage 4 dogfood spawn 评
- T-9：[process action] stage 6 dogfood spawn 评
- T-12：stage-7 commit + push
- T-13：stage-9 deploy verify（无部署面 → skipped）
- T-14：stage-10 close

## 任务依赖（文字 only；无 ASCII DAG）

- T-0 不依赖（stage 2 末手动跑）
- T-1, T-3 并行（独立）
- T-2 ← T-1
- T-4 ← T-1, T-2, T-3
- T-5 ← T-1~T-4
- T-6a, T-6b 并行 ← T-5
- T-7 ← T-1, T-2（不等 T-3/T-4/T-5/T-6）
- T-8 ← T-1, T-2, T-7
- T-9 ← T-1, T-2, T-8
- T-10 ← T-1~T-6
- T-11 ← T-5, T-6a, T-6b, T-7, T-8, T-9
- T-12 ← T-11
- T-13 ← T-12
- T-14 ← T-12, T-13

无环 ✓。

## AC 覆盖矩阵

| AC | task |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3a/3b/3c | T-3 |
| AC-4 | T-4 |
| AC-5 | T-5 |
| AC-6 | T-6a, T-6b |
| AC-7 | T-7, T-8, T-9 |
| AC-8 | T-5 |
| AC-9 | T-6a, T-6b |
| AC-10 | T-11 |
| AC-11 | T-10 |
| AC-12 | T-11 |
| AC-13 | T-11 |
