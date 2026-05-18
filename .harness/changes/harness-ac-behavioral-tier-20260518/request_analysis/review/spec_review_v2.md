---
change_id: harness-ac-behavioral-tier-20260518
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-agent:harness-ac-behavioral-tier-20260518-stage2-reviewer-v2
reviewed_at: 2026-05-18T09:15:00Z
verdict: REVISION REQUIRED
---

# Spec Review v2

## v1 MUST FIX 复检（reviewer 实跑 v1 review 复检指引中的 bash 命令）

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST #1 | AC-4 + 风险表的 `awk '/## 验收标准/,/^## /'` 起止同行命中 → 大面积误报 | **CLOSED** | spec.md L64/L102 改为状态机 `awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p'`；reviewer 本机对 19 个 closed change spec 逐个跑此 awk：所有 spec 返回 **≥13 行**（repo-api-mvp 13 / processor-framework 15 / harness-bootstrap 18 / commit-api-mvp 102 等），完整覆盖 AC 表段，无 1 行假阳性。 |
| MUST #2 | "18 个" 计数错且豁免标准 17/19 不合理 | **PARTIAL CLOSED**（见 MUST FIX #1） | spec 正文 8 处改为 "19 个"，且 AC-7 把 17 + 2 拆分清楚；但 **summary.md L57 仍写 "18 个 closed change"**——v1 复检指引明确要求 "summary.md 一致性同步"，未完成 ⇒ 落到新 MUST FIX。 |
| MUST #3 | AC-7 三 ID 单行 grep 实跑 NOT MATCH | **CLOSED** | AC-7 改为 `for cid in <19 ID>; do grep -q "$cid" SKILL.md \|\| exit 1; done && grep -q "永久豁免" && grep -q "暂豁免"`；reviewer 在临时构造的 SKILL.md（含 19 ID + 两类字面）上 dry-run for-loop 形态合法，每 ID 独立校验，不再单行依赖。 |
| MUST #4 | self-attest vs deferred 语义未闭合 + 必填字段 | **CLOSED** | AC-5 验证扩展为 4 grep（verdict=PASS / self-attest / 禁止 deferred / 必填字段）；spec L88 P-ci 文案改 "self-attest + 必填字段"；spec L69-L74 列 4 checkpoint 含 self-attest 模板片段。语义闭合：self-attest 是允许的特例（含 4 必填字段），纯 deferred 被禁。 |
| MUST #5 | 豁免判定标准缺失 + reviewer 复核机制缺 | **CLOSED** | spec L114 风险表"新规约导致小型 PR 流程过重"缓解：豁免判定标准量化（代码改动只在 `.harness/*` / `wiki/*` / `scripts/*` / `*.md`）；L117 新增风险"`ac_kind_lint: exempt` 自声明被滥用"，缓解为 `expert-reviewer/SKILL.md` 加 stage 2 必查 `git diff --stat` + 附结果到 review。AC-3 验证 `grep -qE "git diff.*ac_kind_lint" expert-reviewer/SKILL.md` 也强制了文档落地。 |
| MUST #6 | fixture 真跑机制未具象（缺 SCAN_DIR/EXEMPT env + fail-fast 撞墙） | **CLOSED** | AC-4 验证由 `bash scripts/lint/test_ac_kind_lint_fixture.sh` 一行触发；T-4 description 列两个 env 入口（`AC_KIND_LINT_SCAN_DIR` / `AC_KIND_LINT_EXEMPT_OVERRIDE`），T-6 description 明确 fixture 用 subshell 跑 `(export AC_KIND_LINT_SCAN_DIR=/tmp/fixture-ok ...; run_ac_kind_lint)` 防 fail-fast 污染；trap cleanup 在 T-6。 |
| MUST #7 | reviewer 字段约束缺机械化（仅 SKILL 文档约束 = 重蹈 reviewer-separation 治理前） | **PARTIAL CLOSED**（见 MUST FIX #2） | spec L118 风险表新增"reviewer 字段约束仅靠 SKILL"+ 缓解"`run_ac_kind_lint` 双条件断言"；T-4 description L132-134 写 `(i) grep -q "\| kind" <段>；(ii) grep -q "behavioral" <段>`。**但 (ii) 的实现 `grep -q "behavioral"` 在 AC 表段内随便一行命中即 PASS——本 spec 自身 6 行含"behavioral"字串中只有 2 行的 `kind` 真值是 behavioral**，机械化保护被绕过（详新 MUST FIX #2）。 |
| SHOULD #1 | AC-4 描述过长违反一行式 | CLOSED | 拆出 `scripts/lint/test_ac_kind_lint_fixture.sh`，AC-4 验证只剩一行。 |
| SHOULD #2 | AC-5 grep 缺 test -f | CLOSED | AC-5 改为 `test -f .harness/rules/development-process.md && grep -A 60 ... \| grep -q ...`，符合 SKILL §6 模式。 |
| SHOULD #3 | AC-7 单行 grep 不可命中 | CLOSED via MUST #3 | — |
| SHOULD #4 | 混合 AC 拆分缺示例 | CLOSED | spec L144 决策栏新增"混合型 AC 拆分示例（伪代码）"：AC-N → AC-Na (static, grep router) + AC-Nb (behavioral, ASGITransport pytest)，清晰可参照。 |
| SHOULD #5 | AC-8 写死 PASS 数易脆 | CLOSED | AC-8 改为 "退码 0 + 本 change block 8/8 PASS + 2 个 global lint PASS"，不再写死总 PASS 数。 |
| SHOULD #6 | behavioral 三层判定 | CLOSED | spec L115 风险表 + L142 决策栏明确 (L1) curl smoke / (L2) ASGITransport / (L3) load_recipe pydantic parse；T-1a description L34-L40 同步落地到 SKILL 编辑指令。 |

