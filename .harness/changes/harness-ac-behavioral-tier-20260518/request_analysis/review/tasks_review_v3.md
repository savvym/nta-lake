---
change_id: harness-ac-behavioral-tier-20260518
target: tasks.md
target_version: 3
review_version: 3
reviewer: claude-agent:harness-ac-behavioral-tier-20260518-stage2-reviewer-v3
reviewed_at: 2026-05-18T09:55:00Z
verdict: APPROVED
---

# Tasks Review v3

## v2 MUST FIX 复检（reviewer 实跑 tasks_review_v2.md §复检指引 命令）

| # | v2 issue | 状态 | 证据（reviewer 本机实跑）|
|---|---|---|---|
| MUST #1 | T-4 description (ii) `grep -q behavioral` 裸 grep 不锚定 AC 行；T-6 fixture-bad 缺"全 static + 描述含 behavioral"反例 | **CLOSED** | **(a) T-4 已锚定**：tasks.md L136 `(ii) grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|' <段>`，与 spec.md L81 完全一致（reviewer `diff <(grep "ii\) grep" spec.md) <(grep "ii\) grep" tasks.md)` 双方语义同型）。<br>**(b) T-4 description L137-L138** 加注释："**必须锚定 AC 行的 kind 单元格** —— 不接受裸 grep -q behavioral（会被 AC 描述里"behavioral 三层"等字串误命中，机械化保护失效）"。<br>**(c) T-6 三种 fixture-bad 齐全**：tasks.md L169-L186 列出：<br>&nbsp;&nbsp;- `/tmp/fixture-ok`（合规）<br>&nbsp;&nbsp;- `/tmp/fixture-bad-no-kind`（缺 kind 列）<br>&nbsp;&nbsp;- `/tmp/fixture-bad-static-but-mention-behavioral`（**v3 新增最隐蔽反例**：AC 表有 kind 列 + 所有 AC kind=static + AC 描述里在多个位置塞 "behavioral" 字串 + 期望 lint FAIL）<br>**(d) subshell 跑 3 次**：tasks.md L179-L185 三次 `(export AC_KIND_LINT_SCAN_DIR=...; run_ac_kind_lint)` 期望退码 0 / != 0 / != 0；trap cleanup 删除 `/tmp/fixture-*` 全部目录。<br>**(e) reviewer 本机用同型反例 dry-run v3 regex**（参见 spec_review_v3.md MUST #2 (e)）：裸 grep 命中 4、v3 regex 命中 0，证明 fixture-bad-static-but-mention-behavioral 真能区分。 |

**v2 1 个 MUST FIX 复检结论**：真闭环。

## v2 SHOULD FIX 复检

