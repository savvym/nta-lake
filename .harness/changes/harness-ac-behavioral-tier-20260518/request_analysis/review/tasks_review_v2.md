---
change_id: harness-ac-behavioral-tier-20260518
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-agent:harness-ac-behavioral-tier-20260518-stage2-reviewer-v2
reviewed_at: 2026-05-18T09:15:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v2

## v1 MUST FIX 复检（reviewer 跑 v1 review 复检指引）

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST #1 | T-4 awk 错误 + T-6 fixture 无 env 入口 | **CLOSED** | T-4 description L132 改为状态机 awk；T-4 L127-L128 列出 `AC_KIND_LINT_SCAN_DIR` + `AC_KIND_LINT_EXEMPT_OVERRIDE` 两个 env 入口；T-6 L170-L173 用 subshell + export env 包裹 `run_ac_kind_lint` 跑两次（fixture-ok PASS / fixture-bad FAIL）+ trap cleanup `/tmp/fixture-*`。reviewer dry-trace 形态合法。|
| MUST #2 | T-1 任务粒度过载（7 子项） | **CLOSED** | 拆为 T-1a（SKILL AC 分层定义 + behavioral 三层判定指引，~1.5h）+ T-1b（豁免清单 19 ID 分两类 + 自声明机制 + 豁免判定标准，~1h）+ T-1c（混合 AC 拆分示例，~0.5h）。`grep -cE "id: T-1[abc]" tasks.md` = 3。|
| MUST #3 | T-6 缺 spec MUST #7 联动（kind 列双检） | **PARTIAL CLOSED** | T-4 description L134 写 `(i) grep -q "\| kind" <段>     # kind 列表头存在；(ii) grep -q "behavioral" <段>  # 至少 1 行 behavioral`；T-6 L168 fixture-bad 设计是"缺 kind 列 OR 全 static"。形态闭环。**但 (ii) 实现继承 spec_review_v2 MUST FIX #2 同型缺陷：`grep -q behavioral` 在 AC 描述里命中即 PASS，机械化保护实质失效**——本 tasks 必须与 spec 同步修。|
| MUST #4 | T-3 4 checkpoint 文案太空 | **CLOSED** | T-3 description L106-L115 列 4 个 checkpoint：(i) verdict=PASS 默认 / (ii) self-attest 替代 + 4 必填字段（理由/本机证据/跑过命令/时间） / (iii) 禁止纯 deferred / (iv) SKILL 引用；附 self-attest 模板片段说明。`grep -cE "verdict=PASS\|self-attest\|必填字段\|禁止.*deferred" tasks.md` = 10（>=4）。 |
| SHOULD #1 | P-ci/P-deploy 改 self-attest | CLOSED | P-ci.status=`self-attest` + notes="项目无 remote..."；P-deploy.status=`self-attest` + notes="纯 harness..."；`grep -cE "status:.*self-attest" tasks.md` = 3（含 v1 闭环表自引用 + 2 实际值）。 |
| SHOULD #2 | T-5 与 spec 非范围矛盾 | CLOSED via spec v2 | spec v2 翻转决策（L145 决策栏 + 非范围 strike-through "~~不改 _template~~"）；T-5 description 注明"v2 与 spec 非范围对齐"。 |
| SHOULD #3 | T-6 fixture 应 stage unit_test | **PARTIAL CLOSED** | T-6 description 含 fixture 真跑断言（"在 subshell 跑两次 run_ac_kind_lint 期望 PASS/FAIL"）但 `estimated_stage: coding`——T-6 是 fixture **脚本**（编码 artifact）放 coding 合理；T-8 estimated_stage=`unit_test` 跑全仓 self_check 是行为型 AC-8 自验证，分层合理。**但 T-7（block 函数）也归 coding（合理），不存在 v1 SHOULD #3 担心的"编码与单测混"——v2 拆 T-6/T-7/T-8 已分离干净。**视为闭环。 |
| SHOULD #4 | T-7 期望值动态 | CLOSED | T-8 description（v2 改名）L208-L213："退码 0 / 本 change block 8/8 PASS / 2 个 global lint PASS / 不强约束总 PASS 数"，不再写死 `PASS: 238`。 |

**v1 4 MUST FIX 复检结论**：3 真闭环；1 部分闭环（MUST #3 形态闭环但实现层与 spec_review_v2 MUST FIX #2 同型缺陷 — `grep -q behavioral` 不锚定 kind 单元格）。**4 SHOULD FIX 全闭环**。