**v1 11 个 MUST FIX 逐条复检结论**：9 真闭环；2 落空（#2 summary.md 未同步、#7 双条件 (ii) 语义破损）。

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 + request-analysis SKILL 跨 AC 自审 9 条）

### plan 模式 spec.md 6 条

- [x] 背景：清晰承接 pipeline-orchestrator stage 9 三 bug。
- [x] 问题陈述与目标：自递归 dogfood 清楚（"本 spec 自身就是新规约第一个真用例"）。
- [x] 范围 / 非范围：6 条非范围显式列出，含 v1→v2 决策翻转（_template 加列）有 strike-through 历史保留。
- [x] 验收标准每条都可演示且可机械化——核心机械化 `awk` 已修复；但 AC-7 缺 `test -f .harness/skills/request-analysis/SKILL.md` 前置（详 SHOULD FIX #1）。
- [x] 风险有缓解措施或显式 accept——7 条均配缓解。
- [x] 没把已有架构当新提案。

### 跨 AC 一致性自审 9 条

| # | 条目 | 状态 | 评语 |
|---|---|---|---|
| 1 | 四链路一致（schema/hash/idempotency/fixture） | n/a | 无 DB schema / hash |
| 2 | 事务边界三处一致 | n/a | 无事务 |
| 3 | AC 验证命令一行式 | PASS | AC-4 已拆 fixture；AC-5/AC-8 是合理的多步 grep 链。 |
| 4 | 风险缓解 ↔ AC 测试 | PASS | 7 条风险均映射到 AC-3/AC-4/AC-8 测试。 |
| 5 | commit parents 检查 | n/a | 无 commit 写入 |
| 6 | 反向 grep + test -f + 不吞 stderr | PASS | spec 无 `! grep`、无 `2>/dev/null`；正向 grep 都配 `test -f`（AC-1..AC-6 已加，AC-7 漏一个，详 SHOULD FIX #1）。 |
| 7 | process_tasks 6 条 | PASS | tasks.md 含 6 条 process_tasks；P-ci/P-deploy status=`self-attest` + notes，与 spec AC-5 一致。 |
| 8 | AC 验证命令 dry-parse | PASS | spec 无 python -c 复合语句；awk 已 dry-run 验证（见 v1 MUST FIX #1 复检）。 |
| 9 | summary.md 占位符残留 | PASS | `grep -cE "<feature-slug>\|<YYYY-MM-DDTHH:MM:SSZ>\|<复述\|<bullet list>" summary.md` = 0。 |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | summary.md L57（关键决策栏第 1 行） | **v1 review MUST FIX-2 复检指引明确要求"summary.md 一致性同步"未完成**：summary.md L57 仍写 "18 个 closed change 全量回填工作量超本 change 承载"。这是 v1 reviewer 显式列出的复检条目（"(d) summary.md 一致性同步"），spec v2 闭环表声明 CLOSED 但 summary.md 未真改。本变更核心议题是"机械化诚实标注"——meta-change 自身在 summary 里继续印错数，dogfood 破功。 | summary.md L57 把 "18 个 closed change" 改为 "19 个 closed change"。同时建议借机把该决策行的"grandfather 旧 change"补成"grandfather 旧 change 分两类（2 永久 + 17 暂豁免，后续 backfill）"以与 spec AC-7 字面一致。 |
| 2 | spec.md L65 + L118（双条件断言 (ii) 实现）+ tasks.md L132-L135 | **双条件断言 (ii) `段内至少 1 行含 behavioral` 是裸 `grep -q behavioral`，会被 AC 描述文本里的 "behavioral" 字串触发，机械化保护实质失效**：实测本 spec v2 AC 表段 `grep -c behavioral` = **8 次命中**，但其中只有 AC-4 / AC-8 的 `kind` 单元格真为 behavioral，AC-1 / AC-2 / AC-3 / AC-6 的 `kind=static` 但描述里提到 "behavioral 三层 / behavioral AC / kind: behavioral" 等概念。一个未来 spec 可以写 6 条 `kind: static` AC、在描述里任何位置塞一句"参考 behavioral 三层"，lint 即 PASS。这正是 v1 MUST #7 想堵的 "harness-reviewer-agent-separation 治理前同型"漏洞——SKILL 写了硬约束但 lint 没有真守门。本 change 自我设计的最后一道机械门被绕过。 | (ii) 实现改为锚定 AC 表行结构：`grep -qE "^\\| AC-[0-9]+[a-z]?[[:space:]]*\\|[[:space:]]*(\\*\\*)?behavioral(\\*\\*)?[[:space:]]*\\|" <段>`，即 "AC-X 行的 kind 单元格"必须真为 behavioral。同步：spec.md L65、L118 描述、tasks.md T-4 L132-L135 description、T-6 fixture 的 /tmp/fixture-bad spec 设计成 "AC 描述里含 'behavioral' 字串但所有 kind 单元格都是 static" 这一最隐蔽场景去专项打靶——若 fixture 不覆盖此场景，本 MUST 修了也只是文案，跑不到机械化打靶。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md L103（AC-7 for loop 前缺 `test -f`） | AC-7 验证：`for cid in ...; do grep -q "$cid" .harness/skills/request-analysis/SKILL.md \|\| exit 1; done && grep -q "永久豁免" ... && grep -q "暂豁免" ...`——若 SKILL.md 不存在，每次 grep 退码 2，for loop 第一次 `exit 1` 触发，AC 报 FAIL 但 FAIL 原因是"路径错"不是"豁免名单缺"，与 SKILL §6 精神（test -f 让路径错暴露而非把"零代码状态"误成 lint 失败）不完全一致。 | 在 for loop 前加 `test -f .harness/skills/request-analysis/SKILL.md &&`，与 AC-1/AC-2 一致。 |
| 2 | spec.md L101（AC-5 `grep -A 60`）| `grep -A 60 "## 阶段 9"` 把 stage 9 + stage 10 + 文末完全吞下；若 stage 10 段未来加入 "verdict: deferred 示例"，AC-5 第三条 `grep -q "禁止.*deferred"` 仍 PASS 但 stage 9 本身没那行也能假阳性。当前文件 stage 9 段只到 stage 10 标题之前的 9 行，60 偏大。 | 用 awk 状态机抽 stage 9 段（同 awk 模式：`awk '/^## 阶段 9/{p=1;next} p && /^## 阶段 /{exit} p'`），不再依赖 `-A 60` 行数硬编码。 |
| 3 | spec.md L140（决策栏第 1 行）| 决策栏第 1 行写"19 个历史中 2 个真纯 harness 永久豁免、17 个实代码暂豁免"，与 summary.md L57 的 "18 个" 仍不一致——dogfood meta-change 必须前后口径完全一致才有说服力。修了 MUST #1 自然带出。 | 修 MUST FIX #1 时一并对齐。 |
| 4 | spec.md L31（v1 闭环表 MUST #1 行写"对 pipeline-orchestrator-mvp/spec.md 返回 37 行"）| 已被 reviewer 实测验证；但行数应该是"≥13 行（最少的 repo-api-mvp）"，37 只是单一样本。 | 改为"对所有 19 个 closed spec 跑该 awk，最少返回 13 行（repo-api-mvp），最大 102 行（commit-api-mvp）"，更准确支撑闭环。 |
| 5 | spec.md "Behavioral AC 数：2（AC-4 / AC-8）" L106 + AC-6 L102 期望 "behavioral 计数 ≥ 2" | AC-6 用 `[ "$(... \| grep -c behavioral)" -ge 2 ]`，等价于裸字串计数，**继承 MUST FIX #2 的同型缺陷**。AC-6 期望"本 spec behavioral 计数 ≥ 2"如果按 AC 行严格匹配是 2，按裸 grep 是 8——AC 期望与 lint 实现不对齐。 | 与 MUST FIX #2 一并修：AC-6 内的 `grep -c behavioral` 改为 `grep -cE "^\\| AC-[0-9]+[a-z]?[[:space:]]*\\|[[:space:]]*(\\*\\*)?behavioral(\\*\\*)?[[:space:]]*\\|"`，与新双条件实现保持一致。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md AC-7 + tasks.md T-1b L57-L59 把 19 个 ID 硬编码 | AC-7 硬编码 19 ID，未来再 close 第 20 个 change（如本 change 自身）后 AC-7 会失效（因为本 change 自身不在 19 ID 列表，且生效后强制 kind 列）。但因本 change 是 lint 制定者自身豁免（永久豁免 3 个？），SKILL 永久豁免清单需在 T-1b 同时把本 change ID 加入。 | T-1b description 补"`harness-ac-behavioral-tier-20260518` 自身也加入永久豁免（meta-change 制定者）"或"本 change 自带 ≥1 behavioral AC（dogfood），不需豁免"。建议后者更诚实，spec 已是 dogfood，不要把"制定者"加豁免名单。NICE 不阻塞。 |
| 2 | spec.md 引用段 | 缺 `harness-pipeline-orchestrator-mvp/.harness/changes/.../deploy_verify_v1.md` 完整路径 | 已写引用 § "需要 follow-up"，但绝对路径片段是相对的；NICE。 |