| # | v2 issue | 状态 | 评语 |
|---|---|---|---|
| SHOULD #1 | T-2/T-4/T-5 `depends_on: [T-1a]` 单点 fan-out 过宽 | **NOT CLOSED but acceptable** | reviewer 本机 `grep -cE "depends_on: \[T-1a\]" tasks.md` = 5（T-1b/T-1c/T-2/T-4/T-5）。v3 未解耦。但本 change 是单人/单 session 执行的纯 harness change（无多人并行），并行度损失估值仅 2-3h，对实际交付影响极小；且 T-1a 完成是 SKILL 编辑共识的 anchor，强行解耦反而可能引入"实施者在 SKILL 写好前编 self_check.sh"导致两边不一致。SHOULD 不阻塞 verdict（按 SKILL §3 唯一判据 = MUST FIX 数），但建议 generator 在 stage 3 进入时**显式选择**：是接受 T-1a 串行 OR 在 T-1a 完成后立刻并行 T-2/T-4/T-5。本 review 视为 generator 默认接受串行路径，**deferred 理由**："v3 闭环表未列 SHOULD，按 'closed via 默认接受' 处理；T-1a 1.5h，串行影响可控"。 |
| SHOULD #2 | T-8 缺 rollback #4（fixture-bad-static-but-mention-behavioral 假 PASS 检测） | **NOT CLOSED but acceptable** | reviewer 本机 `grep -nE "fixture-bad.*PASS\|描述含 behavioral.*PASS\|回 T-4.*双条件" tasks.md` = 0 命中。v3 未显式加 rollback #4。但 T-6 fixture 内部已对此反例硬断言（"期望退码 != 0"），若 lint 实现错误（裸 grep 未改 regex）则 fixture 直接 FAIL → T-7 调用 fixture 也 FAIL → T-8 全仓 self_check 退码 != 0。即"fixture 内部硬断言"已隐式覆盖该 rollback 路径。SHOULD 不阻塞，建议 T-8 实施时在 description 里补一句"若 fixture-bad-static-but-mention-behavioral 跑出 PASS（与 T-6 期望反向）→ 回 T-4 修双条件 (ii)"，使错误回溯路径在文档里显式。 |
| SHOULD #3 | T-1b description 缺"19 ID 必须显式写进 SKILL.md（不是引用 spec）" | **NOT CLOSED but acceptable** | reviewer 本机 `grep -nE "显式写进 SKILL\|不是引用 spec\|self_check 读取源" tasks.md` = 0 命中。v3 未显式加。但 T-1b description L57-L62 列了 19 ID 全名（永久 2 + 暂豁免 17）+ AC-7 验证里 for loop 直接 `grep "$cid" SKILL.md`——这强约束实施者只能把 ID 写进 SKILL.md（AC-7 才能通过）。AC 验证形态本身堵死了"光引用不写入"的实施路径。SHOULD 不阻塞；T-1b 实施时实操层面没有歧义。 |
| SHOULD #4 (tasks) | — | n/a | tasks_review_v2 SHOULD 仅 3 条；MUST FIX 1 条。NICE 3 条全是文档清晰度。 |

**3 个 v2 SHOULD FIX**：均"NOT CLOSED but acceptable"——v3 没显式响应，但 v3 已通过其它机制（fixture 硬断言 / AC 验证形态 / 单人执行的并行度损失可接受）覆盖。按 SKILL §3 verdict 判据，SHOULD 不阻塞 APPROVED。Generator 应在 summary.md "Deferred 项" 表里登记这 3 条（v2 SHOULD 接受 deferred + 理由：fixture 硬断言已覆盖 / AC 形态已堵死 / 单人串行影响可控）作为 dogfood 诚实标注。

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 tasks 4 条）

- [x] 每个任务粒度合理（1-3 小时）：T-1a 1.5h / T-1b 1h / T-1c 0.5h / T-2 估值未写但单文件邻段编辑 ≤1h / T-3 1h / T-4 2h / T-5 ≤0.5h / T-6 1.5h / T-7 1.5h / T-8 ≤1h。
- [x] depends_on 无环：DAG L269-L275 `T-1a → {T-1b, T-1c, T-2, T-4, T-5}; T-4 → T-6 → T-7 → T-8; T-3 独立`；reviewer 拓扑排序检查无环。
- [x] 评审 / 单测 / CI / 部署 / 用户确认 对应任务都存在：process_tasks 6 条（P-spec-review / P-code-review / P-test-review / P-ci / P-deploy / P-user-confirm）；`grep -cE "id: P-" tasks.md` = 6。P-ci / P-deploy status=`self-attest` + notes，符合 spec AC-5 stage 9 4 checkpoint 之 (ii)。
- [x] 没有"做完整个系统"类目标任务：T-1a/b/c 已粒度拆分；T-4 / T-6 / T-7 / T-8 各自单一职责。

## 与 spec.md trace 一致性

| AC | tasks 覆盖矩阵 | reviewer 复核 |
|---|---|---|
| AC-1 | T-1a / T-1c / T-5 | ✓ |
| AC-2 | T-1a | ✓ |
| AC-3 | T-2 | ✓ |
| AC-4 | T-4 / T-6 / T-8 | ✓ T-6 三 fixture-bad 完整覆盖（含 v3 新增反例打靶） |
| AC-5 | T-3 | ✓ |
| AC-6 | T-4 / T-5 / T-7 | ✓ T-7 description L201 写"用 AC 行 regex 而非裸 grep" 与 spec.md L118 AC-6 实现一致 |
| AC-7 | T-1b / T-7 | ✓ |
| AC-8 | T-7 / T-8 | ✓ |

