---
change_id: platform-north-star-pivot-20260520
review_of: request_analysis/tasks.md
reviewer: claude-stage2-reviewer
version: 1
authored_at: 2026-05-20T16:30:00Z
verdict: APPROVED
---

# Tasks Review v1

## 机械化检查清单

| # | 检查项 | 结果 | 说明 |
|---|---|---|---|
| M-1 | frontmatter 合法（change_id / version / authored_at） | PASS | 三字段完整 |
| M-2 | DAG 无环验证 | PASS | 拓扑排序：T-1 → {T-2,T-3,T-4} → {T-5,T-6,T-7,T-8} → {T-9,T-10} → T-11 → T-12，无环 |
| M-3 | DAG 图与 depends_on 字段一致 | PASS（含说明） | 见问题 #1：图的 ASCII 有一处视觉歧义，但不影响实际 depends_on 正确性 |
| M-4 | AC 全覆盖（每条 AC 被至少一个 T 的 covers_ac 引用） | PASS | AC-1~AC-10 均至少出现一次于 covers_ac 字段；T-12 作为总验证任务 covers 全部 10 条 |
| M-5 | 每个 T 粒度合理（30-90 分钟） | PASS（含说明） | 见问题 #2：T-1/T-2 粒度差异较大，但均在合理范围内 |
| M-6 | 单测阶段任务存在 | PASS | T-12 `estimated_stage: unit_test`，且明确跑 `self_check` + pnpm/pytest 无回归验证 |
| M-7 | 无"做完整个系统"类目标任务 | PASS | 每个 T 都有具体交付物（某节 design.md / 某个文件 / lint 脚本） |
| M-8 | T-6 / T-7 的 covers_ac: [] 合理性 | PASS（含说明） | 见问题 #3：可接受，但建议补 AC |
| M-9 | T-10 depends_on 完整性 | PASS | 依赖 [T-1,T-2,T-3,T-4,T-5]，覆盖 lint 脚本验证的所有 design.md 章节前置任务 |
| M-10 | Stage 估时合理性 | PASS（含说明） | 见问题 #4：Stage 8 CI 估时 ~5 分钟偏乐观 |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 理由 | 建议 |
|---|---|---|---|---|
| 1 | tasks.md §DAG 摘要，第 158-164 行 | ASCII DAG 图有一处视觉歧义：`T-4 ──┬── T-8 ──┼── T-9` 后跟 `│ └────────────────────┤` 这条横线容易被误读为 T-4 直接连 T-9（即 T-9 depends_on 包含 T-4）。实际 T-9 deps=[T-1, T-8]，T-4 只通过 T-8 间接到达 T-9。 | 图/数据不一致风险（虽然 depends_on 字段正确，图的歧义可能误导实现者跳过 T-8 直接写 T-9） | 把图中该条线改为 `T-4 ──── T-8 ──── T-9`（去掉 T-4 的直连分支），或加注释说明 |
| 2 | tasks.md T-11，第 134-141 行 | T-11 描述"10 条 AC 全部转 bash run_ac 调用"，与 spec.md §范围 D-11 里的"6 条 AC"矛盾（D-11 是笔误，实际应为 10）。本文件数字是正确的，但会导致阅读 spec 再看 tasks 的人困惑。 | 跨文件一致性 | 此条待 spec SHOULD FIX #3 修复后自然消除，tasks 本身无需改动 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 3 | tasks.md T-6（第 76-83 行）/ T-7（第 85-95 行） | T-6 `covers_ac: []`（§与业界的关系）、T-7 `covers_ac: []`（deprecated 标记）。D-7 在 spec §范围是明确的交付项，没有 AC 覆盖意味着实现者"做完就算完"，无法机械化验证。 | 若 spec 加了 AC-11（§与业界的关系 存在 + 含 4 个参考项目名），则 T-6 更新 `covers_ac: [AC-11]`。T-7 若加 AC（验证 deprecated 节 + 版本指针），则同步更新。此条依赖 spec 先补 AC。 |
| 4 | tasks.md §Stage 估时，第 178 行 | Stage 8（CI = self_check full）估时 `~5 分钟` 偏乐观。当前 `_self_check.sh full` 包含 330+ 条 run_ac 调用，含 pytest、uv build 等耗时命令；加上 platform-north-star-pivot 的 10 条 AC 和 AC-9 的 bash 脚本，实测通常 10-15 分钟。 | 改为 `~10-15 分钟` 以避免用户提前中止等待 |

## 评审重点结论

### F. T-1 ~ T-12 DAG
DAG 真实无环，depends_on 字段与描述一致。有一处 ASCII 图视觉歧义（见 SHOULD FIX #1），不影响实际执行正确性。

拓扑顺序合理：T-1（基础节）→ 多分支并行（T-2/T-3/T-4）→ 依赖产物任务（T-5/T-6/T-8）→ 汇总型任务（T-9 规则文件、T-10 lint 脚本）→ T-11（self_check 集成）→ T-12（全量验证）。

### G. covers_ac 覆盖
全部 10 条 AC 均有 T 覆盖（含 T-12 作为总验收）。T-6 和 T-7 无独立 AC 覆盖属于可接受的边界情况（总结性/过渡性章节，非核心验收路径），但建议 spec 补 AC-11 后同步更新。

### H. Stage 估时
Stage 3（3-4 小时）和 Stage 2/4/6（20-30 分钟）估时对纯 doc change 合理。Stage 8 偏乐观（见 NICE TO HAVE #4），不阻塞评审。

### I. T-12 自检设计
T-12 = `bash scripts/_self_check.sh platform-north-star-pivot → 10 PASS` 作为 stage 5 单测，对**纯文档/治理 change** 来说是合适的验证粒度。理由：
1. 所有 AC 都是结构性静态检查（grep/awk）或单一 bash 脚本（AC-9），没有业务路径需要集成测试覆盖。
2. 本 change 不动任何业务代码，pnpm/pytest 无回归验证只需确认无意外改动。
3. `_self_check.sh` 的 AC 命令若因 spec MUST FIX #1 修复而正确运行，则 T-12 能真实捕获 design.md 结构缺失。

若 spec 的 awk 命令不修复，T-12 的 10 条 AC 中有 5 条（AC-1/2/3/4/5）在 design.md 改好之后仍会 FAIL，导致 stage 5 无法通过。这是 spec 问题的连带影响，不是 tasks 本身的设计问题。

## Verdict

**APPROVED**

tasks.md 的 DAG 结构正确、无环、AC 全覆盖、粒度合理，作为独立文档质量合格。

但注意：tasks 的可执行性依赖 **spec 的 MUST FIX 修复**（awk 命令缺陷），在 spec 通过评审之前，T-12 无法真实通过。建议先把 spec 打回修复，spec_v2 通过 review 后 tasks_v1 直接进入 stage 3 coding，无需重新评审 tasks。

## 后续指引

1. spec_review_v1.md 已打回 REVISION REQUIRED（MUST FIX 2 条）。
2. 作者修完 spec 并通过 spec_review_v2.md（verdict: APPROVED）后：
   - tasks 本身无需重新提交评审（tasks_v1 已 APPROVED）。
   - 若 spec 新增了 AC-11（§与业界的关系），则在 coding 阶段同步更新 T-6 的 `covers_ac`。
3. 进入 stage 3 coding 时，建议实现顺序：T-1 → T-3/T-4 并行 → T-2 → T-5/T-7/T-8 并行 → T-9/T-10 → T-6 → T-11 → T-12。