## 检查清单结论

### expert-reviewer SKILL §1 tasks 部分 4 条

- [x] 每个任务粒度合理（1-3 小时）：T-1 拆 a/b/c 后每个 ~0.5-1.5h；T-2..T-8 在 1-3h 内；T-1a 1.5h 略宽但可接受。
- [x] depends_on 无环：DAG 已校验 `T-1a → {T-1b, T-1c, T-2, T-4, T-5}; T-4 → T-6 → T-7 → T-8; T-3 独立`，无环。
- [x] 评审 / 单测 / CI / 部署 / 用户确认 对应任务都存在（process_tasks 6 条都在；P-ci + P-deploy = self-attest，P-* 4 条 pending）。
- [x] 没有"做完整个系统"类目标任务。
- [x] 每条 AC 至少一个 T-* 关联 + 覆盖矩阵清晰（L271-L280）。
- [x] `grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md`：v2 用了"estimated_stage: <name>"格式（request_analysis_review / coding_review / unit_test_review / ci_result / deployment / user_confirmation），命中 6 条——与 SKILL § 跨 AC 自审 #7 等价（只是用 stage 命名而非数字），可接受。

### 与 spec.md trace 一致性

| AC | tasks 覆盖矩阵 | reviewer 复核 |
|---|---|---|
| AC-1 | T-1a / T-1c / T-5 | ✓ |
| AC-2 | T-1a | ✓ |
| AC-3 | T-2 | ✓ |
| AC-4 | T-4 / T-6 / T-8 | ✓（但 T-6 fixture 反例打靶不覆盖 spec MUST FIX #2 漏洞，需补） |
| AC-5 | T-3 | ✓ |
| AC-6 | T-4 / T-5 / T-7 | ✓ |
| AC-7 | T-1b / T-7 | ✓ |
| AC-8 | T-7 / T-8 | ✓ |

每条 AC 至少 1 任务覆盖，process_tasks 6 条齐全。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-4 description L132-L135 双条件 (ii) + T-6 fixture-bad spec 设计 L168 | **与 spec_review_v2 MUST FIX #2 联动**：T-4 description (ii) 写 `grep -q "behavioral" <段>`——裸 grep 不锚定 AC 行的 kind 单元格，被 AC 描述文本里的 "behavioral" 字串触发即假 PASS（详 spec_review_v2 MUST FIX #2 实证：本 spec 6 行命中只有 2 行真为 kind=behavioral）。T-6 fixture-bad 现写"缺 kind 列 OR 全 static"，但未覆盖**最隐蔽的反例**："AC 表有 kind 列、所有 kind 单元格都是 static、但 AC 描述里出现 'behavioral' 字串"——这是机械化保护被绕过的真实场景。 | (a) T-4 description (ii) 改为：`grep -qE "^\| AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|" <段>`，锚定 AC 行的 kind 单元格。(b) T-6 description 加 fixture-bad 第三种反例 spec：`AC 表有 kind 列 + 所有 AC kind=static + 描述含"behavioral"字串` → 必须 lint FAIL。三种 fixture-bad 都跑过才算真覆盖。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-1a/T-1b/T-1c/T-2/T-4/T-5 全部 `depends_on: [T-1a]` | **T-1a 单点 fan-out 过宽，并行度损失**：T-1a 是 SKILL `request-analysis/SKILL.md` 加 §"AC 分层规约" 段编辑任务；T-2 编辑 `expert-reviewer/SKILL.md`（不同文件）、T-4 编辑 `scripts/_self_check.sh`（脚本）、T-5 编辑 `_template/request_analysis/spec.md`（模板），三者都不实际"读"T-1a 的输出文件——只是"概念上以 T-1a 定义的规约为准"。这种"语义依赖"实际上一旦 spec.md 定稿就可以并行实施，T-1a 完成不是 hard prerequisite。结果是 6 个任务串行化，过窄 → 损约 2-3h 并行节省。 | 把 T-2 / T-4 / T-5 的 `depends_on` 改为 `[]`（与 T-3 同列），把"依赖 T-1a 的规约定义"以 description 注脚说明（"实施前查 spec.md AC-1..AC-3 的 SKILL 修改设计"）。T-1b / T-1c 留 `depends_on: [T-1a]` 因为它们改同一个 SKILL.md（避免编辑冲突）。 |
| 2 | tasks.md T-7 description L188 + T-8 description L211 | T-7 / T-8 期望"global run_ac_kind_lint PASS"——但 T-8 在跑全仓 self_check 时若 lint 因 spec_review_v2 MUST FIX #2（描述含"behavioral"也通过）产生**假 PASS**，T-8 仍 exit 0 但实际机械化保护失效——T-8 不能区分真 PASS / 假 PASS。 | T-8 description 加 "rollback 路径 #4：若 lint 对一份故意构造的 fixture-bad（描述含 behavioral 但 kind 全 static）仍 PASS → 回 T-4 修双条件 (ii)"。这条 rollback 与 MUST FIX #1 联动闭环。 |
| 3 | tasks.md T-1b L51-L68 19 个 ID 全列 | T-1b description (b) 写"暂豁免 grandfather（17 个，实代码 change，必须 backfill）：17 个 ID 全列出（见 spec AC-7）"——把 17 ID 列在 spec AC-7 而 T-1b 引用，节省重复。**但 T-1b 实施者实际改 SKILL.md 时必须把 19 个 ID 显式写进 SKILL.md**（不是引用 spec），这一点 description 未明示。 | T-1b description 加一句："19 个 ID 必须显式写进 SKILL.md 豁免段（不是引用 spec）；SKILL.md 是 self_check 读取源，AC-7 for-loop 直接 grep SKILL.md 命中。" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md L271-L280 验收覆盖矩阵 | AC-6 关联 T-4 / T-5 / T-7 三任务，AC 拆解清晰；但 AC-4 关联 T-4 / T-6 / T-8 三任务也较广（覆盖 lint 函数 / fixture script / 自验证），可加注释"AC-4 是行为型核心 AC，三任务分别覆盖：lint 实现 / fixture 真跑 / 整链路自验证"。 | 文档注释，不阻塞。 |
| 2 | tasks.md DAG 图 L259-L264 | DAG 图清楚展示无环，但 T-3 独立的"独立可并行实现"已在文本注明。再清楚标"T-3 与 T-1/T-2/T-4 并行"会更直观。 | 文档清晰度，NICE。 |
| 3 | tasks.md L210 T-8 description "若 fixture 测试本身 FAIL → 回 T-4 / T-6 修 lint 函数" | rollback 路径列了 3 种 fixture FAIL 场景；可补一种"若豁免名单读取错误（误对豁免 change 报 FAIL）→ 回 T-1b 修豁免清单"（已有）。 | 已有，pass。 |