## v1 reviewer 提出的"19 个豁免"是否合理性复审

v1 reviewer 在 v1 review § 豁免清单审查 列出 19 个 change 的 grandfather 合理性（2/19 合理、17/19 不合理但建议保留 + backfill）。v2 spec 接受了该建议（spec AC-7 明确分两类 + follow-up `harness-ac-kind-backfill-*` 标 P1）。reviewer v2 确认这是**最优实践**：不让 grandfather 成为永久豁免、不让 follow-up 无限 deferred、显式诚实标注。该方面已闭环。

## v1 决策翻转（_template 加 kind 列）合理性复审

v1 spec 非范围曾说"**不**改 _template/request_analysis/spec.md 表头自动加 kind 列"；v2 翻转为"加列"。reviewer 评估：

- 翻转理由（spec L145 决策栏）："让新 change 复制 _template 时自然带列，扩散更顺；v1 担心冲击旧 review 工具，但实际旧 change 不动 _template 影响"——**合理**。
- 旧 change 已 close 不再复制 _template，所以"冲击"实际不存在。
- 新 change 复制 _template 时直接有 `kind` 列，0 心智成本即可触发 lint 通过路径——dogfood 闭环更紧。

翻转决策成立。

## Verdict

**REVISION REQUIRED**

理由（按 SKILL §3 唯一判据 = 是否还有未关闭 MUST FIX）：

