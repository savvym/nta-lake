---
change_id: harness-reviewer-agent-separation-20260518
target: tasks_v2.md
target_version: 2
review_version: 2
reviewer: claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v2
reviewed_at: 2026-05-18T04:16:49Z
verdict: REVISION REQUIRED
---

# Tasks Review v2

> v2 reviewer 与 v1 reviewer / generator 均不共享上下文，独立子 agent 复检。

## v1 MUST FIX 复检

| v1 MUST FIX | 状态 | 证据 |
|---|---|---|
| #1 T-11 vs spec AC-12 数字打架（+1 vs +13） | **partial closed** | tasks_v2 T-11 写 `期望 PASS = baseline + 1 = 225 + 1 = 226`；spec_v2 AC-12 同步 `PASS: 226$`。两文档**字面数字一致** ✓。但 **baseline=225 来源未给推导**，且仓库没有 baseline 实测产物——若实测 baseline ≠ 225，T-11 必失败。详见 spec_review_v2.md MUST FIX #1（同源问题在 spec 端记主，tasks 端记从）。|
| #2 DAG ↔ depends_on 矛盾 | **closed** | tasks_v2 §"任务依赖（文字 only；删除 ASCII DAG）" 已删 ASCII 图，只留文字。我复检每条 depends_on：T-1, T-3 并行 ✓；T-2 ← T-1 ✓；T-4 ← T-1,2,3 ✓；T-5 ← T-1~T-4 ✓；T-6a/6b ← T-5 ✓；T-7 ← T-1,T-2（不等 T-3~T-6） ✓ 合理；T-8 ← T-1,2,7 ✓；T-9 ← T-1,2,8 ✓；T-10 ← T-1~T-6 ✓；T-11 ← T-5,T-6a,T-6b,T-7~T-9 全收口 ✓；T-12 ← T-11 ✓；T-13 ← T-12 ✓；T-14 ← T-12,13 ✓。**无环** ✓。|

## v1 SHOULD FIX 复检（简表）

| # | v1 issue | v2 状态 | 备注 |
|---|---|---|---|
| 1 | T-7/8/9 stage 与 task 混淆 | closed | tasks_v2 把 T-7/8/9 标 `[process action]`，移到 §process_tasks（与 T-12/13/14 并列）；estimated_stage 字段保留 stage-2/4/6 同时注 "（process action）"。✓ |
| 2 | AC-13 自递归没说怎么自递归 | closed | T-11 描述新增 "跑 `bash scripts/_self_check.sh reviewer-lint` 套娃断言含 'reviewer-lint' 字面（AC-13 自递归）"。✓ |
| 3 | T-6 漏 template 占位符回溯 | closed | tasks_v2 拆 T-6a（20 行 application-owner-agent）+ T-6b（12 行 template 占位符）。✓ 但 T-6b 包含本变更自己的 3 行 — 新问题，详见 MUST FIX #1 下。|
| 4 | T-5 lint 前置 / 后置 | closed | tasks_v2 T-5 明确 "**前置 + fail-fast**：lint FAIL 时立 exit 1（不跑后续 block，省时）"。✓ |
| 5 | T-7~T-9 spawn prompt 与 T-2 模板一致性 | closed | tasks_v2 T-7 描述 "prompt **必须与 T-2 模板一致**；若实操中临时修改，回头补 T-2"。✓ |
| 6 | process_tasks 段补全 | closed but spec_v2 §跨链路 7 还写 "3 条" | tasks_v2 §process_tasks 实际 6 条（T-7/8/9 + T-12/13/14）✓，但 spec_v2 §跨链路 7 仍写 "3 条"——一致性问题反向打回 spec（见 spec_review_v2 SHOULD FIX #1）。|

## v2 自身新检查（plan 模式 tasks 5 条 + 跨链路）

### plan 模式 tasks 5 条

