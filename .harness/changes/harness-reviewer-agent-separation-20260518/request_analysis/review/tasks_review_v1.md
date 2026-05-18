---
change_id: harness-reviewer-agent-separation-20260518
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v1
reviewed_at: 2026-05-18T12:50:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 tasks）

- [x] 每个任务粒度合理（1-3 小时）—— T-1~T-11 单任务都在范围；T-7/T-8/T-9 dogfood 是评审 + 子 agent 用时，总约 1-2h/任务。
- [ ] **depends_on 形成 DAG，没有循环** —— DAG 文本与文字 depends_on 不一致；T-2 文字依赖 `T-1`，DAG 图却显示 T-1+T-3 都流到 T-2（隐含 T-3 ↔ T-2 顺序未声明）；详见 MUST FIX #2。
- [x] 评审 / 单测 / CI 阶段对应任务都存在 —— T-7/T-8/T-9 是 stage 2/4/6 评审；T-11 是 self_check；T-12 commit + push；T-13 deploy；T-14 close。
- [x] 没有"做完整个系统"类目标任务 —— 每条 T-N 都聚焦 1 件事。
- [ ] **AC 全覆盖** —— AC 覆盖矩阵列了 AC-1~13 → T-1~T-11，但 AC-13 在矩阵里写了 T-11 覆盖，spec AC-13 命令空（见 spec_review_v1 SHOULD FIX #3）；详见 SHOULD FIX #2。

## 跨链路一致性（与 spec 对齐）