## Verdict

**REVISION REQUIRED**

理由（按 SKILL §3 唯一判据 = 未关闭 MUST FIX 数）：

- **MUST FIX #1**（T-4 双条件 (ii) + T-6 fixture 反例打靶）：与 spec_review_v2 MUST FIX #2 严格联动；spec 修了 tasks 必须同步，且 T-6 fixture-bad 必须打靶 "描述含 behavioral 但 kind 全 static" 这类隐蔽反例，否则机械化保护跑不到的地方就算文档完美也是空头支票。

修完 tasks_v3 后重提评审。

## 复检指引（generator 修 v3 后自查命令）

```bash
cd /data/home/zhhdzhang/nta/nta-lake

# MUST FIX #1: T-4 双条件 (ii) 用 AC 行 regex
grep -nE "ii\).*grep.*AC-\[0-9\]|ii\).*\^\\\\\|" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md
# 期望：T-4 description 中 (ii) 行命中 AC 行 regex（含 ^\| AC- 或等价锚定）

# MUST FIX #1: T-6 fixture-bad 三种反例
grep -nE "fixture-bad" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md
# 期望：T-6 description 列三种 fixture-bad spec（缺 kind 列 / kind 全 static / 描述含 behavioral 但 kind 全 static）

# SHOULD FIX #1: depends_on 解耦
grep -cE "depends_on: \[T-1a\]" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md
# 期望：≤2（仅 T-1b 与 T-1c；T-2/T-4/T-5 解耦后 depends_on: []）

# SHOULD FIX #2: T-8 rollback #4
grep -A 8 "rollback\|如 FAIL" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md | grep -E "fixture-bad.*PASS|描述含 behavioral"

# 与 spec_review_v2 MUST FIX 联动：tasks v3 与 spec v3 必须同步生成
diff <(grep -E "(i\) grep|ii\) grep" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md | head -1) \
     <(grep -E "(i\) grep|ii\) grep" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md | head -1)
# 期望：spec 与 tasks 的双条件描述一致
```

复检 v3 tasks 重提评审时，请同步开 `tasks_review_v3.md`（不要覆盖本 v2 文件）。