- [x] 1 每个任务粒度合理（1-3 小时）：T-1（写 1 文件）/ T-2（加 1 段）/ T-3（改 3 处）/ T-4（加 1 段）/ T-5（写 1 function 加 case）/ T-6a/6b（机械替换 20+12 行）/ T-10（跑 1 命令）/ T-11（跑 self_check + 检查）—— 都在范围。T-7/8/9 spawn 子 agent 评审本身 ~30-60min OK。
- [ ] 2 depends_on 形成 DAG 无环：✓（已复检，见 v1 MUST FIX #2 复检）；但 T-3 estimated_stage=stage-3 含 "实施前先 `cat ... \| grep -E '^##'` 确认 stage 标题层级" —— 这条 mitigation 应在 stage 2（spec 阶段）就跑掉。详见 SHOULD FIX #1。
- [x] 3 评审 / 单测 / CI 阶段对应任务都存在：T-7（stage 2 review）/ T-8（stage 4 review）/ T-9（stage 6 review）/ T-12（push）/ T-13（deploy）/ T-14（close）✓
- [x] 4 没有"做完整个系统"类目标任务 ✓
- [ ] 5 AC 全覆盖：AC 覆盖矩阵把 AC-3a/3b/3c 合写一行 "T-3"；但 spec_v2 §"v2 调整：AC 个数" 段又说 "13 AC（视为）/ 15 AC（实际）"——矩阵粒度模糊。详见 SHOULD FIX #2。

### 跨链路一致性（与 spec_v2 对齐）