- [ ] **tasks.md ↔ spec.md AC-12 数字打架**：tasks T-11 写 "期望全仓 PASS: 225（原 16 block）+ lint 计入新 1 个 → 226+；具体数等实测"；spec AC-12 写 `PASS: 238` —— 同一数字 spec 说 238、tasks 说 226+。详见 MUST FIX #1。
- [ ] **T-11 自己说"不为本变更建一个 13 AC block"**：但 spec AC-12 算法用了 `+ 本块 13`——两个文档对"是否新建 13 AC block"决策不一致。详见 MUST FIX #1。
- [x] T-7/T-8/T-9 dogfood 顺序合理：T-7 在 T-1+T-2 完成后才能 spawn（spawn 需 reviewer-agent.md 定义 + owner 模板），T-8 依赖 T-7，T-9 依赖 T-8。
- [x] T-6 历史回溯依赖 T-5 self_check lint 先就位 —— 顺序合理（先有守门，再回溯 + lint 实测两边都过）。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-11 + spec.md AC-12 | **两文档对"是否建 13 AC block"决策不一致**：tasks T-11 写 "暂时**不**为本变更建一个 13 AC block；本变更的 AC 在 spec 阶段通过 global lint + 阶段产物覆盖；但 reviewer-lint 是新 block；加入总入口；期望全仓 PASS: 225（原 16 block）+ lint 计入新 1 个 → 226+；具体数等实测"。spec AC-12 写 `+ 本块 13 = 238`。一个说 +1，一个说 +13，必须二选一。 | 选 +1（推荐）：T-11 写 "新加 1 个 global AC：reviewer-lint，挂在所有 block 之前；预期 PASS = baseline + 1"；spec AC-12 同步改为 `+ 1 = baseline_plus_1`，且 baseline 数字以实测为准（当前 211 因 env FAIL，理想 225）。或选 +13（不推荐，spec 已写 out-of-scope 不建 block，得改 out-of-scope）。 |
| 2 | tasks.md §任务依赖图 | **DAG 与文字 depends_on 矛盾**：(a) 文字 T-2 `depends_on: T-1`，DAG 图却写 `T-1 ─┐  T-3 ─┤  ↓  T-2`——隐含 T-2 也依赖 T-3，但 T-2 文字未声明；(b) DAG 中 T-10 文字 `depends_on: T-1~T-6`，DAG 显示 T-10 在 T-6 下游 OK，但 DAG 把 T-7~T-9 与 T-5/T-6 串成两条平行链最终汇到 T-11 —— T-7 文字 `depends_on: T-1, T-2`，但 DAG 显示 T-7 排在 T-5 之后（与文字不一致，T-7 可能在 T-5 前就能跑）。 | 修正 DAG 图与文字 depends_on 一一对应；或干脆删掉 ASCII DAG 留文字 depends_on（最不易错）。建议正确顺序：T-1, T-3 并行（独立）；T-2 在 T-1 后；T-4 在 T-1+T-2+T-3 后；T-7 在 T-1+T-2 后（不必等 T-4/T-5）；T-5 在 T-4 后；T-6 在 T-5 后；T-8 在 T-7 之后但与 T-5/T-6 并行；T-9 在 T-8 之后；T-10/T-11 收尾。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-7 + 整体 stage 分配 | T-7 `estimated_stage: stage-2`、T-8 `stage-4`、T-9 `stage-6`，但 T-7 是 **stage 2 的评审动作**本身（spawn 子 agent 评）—— "task" 与 "stage" 边界混淆。常规 tasks 描述 stage 3 实现做什么；spawn-子 agent 评审是 stage 2/4/6 的"流程动作"非"实现任务"。 | 把 T-7/T-8/T-9 移到 `## process_tasks` 段（与 T-12/T-13/T-14 并列），明确这是流程动作而非可"完成"的 implementation task；或在 task 描述加注 "executed as process action in stage N"。 |
| 2 | tasks.md §AC 覆盖矩阵 AC-13 | AC-13 在矩阵里写 T-11 覆盖，但 spec AC-13 命令空（"AC-13：self_check 自递归"无 bash）。tasks T-11 文字也只写 "AC: AC-10, AC-12, AC-13"，没说怎么自递归。 | 让 T-11 显式跑一次 `bash scripts/_self_check.sh reviewer-lint` 作为自递归证据，写进 T-11 任务描述。 |
| 3 | tasks.md T-6 | "扫描全仓所有 review 文件，把 reviewer: application-owner-agent 改为 reviewer: self-attest (...)" —— 但 spec §范围还说改"模板占位符 `<name 或 agent id>`"也改为 self-attest。T-6 同样要处理这 14 行（非 _template 内），任务描述没明示。 | T-6 拆为 T-6a (改 application-owner-agent → self-attest，~20 行) + T-6b (改 `<name 或 agent id>` 占位 → self-attest，~14 行非 template)，或在 T-6 描述加注两类各自的命令与计数。 |
| 4 | tasks.md T-5 | "全跑入口排在所有 block 之前（或最后），不与 block 重复" —— "前 / 后" 二选一未定。lint 是否 fail-fast（前置）还是收尾跑（后置）影响开发者体验。 | 推荐"前置 + 块跑完后再总计"——lint 失败时直接 exit 1 阻止后续 block 跑（省时），符合 "守门"语义。明确写到 T-5 描述。 |
| 5 | tasks.md T-7~T-9 | dogfood spawn 模板用什么 prompt 必须在 T-7 任务描述里给出（或引用 T-2 写的模板）；否则 stage 3 实现 T-2 时与 stage 2 dogfood T-7 实操之间的 prompt 一致性无法保证。 | T-7 描述加 "spawn 时使用的 prompt 必须与 T-2 模板一致；若实操中临时修改，回头补 T-2 模板"。 |
| 6 | tasks.md §process_tasks | spec §跨链路 第 7 条说 "process_tasks 6 条：T-9~T-14 占位"，但 tasks.md process_tasks 段只 3 条（T-12/T-13/T-14）。T-7/T-8/T-9 不在 process_tasks 段。spec 自审与 tasks 实际不一致（spec_review_v1 SHOULD FIX #2 也指出）。 | tasks.md process_tasks 段补全（如加入 T-7/T-8/T-9）或修 spec §跨链路 第 7 条的"6 条"说法。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-1 | "**只读模式优先**（用 Read/Grep/Glob，不 Edit/Write 代码）" —— spec §Out of scope 已说 reviewer 工具限定 → follow-up；T-1 里再写"只读优先"会让本变更范围模糊。 | T-1 表述简化为"reviewer 通常只读，但当前未强制；工具限定见 follow-up `reviewer-tool-restrict-*`"。 |
| 2 | tasks.md T-2 | spawn 模板里要不要写 prompt 长度上限 / 超时上限 —— 当前未提。general-purpose subagent 的 spawn 默认上限是多少未说。 | T-2 加注 "若 spawn 子 agent 评审超时（如 >30min），优先减少给定上下文或拆 review 范围"。 |
| 3 | tasks.md T-10 | "本变更不动 Python；跑 ruff + mypy 仅确认全仓无回归" —— 实测当前 baseline mypy/ruff 已有失败（self_check FAIL: 14）。T-10 "无回归" 标准要看 baseline diff。 | T-10 加注 "对比 main 分支 ruff/mypy 报告，本变更只允许新增 0 个错误（已有错误不修也不让本变更负责）"。 |
| 4 | tasks.md §AC 覆盖矩阵 | 矩阵清晰但缺 AC-7 多任务列对应 —— AC-7 在 T-7+T-8+T-9 都列了，但 stage 2 评 AC-7 时只能见 T-7 产物。 | 在矩阵 AC-7 行加 "(完整验证需 T-9 完成后)"。 |

## Verdict

**REVISION REQUIRED**

理由：2 条 MUST FIX 未关闭。其中 MUST FIX #1（tasks T-11 vs spec AC-12 数字打架）是 spec 自相矛盾的另一面，必须与 spec_v2 一起改齐；MUST FIX #2（DAG 与 depends_on 不一致）会让 stage 3 实现时排序混乱、影响子 agent dogfood spawn 时机。

## 后续指引

Generator 修 tasks_v2 后请自检：

1. AC-12 数字一致性：grep tasks_v2 找 "PASS:" 与 spec_v2 找 "PASS:" 数字完全一致（推荐方案：+1 个 reviewer-lint AC，不建 13 AC block）。
2. DAG 一致性：人工再画 DAG，验证文字 `depends_on` 与图箭头一一对应；或保留文字版删除 ASCII 图。
3. process_tasks 段补全或修 spec §跨链路第 7 条措辞，使两文档"6 条 / 3 条"一致。
4. T-6 拆/合后明确两类回溯（application-owner-agent 与 `<name 或 agent id>` 占位符）各自的命令与计数。
5. 重提 tasks_v2 + spec_v2 后开 `tasks_review_v2.md`（不要覆盖 v1）。