每条 AC 至少 1 任务覆盖；behavioral 双 AC（AC-4 + AC-8）各自映射多任务，dogfood 闭环。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无（v2 SHOULD 已视为"deferred but acceptable"——见上方复检表，应在 summary.md Deferred 表登记）。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md v3 闭环表只列 v1 review 闭环（标题 L13 "v1 review 闭环表"）| v3 没有显式 "v2 review 闭环表"。spec.md v3 有 "v2 review 闭环表"（L15-L26），tasks.md v3 仅在 L11 修订说明里一句话带过 "T-4/T-6 双条件 (ii) 同步改"。dogfood 诚实标注角度，建议 tasks.md v3 也加一个 "v2 review 闭环表" 显式列 MUST #1 状态 + 3 个 SHOULD FIX 的 deferred 理由。 | 不阻塞 verdict。可在 stage 3 启动前补，作为"summary.md SSoT 一致性"扩散到 tasks.md 的实践。 |
| 2 | tasks.md DAG 图 L269-L275 | DAG 图清楚，但 T-3 独立性可加注 "T-3 与 T-1a/T-4 完全并行（编辑不同文件，无概念依赖）"；同理 SHOULD #1 提到的 T-2 / T-5 可在 T-1a 完成后立即并行启动。 | 文档清晰度，NICE。 |
| 3 | tasks.md T-2 / T-5 没写 estimated time | T-1a/b/c/T-3/T-4/T-6/T-7 都写了 "预计 ~Xh"，T-2 / T-5 / T-8 未写。粒度评估时不一致。 | 补 T-2 ~1h / T-5 ~0.5h / T-8 ~1h，便于 stage 3 排期。NICE。 |

## v2 → v3 增量缺陷扫描

- v3 修订集中在 tasks.md L11 修订说明 + L136 T-4 (ii) + L169-L186 T-6 三 fixture-bad。**未发现 v2 已 CLOSED 项被 v3 反向破坏**。
- T-4 (ii) 与 spec.md L81 AC-4 (ii) **逐字符同型**（reviewer `diff` 验证），无漂移。
- T-7 description L201 "用 AC 行 regex 而非裸 grep" 与 spec AC-6 实现统一。

## Verdict

**APPROVED**

理由（按 SKILL §3 唯一判据 = 未关闭 MUST FIX 数）：

- v2 1 MUST FIX 真闭环：T-4 (ii) 改锚定 AC 行 regex；T-6 三个 fixture-bad 齐全（含 v3 新增 fixture-bad-static-but-mention-behavioral 关键打靶反例）。
- v2 3 SHOULD FIX 视为"deferred but acceptable"——v3 通过 fixture 硬断言 + AC 验证形态堵死路径 + 单人串行影响可控 隐式覆盖；不阻塞 verdict（SHOULD 不阻塞是 SKILL 明文规约）。
- v3 未引入新 MUST FIX；3 条 NICE TO HAVE 不阻塞。
- DAG 无环、AC 覆盖完整、process_tasks 齐全（6 条）。
- 与 spec v3 双向一致（双条件 (ii) regex 完全同型）。

## 后续指引

- tasks.md APPROVED → 进入 stage 3 编码实现。
- **建议 generator 在 stage 3 启动前**：
  1. summary.md Deferred 表登记 v2 tasks SHOULD #1/#2/#3 三条"deferred but acceptable"+ 理由（满足 SKILL §跨 AC 自审 #9 dogfood "诚实标注"）。
  2. 选填：tasks.md 补 v2 review 闭环表（NICE #1）+ T-2/T-5/T-8 预计时长（NICE #3）—— 不补也不阻塞 stage 3。
- **stage 3 实施时硬约束**：
  - T-4 lint 实现必须严格用 spec L81 / tasks L136 的 regex；任何变体（如改成 awk 列匹配）必须 spawn reviewer 重审。
  - T-6 fixture 必须包含 fixture-bad-static-but-mention-behavioral 反例；缺则 stage 4 code review 应 MUST FIX 打回。
  - T-8 全仓 self_check 必须真跑（行为型 AC-8 自验证），不允许 self-attest 替代——本 change 自身是 stage 9 规约的制定者，不能在 stage 8/9 失节。