- [ ] **tasks_v2 T-11 vs spec_v2 AC-12 数字**：字面一致（226）但 baseline=225 共同未推导 — 见 spec_review_v2 MUST FIX #1，tasks 同源问题。
- [ ] **tasks_v2 T-6b vs spec_v2 §背景**：spec 写 "5 个早期 change"，tasks T-6b 写 "12 行分布在 5 个早期 change" — 两文档错得一致，实测 = **4 个 change（含本变更自身 3 行）**。详见 MUST FIX #1。
- [ ] **tasks_v2 §process_tasks 6 条 vs spec_v2 §跨链路 7 "3 条"** — tasks 对，spec 错（见 spec_review_v2 SHOULD FIX #1，是 spec 修，tasks 不动）。
- [x] T-7/T-8/T-9 dogfood 顺序 ✓（T-7 不等 T-3~T-6，因 spawn 自评 spec 不需要 lint 完成 —— 合理且与 v1 SHOULD FIX #1 修复一致）
- [x] T-6a/T-6b ← T-5 — lint 在前回溯在后；如果 T-6 先做、T-5 后做，回溯期间 lint 不存在没法防新违规。顺序合理。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks_v2 T-6b + §改动摘要"12 行" + spec_v2 §背景 | **T-6b 命令会把本变更自己的 3 行 template 占位符也改成 self-attest**：实测 `grep -rE "^reviewer:[[:space:]]+<" .harness/changes/ \| grep -v _template` 共 12 行，但其中 **3 行在本 change**（harness-reviewer-agent-separation-20260518/coding/review/code_review_v1.md + .../unit_test/review/test_review_v1.md + .../request_analysis/review/{tasks_review,spec_review}_v1.md 中尚未由 spawn 子 agent 填充的占位符）。这 3 行是 stage 4/6 dogfood 时由子 agent 真填 `claude-agent:` 的位置，**回溯成 self-attest 会冲掉 dogfood 真实记录**，与 §AC-7 "本变更 4 review 文件 reviewer 字段全部以 claude-agent: 开头" 直接矛盾。T-6b 文字"12 行分布在 5 个早期 change"也是错（实测 4 个 change：harness-reviewer-agent-separation 自身 + repo-files-tab + web-mvp-pages + web-write-flows）。| (a) T-6b 命令加 `--exclude-dir=harness-reviewer-agent-separation-20260518`（或 `grep -v` 过滤本 change 路径）；(b) T-6b 描述改 "实测 12 行 - 本变更 3 行 = **9 行**，分布在 3 个 closed change"；(c) spec_v2 §背景同步改 "**4 个 change 含本变更自身 3 行未填**，回溯实际改动 9 行 + 本变更 dogfood 填 3 行"。|
| 2 | tasks_v2 T-11 + §AC 覆盖矩阵 | **T-11 期望 PASS 数 = baseline + 1 但 baseline 未给实测来源**（与 spec_review_v2 MUST FIX #1 同源）。tasks_v2 T-11 直接写 "225 + 1 = 226"，但**仓库内没有 baseline 实测产物**（无 `request_analysis/baseline.md`、summary 也未记录何时跑出 225）。我尝试在本评审中复跑 self_check 实测 baseline，进程 >2min 仍无输出（16+ block 全跑慢），无法快速验证；实测 `grep -cE "^[[:space:]]*run_ac" scripts/_self_check.sh` 共 230+ 调用，PASS 数依赖环境。若实测 baseline ≠ 225，T-11 必失败、AC-12 必 FAIL、整个变更阻塞。 | T-11 拆为 T-11a（stage 1/2 末跑 baseline；产物 `request_analysis/baseline.md`）+ T-11b（stage 3 末跑差值断言：`PASS_new == PASS_baseline + 1`）。AC-12 同步改动态比较（见 spec_review_v2 后续指引 #1）。|

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks_v2 T-3 描述 "实施前先 cat ... \| grep -E '^##' 确认 stage 标题层级" | T-3 estimated_stage=stage-3，但这条 mitigation 应在 **stage 1/2** 跑掉（spec 评审时就该知道 awk pattern 能不能 work）；放 stage-3 等于 reviewer 在 stage 2 评 AC-3a/3b/3c 时只能信任 generator 而不能复检。我替它跑了（结果 PASS），但应该是流程产物。 | T-3 描述删除该句；改在 spec_v2 §"AC dry-parse 证据"段附该 grep 输出（spec_review_v2 SHOULD FIX #3 已建议加该段）。|
| 2 | tasks_v2 §AC 覆盖矩阵 | AC-3a/3b/3c 合写 1 行 "T-3"；spec 是 3 sub-AC。矩阵粒度与 spec 不一致。 | 矩阵拆 3 行：AC-3a / AC-3b / AC-3c → T-3。或矩阵注 "AC-3a/3b/3c 共同覆盖于 T-3 内"。|
| 3 | tasks_v2 T-5 描述 | "在所有 change block 之前跑（`run_reviewer_lint` 排在 case `""` 第 1 行）" —— `case "$FILTER" in` 的 `""` 分支匹配的是"无 filter 跑全仓"，前置 lint 该挂哪个 case 写得含糊；可能开发者把 `run_reviewer_lint` 放进 `*)` 默认分支也行。 | T-5 描述改 "在 `case "$FILTER" in` 的 `""` 与 `*)` 两个分支顶部均调用 `run_reviewer_lint`，确保 `bash scripts/_self_check.sh` 与 `bash scripts/_self_check.sh <block-name>` 都先跑 lint"。|
| 4 | tasks_v2 T-5 实现 | spec_review_v2 SHOULD FIX #4 提到：reviewer-lint 内部 3 个 grep（反向 #1 + 反向 #2 + 白名单），但对外应只 echo 1 行 PASS/FAIL（否则 baseline 不是 +1）。T-5 描述没明示。 | T-5 描述加 "function `run_reviewer_lint` 内部 3 个 grep 检查，但只输出 1 行 `PASS: AC-reviewer-lint ...` 或 `FAIL: AC-reviewer-lint ...`，确保 self_check 计数 +1 不是 +3"。|
| 5 | tasks_v2 T-10 | "本变更不动 Python；跑 self_check AC-11 sdk-cli-mvp block 确认仍 PASS" —— 只看 sdk-cli-mvp 的 AC-11 不代表全仓 AC-11 不回归。若本变更意外动了 Python（如修改 scripts/），其他 block AC-11 可能 FAIL。 | T-10 命令改 "跑全仓 self_check，确认 `grep -c "^FAIL: .*AC-11" output == 0`"。|
| 6 | tasks_v2 T-12（push） + T-13（deploy） | tasks 文字层无问题，但 summary.md §阶段进度 当前仍是 v1 / status pending，spec_v2 承诺更新但 generator 未做（见 spec_review_v2 SHOULD FIX #5）；T-12/T-14 描述应包含 "更新 summary 阶段进度表" 步骤。 | T-12 末加 "更新 summary §阶段进度：1 → v2 / 2 → v1+v2 review 链接"；T-14 末加 "summary §交付 + §复盘 填写"。|

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks_v2 T-1 | "只读模式优先"未删（v1 NICE TO HAVE #1 提到要简化或挪 follow-up）—— v2 改动摘要里没列这条 SHOULD FIX 但 T-1 描述确实有 "只读模式优先（用 Read/Grep/Glob，不 Edit/Write 代码）"。 | T-1 简化为 "reviewer 通常只读，但当前未强制；工具限定见 follow-up `reviewer-tool-restrict-*`"。|
| 2 | tasks_v2 T-2 | spawn 模板的 prompt 长度上限 / 超时上限未提（v1 NICE TO HAVE #2）。 | T-2 加注 "若 spawn 子 agent 评审超时（>30min），优先减少给定上下文或拆 review 范围"。|
| 3 | tasks_v2 T-7~T-9 | "estimated_stage: stage-2/4/6（process action）" —— estimated_stage 字段是 task 落到哪个 stage 的，process action 标在括号里看着像注释；模板字段未必识别。 | 改 estimated_stage 为 stage-2/4/6 单独，process action 标签放任务标题 `[process action]` 前缀（已是这样）；或新增字段 `task_kind: process_action`。|
| 4 | tasks_v2 §AC 覆盖矩阵 AC-7 | AC-7 行写 "T-7, T-8, T-9" 没注时序（stage 2 评只见 T-7）。 | 加注 "（stage 6 末才完整断言）"。|
| 5 | tasks_v2 §改动摘要表头 | "MUST FIX" 列把 SHOULD FIX 项也塞进去（如 "SHOULD FIX #1 T-7/8/9 stage 与 task 混淆"），列名不准。 | 列名改 "v1 issue（含 MUST/SHOULD FIX）" 或把 MUST FIX 和 SHOULD FIX 拆两张子表。|