- **MUST FIX #1**（summary.md L57 "18 个" 未同步）：v1 review 复检指引第 (d) 条明确要求"summary.md 一致性同步"，spec v2 闭环表自称 CLOSED 但 summary.md 未真改。即使是 1 处文字差异，本 meta-change 的核心议题就是"机械化诚实标注"——dogfood 在自己的 summary 里继续印错数，是 self-contradicting。
- **MUST FIX #2**（双条件 (ii) `grep -q behavioral` 语义破损）：v1 MUST #7 的机械化目的（让 lint 真守门、不重蹈 reviewer-separation 治理前漏洞）在 v2 实现层面被绕过。该漏洞与本 change 的**核心命题**直接冲突——AC-7 "lint 抓不到没标 kind: behavioral 的 spec" 是本 change 存在的理由。文档闭环但实现可被绕过 = 假闭环。

修完 v3 重提评审；预计修改集中在：
- summary.md L57 数字 + decision-row 表述
- spec.md L65、L118 双条件 (ii) 改为锚定 AC 行 kind 单元格 regex
- spec.md AC-6 内 `grep -c behavioral` 同步改 regex
- tasks.md T-4 description L132-L135 双条件 (ii) 同步改 regex
- tasks.md T-6 fixture description 补"全 static 但描述含 behavioral 字串"反例打靶

