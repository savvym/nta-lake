---
change_id: harness-bootstrap-20260516
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:stage2-reviewer
reviewed_at: 2026-05-16T19:26:14Z
verdict: APPROVED
---

# Tasks Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1（plan 模式 tasks.md）。

- [x] 每个任务粒度合理：T-1 ~ T-13 对应单一 markdown 文件或一组相关文件，对应实文件 26 ~ 187 行，落在 1-3 小时内可完成。
- [x] depends_on 形成 DAG，无循环：仅 T-8 → T-7、T-10 → T-9 两条；其余 `depends_on: []`。
- [x] 评审 / 单测 / CI 阶段对应任务都存在：process_tasks 含 P-spec-review / P-code-review / P-test-write / P-test-review / P-push / P-ci / P-deploy / P-user-confirm 共 8 条。
- [x] 没有"做完整个系统"类目标任务。
- [x] 验收覆盖矩阵：12 条 AC 每条至少 1 个 T-* 关联，无孤立 AC。
- [x] process_tasks 中 P-ci / P-deploy 的 `status: skipped` 均带 `reason` 字段且理由充分（不引入 CI / 无部署面）。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|

（无）

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-3（行 38-45）+ §验收覆盖矩阵（行 207） | T-3 产出 `.harness/README.md`（harness 自身导航），但其 `covers_ac: [AC-2]` 不准确——AC-2 在 spec 中只针对 `application-owner.md`。`.harness/README.md` 没有任何 AC 显式约束，但 AC-11 "文件非空" 间接覆盖了它。建议要么在 spec 加一条 AC（如 "AC-2b：`.harness/README.md` 存在并描述分层加载策略"），要么把 T-3 的 covers_ac 改为 `[AC-11]` 或新增的 AC 编号。 | 倾向第二种：把 T-3 的 `covers_ac` 改成 `[AC-11]` 并在覆盖矩阵相应行加入 T-3。无需改 spec。 |
| 2 | tasks.md P-push（行 173-175） | `status: pending` 后用 `#` 行内注释写"需要先 git init"，与 P-ci / P-deploy 用结构化 `reason:` 字段不一致。stage 7 进入时机不清。 | 把 P-push 注释改为正式字段：增加 `blocked_by: 仓库尚未 git init` 或在 `status` 行下追加 `reason: ...`，保持与 P-ci/P-deploy 的写法对称。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md 全部 T-*（行 15-149） | `estimated_stage` 全部填 `coding`，对追溯式记录是合理的，但未来非追溯式变更可考虑细分到 `request_analysis` / `coding` 等更精确的阶段。 | 当前不阻塞；记入 follow-up。 |

## Verdict

APPROVED（MUST FIX 数 = 0）

## 复检指引

若 Generator 选择补 tasks_v2.md：

1. 自检 T-3 与覆盖矩阵一致性：
   `grep -nE "T-3|AC-11" request_analysis/tasks.md` 应能看到 T-3 出现在 AC-11 一行的关联任务中。
2. 自检 P-push reason 字段：
   `grep -A2 "P-push" request_analysis/tasks.md` 应看到 `reason:` 或 `blocked_by:` 一行。
3. DAG 校验：
   `grep -E "depends_on:" request_analysis/tasks.md` 人工确认仍只有 T-8→T-7、T-10→T-9，没有引入循环。
4. 若不补 v2，在 `summary.md` §Deferred 项追加上述 SHOULD FIX 的 deferred 理由与跟进位置。

提交修订后开 `tasks_review_v2.md`；若选择 deferred，本 review 即为最终版。