## Verdict

**REVISION REQUIRED**

理由：2 条 MUST FIX 未关闭：

1. **T-6b 会回溯本变更自己的 3 行 template 占位符**，冲掉 stage 4/6 dogfood 真实记录；§改动摘要"12 行 / 5 个早期 change"实测错（应为 4 个 change 含本变更自身）。
2. **T-11 期望 baseline+1=226 但 baseline 未给实测来源**，若实测 ≠ 225 整个变更阻塞（与 spec_review_v2 MUST FIX #1 同源；tasks 端建议拆 T-11a/T-11b 解耦 baseline 实测与差值断言）。

v1 两条 MUST FIX 都已修：DAG 删除 ✓ / 数字字面一致 ✓（但 baseline 未推导是新发现）。

## 后续指引

Generator 修 tasks_v3 后请自检：

1. **T-6b 排除本 change**：命令加 `grep -v harness-reviewer-agent-separation-20260518`（或 `--exclude-dir=`）；描述改 "实测 9 行（12-3），分布在 3 个 closed change（repo-files-tab / web-mvp-pages / web-write-flows）"。
2. **T-11 拆 a/b**：T-11a stage 1/2 末跑 baseline 写 `request_analysis/baseline.md`；T-11b stage 3 末跑差值断言。
3. **T-5 输出 1 行 PASS** 写进任务描述（防 self_check 计数错乱）。
4. **T-3 cat 验证 stage 标题** 挪到 spec stage 1/2，不放 stage-3 实施。
5. **T-10 改全仓 FAIL 行数 = 0**，不只看 sdk-cli-mvp。
6. **T-12/T-14 加 summary 更新步骤**（spec 承诺 generator 未履行）。
7. AC 覆盖矩阵拆 AC-3a/3b/3c 三行（与 spec 粒度对齐）。
8. 重提 tasks_v3 + spec_v3 后开 `tasks_review_v3.md`（保留 v1/v2 历史）。