其余 9 个 v1 MUST FIX 真闭环；6 个 SHOULD FIX 全闭环；3 个 NICE 全闭环。v2 没有引入除 MUST #1/#2 之外的新缺陷。

## 复检指引（generator 修 v3 后自查命令）

```bash
cd /data/home/zhhdzhang/nta/nta-lake

# MUST FIX #1: summary.md 18→19 同步
grep -nE "18 个" .harness/changes/harness-ac-behavioral-tier-20260518/summary.md
# 期望：0 行命中（全文不再有"18 个"）

# MUST FIX #2: 双条件 (ii) 用 AC 行 regex 而非裸 grep behavioral
grep -nE 'grep -[a-zE]*[c|q].*behavioral' .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md | grep -v "kind 列\|至少 1 行\|behavioral AC\|kind: behavioral\|至少.*条.*behavioral"
# 期望：所有命中行都用 AC 行 regex（含 ^\| AC- 锚点），而非裸 grep -q behavioral

# MUST FIX #2 同步 tasks.md T-4
grep -nE "(i\) grep|ii\) grep" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md
# 期望：(ii) 的 grep 含 AC- 锚点

# MUST FIX #2 fixture 反例打靶
grep -nE "fixture-bad|全 static.*behavioral|描述含 behavioral" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md
# 期望：T-6 description 含"fixture-bad spec 设计：全 static 但描述含 behavioral"反例打靶语句

# SHOULD FIX #1: AC-7 加 test -f
grep -A 1 "AC-7" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md | grep -E "test -f.*SKILL"
# 期望：1 行命中

# SHOULD FIX #2: AC-5 用 awk 抽 stage 9 段（可选，若仍保留 -A 60 也接受）
grep -nE "AC-5.*awk.*阶段 9|awk.*阶段 9" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md

# 跨 AC 自审 #9: summary.md 占位符残留
grep -cE "<feature-slug>|<YYYY-MM-DDTHH:MM:SSZ>|<复述|<bullet list>" .harness/changes/harness-ac-behavioral-tier-20260518/summary.md
# 期望：0
```

复检 v3 spec 重提评审时，请同步开 `spec_review_v3.md`（不要覆盖本 v2 文件）。
