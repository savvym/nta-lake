---
change_id: harness-ac-behavioral-tier-20260518
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:harness-ac-behavioral-tier-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T09:30:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 + request-analysis SKILL 跨 AC 自审 9 条）

### plan 模式 spec.md 6 条

- [x] 背景：清晰说明了"为什么现在做" —— 实证 pipeline-orchestrator stage 9 抓到 3 个 bug + self_check 226/226 是 grep 假象。
- [x] 问题陈述与目标：外部读者可读，引用 deploy_verify_v1.md 具体证据章节。
- [x] 范围 / 非范围：分明，非范围 6 条显式列出（含已被覆盖的、要拆 follow-up 的、长期未决的）。
- [x] **验收标准每条都可演示且可机械化** —— 但 AC-4 的核心机械化命令（awk 截段）**形态合法、语义破损**，详 MUST FIX-1。
- [x] 风险有缓解措施或显式 accept —— 5 条均配缓解；但第 2 条"awk '/## 验收标准/,/^## /' 截断"本身是错误缓解，详 MUST FIX-1。
- [x] 没把已有架构当新提案 —— harness 范畴，不撞 design.md。

### 跨 AC 一致性自审 9 条（request-analysis SKILL）

| # | 条目 | 状态 | 评语 |
|---|---|---|---|
| 1 | 四链路一致（schema/hash/idempotency/fixture） | n/a | 无 DB schema / hash 逻辑 |
| 2 | 事务边界三处一致 | n/a | 无事务 |
| 3 | AC 验证命令一行式 | partial | AC-4 是多步 bash dry-run，无法压缩到一行，需引用 fixture script（详 SHOULD FIX-1） |
| 4 | 风险缓解 ↔ AC 测试 | partial | "awk 锁定 AC 表段" 缓解 ≠ 真实 AC-4 测试断言；二者不对齐 |
| 5 | commit parents 检查 | n/a | 无 commit 写入 |
| 6 | **反向 grep + test -f + 不吞 stderr** | **FAIL** | AC-5 的 `grep -A 30 "## 阶段 9"`、AC-7 的 `grep -qE "harness-bootstrap-20260516.*bootstrap-monorepo.*pipeline-orchestrator-mvp-20260518"` 都没有 `test -f` 前置；详 SHOULD FIX-2/3 |
| 7 | process_tasks 6 条 | partial | tasks.md 已有 6 条 process_tasks，但 P-deploy=skipped、P-ci=deferred，与本 change 自带的 stage 9 强制门禁文案语义矛盾（自递归），详 MUST FIX-4 |
| 8 | AC 验证命令 dry-parse | **FAIL** | AC-4 的核心 awk 表达式 dry-run 后语义错误（详 MUST FIX-1）；AC-7 的 grep pattern 实跑也会 NOT MATCH（详 SHOULD FIX-3） |
| 9 | summary.md 模板占位符残留 | PASS | summary.md frontmatter 已填好 |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md L55（AC-4）+ L68（风险表第 2 行） | **`awk '/## 验收标准/,/^## /'` 形态对、语义错**：当起始模式行（`## 验收标准`）本身也匹配结束模式 `^## `，awk 把范围立刻在同一行关闭。本 reviewer 实测：对 `.harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/spec.md`、`llm-qa-gen-20260518/.../spec.md`、`sdk-cli-mvp-20260518/.../spec.md` 跑该 awk，**输出均为 1 行**（仅章节标题），AC 表内容根本未被扫描。意味着 lint 一旦启用，所有"正常"新 change 必 FAIL，但 FAIL 原因不是"没写 behavioral"而是 awk 错误——会大面积误报、随后被弱化或绕过，**机械化失效，反 grep 假象的初衷被打脸**。本 spec 自身因风险表自引用恰好命中（risk 行字面包含"## 验收标准"），反而"通过"——这是更隐蔽的假阳性。 | 把 AC-4 的 awk 表达式改为状态机式抽段：`awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p'`。spec.md 风险表第 2 行同步更新引用。AC-4 验证方式需明确包含"对一个真实历史 spec（非本 change）跑抽段 → 应返回 ≥10 行（包含 AC 表）"作为正向断言。 |
| 2 | spec.md L50-L59（AC 表）+ L66（风险表"历史 18 个 change"）+ L41（非范围）+ summary.md L57 | **豁免清单的"18 个"事实计数错误，且豁免标准本身违反 AC-2 精神**：本 reviewer 列举 `ls .harness/changes/` 去除 `_template` 与本 change 后共 **19 个 closed change**（不是 18）：bootstrap-monorepo / core-domain-model / cas-storage / auth-scaffold / repo-api-mvp / commit-api-mvp / rq-worker-skeleton / processor-framework / adapter-framework / llm-gateway-mvp / adapter-firecrawl / llm-qa-gen / web-mvp-pages / web-write-flows / repo-files-tab / sdk-cli-mvp / pipeline-orchestrator-mvp / harness-bootstrap / harness-reviewer-agent-separation。其中**仅 2 个**真正"纯 harness/纯文档"（harness-bootstrap-20260516、harness-reviewer-agent-separation-20260518），**其余 17 个均含 dataplat 实代码**（含 sdk-cli-mvp = SDK + CLI 实代码、pipeline-orchestrator-mvp = DB schema + 路由 + worker job、bootstrap-monorepo = apps 骨架等）。把这 17 个全部 grandfather 进豁免 = 在新规约"非纯文档/纯 harness change 至少 1 条 behavioral AC"语义层面**违背 AC-2 自身**。 | (a) 计数从 18 → 19。(b) SKILL.md 豁免清单同段**显式分类**：第 1 类"纯 harness"（2 个，永久豁免）；第 2 类"实代码 change，仅因历史原因暂豁免，必须 backfill"（17 个）+ 附"优先级：高；跟进 change `harness-ac-kind-backfill-*`"。(c) follow-up `harness-ac-kind-backfill-*` 单独列出"P1（下个非紧急 sprint）"——避免无限 deferred。(d) summary.md 一致性同步。 |
| 3 | spec.md L37（AC-8）+ L84（不受影响模块"18 个历史 closed change"） | **18/19 数字穿插不一致**：spec 多处都写 "18 个历史 closed change"，但实测数为 19。AC-7 的精确 grep 模式 `harness-bootstrap-20260516.*bootstrap-monorepo.*pipeline-orchestrator-mvp-20260518` 假定 SKILL.md 内能用三个 change ID 在**一行**内顺序出现——这对豁免清单（通常按表格列出）是病态的。机械化命中条件不可执行。 | (a) 全文统一改为"19 个历史 closed/done change"。(b) AC-7 grep 改为对**每个 change ID 单独命中**（`for cid in <list>; do grep -q "$cid" SKILL.md \|\| exit 1; done`）或断言"豁免表至少 19 行"。(c) 风险表第 1 条同步更新。 |
| 4 | tasks.md L121-L127（process_tasks P-ci=deferred / P-deploy=skipped）+ spec.md AC-5 | **自递归门禁矛盾**：AC-5 写"stage 9 不允许 deferred"，但本 change 自身 stage 8 status=deferred、stage 9 status=skipped（summary.md L49-L50）。spec 解释"纯 harness 无部署面 → self-attest 替代"，但**self-attest 的具体格式 / 本机证据**未在 development-process.md stage 9 文案里出现（只写"verdict 必须 PASS（或 self-attest 显式说明且含本机证据）；不允许 deferred"——self-attest 既然替代 deferred，那它是"允许的特例"还是"被禁止的伪装 deferred"？语义未闭合）。如果 self-attest 是 deferred 的换皮，则 AC-5 等于纸面文案；如果不是，则必须给出最小可填字段集。 | 在 spec AC-5 验证方式里精确化文案要求：development-process.md stage 9 段需含 (i) 默认硬约束 verdict=PASS；(ii) 替代路径：`self-attest (理由)` + 必填字段（理由 / 本机证据列表 / 跑过的命令 / 时间）；(iii) **禁止纯 deferred**（无 self-attest）。并把 self-attest 模板片段也加进 SKILL（如 reviewer-lint 同型）。同时 tasks.md P-deploy=skipped 改 status=`self-attest`，附理由"纯 harness 无部署面"——形成自递归 dogfood。 |
| 5 | spec.md L31（AC-2 措辞"每个非纯文档/纯 harness change"）+ L36（AC-5 豁免清单"纯 harness / 纯文档"）+ 风险表第 3 行 | **"纯 harness" / "纯文档"判定主观，缺乏可机械化标准 + 缺豁免审查机制**：现 spec 把"自声明 `ac_kind_lint: exempt`"作为豁免机制；意味着任何 change 都可以一行 yaml 自证清白 = 滥用面**很大**。无任何"豁免审查"机制（reviewer 评 spec 时是否要复核 `ac_kind_lint: exempt` 声明真实性？）。spec 风险表第 3 行只写"文档/纯 harness change 可显式 ac_kind_lint: exempt 自豁免"，未说滥用风险。 | (a) 在 SKILL "AC 分层规约"段加"豁免判定标准"小段：必须满足"代码改动行 = 0（仅 .harness/* + wiki/* + scripts/* + 文档 *.md）"才可声明；(b) reviewer-agent.md / expert-reviewer SKILL stage 2 必查项加"若 spec 声明 `ac_kind_lint: exempt` → reviewer 必须验证本 change 实际改动是否符合豁免标准（git diff --stat 跑过证据；附在 review）"；(c) spec 风险表新增一行"豁免被滥用"+ 缓解方案。 |
| 6 | spec.md L34（AC-4 验证方式"在 /tmp 造临时 change 目录"）+ tasks.md T-6 | **AC-4 的 fixture 真跑机制未具象**：spec 写"在 /tmp 造临时 change 目录 + 临时豁免清单 override，执行 run_ac_kind_lint，断言两种状态下退码不同"——但 (i) `run_ac_kind_lint` 现设计是扫 `.harness/changes/<id>/`，**没有可注入的 SCAN_DIR 环境变量**；(ii) 如何 override 豁免清单（写在 SKILL.md 文档里硬编码）未交代；(iii) 现 `run_reviewer_lint` 同型函数（已实现）是 fail-fast `exit 1`，AC-4 fixture 第一次 FAIL 必终止 self_check 后续 block。fixture 真跑落不到地。 | (a) AC-4 验证改为：在 `scripts/_self_check.sh` 加 `run_ac_kind_lint` 时增 `AC_KIND_LINT_SCAN_DIR`、`AC_KIND_LINT_EXEMPT_OVERRIDE` 两个 env 入口；(b) fixture 测试用例改在 `run_harness_ac_behavioral_tier()` block 内部跑（不是替代 main 调用），通过 `AC_KIND_LINT_SCAN_DIR=/tmp/fixture-ok` 跑 PASS、`AC_KIND_LINT_SCAN_DIR=/tmp/fixture-bad` 跑 FAIL（fixture 内部用 subshell 防 exit）；(c) tasks.md T-4 与 T-6 同步把上述设计落到 description。 |
| 7 | spec.md 风险表（缺一类风险） | **缺"reviewer 评 spec 时不会顺手检查 kind 字段，仅靠 lint 抓"风险**：本变更把责任下放到 (i) reviewer 必查（SKILL 文字约束）+ (ii) self_check lint（脚本守门）。但 reviewer 字段是文档约束，自检脚本是机械约束——历史教训（harness-reviewer-agent-separation 背景）正是"SKILL 写了硬约束但没机械化 → 21 份 review 全违规"。本 change 必须在 AC 层 mechanically 强制 reviewer 字段填写规约也覆盖"AC kind 列存在"——否则纯靠 reviewer 主动看清单 = 重蹈覆辙。 | (a) 风险表新增一行"reviewer 字段不会被实际审查（与 harness-reviewer-agent-separation 同型）→ 缓解：AC-4 的 lint 函数同时硬检查（i）spec.md AC 表存在 `kind` 列表头、（ii）至少 1 行 behavioral，二者缺一 FAIL"；(b) AC-4 验证方式扩展到双条件断言；(c) tasks.md T-4 中加表头校验。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md L55（AC-4 描述）| AC-4 的描述塞进了大量步骤（"造临时 spec.md + 临时豁免清单 override + cleanup trap"），违反"AC 一行式"自审清单第 3 条精神；应抽到 fixture script 文件 | 把 AC-4 fixture 拆出去为 `scripts/lint/test_ac_kind_lint_fixture.sh`（仿 self_check 模式），AC-4 验证命令只写 `bash scripts/lint/test_ac_kind_lint_fixture.sh` |
| 2 | spec.md L56（AC-5） | grep 命令缺 `test -f`：`grep -A 30 "## 阶段 9" .harness/rules/development-process.md` 若文件缺失会输出空，pipe 后 `grep -q "..."` exit 1，本意是 lint FAIL 但被外层吞掉。应符合 SKILL #6 反向 grep 模式 | 改写为 `test -f .harness/rules/development-process.md && grep -A 30 "## 阶段 9" ... \| grep -qE "..."` |
| 3 | spec.md L58（AC-7） | grep pattern `"harness-bootstrap-20260516.*bootstrap-monorepo.*pipeline-orchestrator-mvp-20260518"` 假定三个 ID 在**单行**顺序出现——但 SKILL 豁免清单应该是分行的 markdown 表格 / 列表；这条 grep 实跑无法命中 | 改用 19 条独立 grep 循环（同 MUST FIX-3）；或断言豁免段"行数 ≥ 19 + 含字串 `ac_kind_lint`" |
| 4 | spec.md 风险表第 4 行 + L74（受影响模块） | 风险表"`kind: behavioral` 的判定主观"缓解写"SKILL.md 加判定指引"，但 spec.md 没说"混合型拆为两条"的**示例**——SKILL 改动是 T-1 任务的描述里，没在 spec.md 体现 | spec 决策栏（关键决策表）补一行：示例混合型 AC（如"AC-N: behavioral：HTTP POST → 200；同时 grep 路由文件含 `@router.post(...)`"），拆为 AC-Na (behavioral) + AC-Nb (static) |
| 5 | spec.md L37（AC-8） | 验证方式写"`DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 ... bash scripts/_self_check.sh` 退码 0 且本 change block 全 PASS"——但 self_check 现在含 `run_reviewer_lint` 是 fail-fast，新加的 `run_ac_kind_lint` 也将 fail-fast。若 lint FAIL，后续 block 一行不跑——expected count 难以精确（"PASS: 238 + 8 + 1"）。 | AC-8 验证方式改为：`tail -3` 的 PASS 计数 ≥ 旧基线（动态）；本 change block 8/8 PASS（grep block 输出而非全仓总数） |
| 6 | spec.md 决策栏 / 风险表 | "behavioral AC 不强求 docker compose 全栈起服务，可接受 ASGITransport + monkeypatch + in-process fake" 这条决策很重要，但 spec 没列在 SKILL 应该展开的"判定指引"里 | SKILL "判定指引"段加 behavioral 三层：(L1) 真起服务 curl smoke；(L2) ASGITransport in-process roundtrip；(L3) load_recipe / pydantic parse 真跑——所有都算 behavioral；纯 grep / test -f / dry-import 都算 static |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md "引用"段 | 缺对 CLAUDE.md 硬约束 #5 的精确章节定位（写"防复发机制补回 .harness/"但没指 rules 还是 skills） | 补一句"本变更落 skills（SKILL.md 加段） + scripts（self_check lint），不动 rules/coding-style"（已隐含；写明更好） |
| 2 | spec.md 决策栏 | "AC kind 二分不引入 mixed" 决策很对，但例子可在决策栏附 1 条混合 AC 拆法的伪代码 | 见 SHOULD FIX-4 |
| 3 | tasks.md DAG | T-3 是孤立任务（development-process.md 加文案），可考虑 depends_on: [T-1]——让 SKILL 文档先稳定，rule 文档再统一更新 | depends_on 留空可接受；NICE 不阻塞 |

## 豁免清单审查（reviewer 实质责任）

| Change ID | 真实代码改动？ | 豁免合理性 | 建议处置 |
|---|---|---|---|
| harness-bootstrap-20260516 | 否（.harness/ + wiki/） | 合理 | 保留豁免（纯 harness） |
| harness-reviewer-agent-separation-20260518 | 仅 scripts/_self_check.sh（shell） + .harness/* | 合理（无 dataplat 业务代码） | 保留豁免（纯 harness）|
| bootstrap-monorepo-20260516 | **是**（apps/api skeleton + apps/web skeleton + docker-compose） | 不合理 | grandfather 但标"优先级：高 backfill" |
| core-domain-model-20260516 | **是**（packages/core domain + apps/api ORM + alembic） | 不合理 | grandfather + 高优先 backfill |
| cas-storage-20260517 | **是**（BlobStore + MinioBlobStore） | 不合理 | grandfather + 高优先 backfill |
| auth-scaffold-20260517 | **是**（users 表 + JWT + 4 路由） | 不合理 | grandfather + 高优先 backfill |
| repo-api-mvp-20260517 | **是**（Repository CRUD 路由） | 不合理 | grandfather + 高优先 backfill |
| commit-api-mvp-20260517 | **是**（5 路由 commit/blob/tree） | 不合理 | grandfather + 高优先 backfill |
| rq-worker-skeleton-20260517 | **是**（RQ + Redis + worker） | 不合理 | grandfather + 高优先 backfill |
| processor-framework-20260517 | **是**（ProcessorRegistry + Runner + 路由） | 不合理 | grandfather + 高优先 backfill |
| adapter-framework-20260517 | **是**（AdapterRegistry + Runner + 路由） | 不合理 | grandfather + 高优先 backfill |
| llm-gateway-mvp-20260517 | **是**（LLM Gateway + Anthropic/Fake + 缓存） | 不合理 | grandfather + 高优先 backfill |
| adapter-firecrawl-20260517 | **是**（FirecrawlURLAdapter） | 不合理 | grandfather + 高优先 backfill |
| llm-qa-gen-20260518 | **是**（LLMQAGenProcessor） | 不合理 | grandfather + 高优先 backfill |
| web-mvp-pages-20260517 | **是**（Vite + React + 三页） | 不合理 | grandfather + 高优先 backfill |
| web-write-flows-20260517 | **是**（Web 写流程 UI） | 不合理 | grandfather + 高优先 backfill |
| repo-files-tab-20260517 | **是**（Repo Files Tab + Ref API） | 不合理 | grandfather + 高优先 backfill |
| sdk-cli-mvp-20260518 | **是**（Python SDK + CLI） | 不合理 | grandfather + 高优先 backfill |
| pipeline-orchestrator-mvp-20260518 | **是**（DB schema + 路由 + worker job） | 不合理 | grandfather + **最高优先** backfill（毕竟是本 change 的实证起源） |

**结论**：豁免清单的合理性 = 2/19，**不合理 17/19**。spec 当前将这 17 个"实代码 change"一并 grandfather 豁免在 AC 语义上是退让；建议**保留**实操选择但在 SKILL 豁免段**显式分类**（2 个真"纯 harness"豁免 + 17 个"实代码但因历史原因暂豁免，必须 backfill"）。本 reviewer 在 MUST FIX-2 已强制要求该分类。

## Verdict

**REVISION REQUIRED**

理由：
- **MUST FIX-1（awk 表达式语义错误）** 是阻塞性硬伤——一旦实施，整个新规约的机械化基石失效；从字面 PASS 倒回到与 harness-reviewer-agent-separation 治理前同型的 "SKILL 写了但没真守门" 状态，反而把本 change 自己设计的反 grep 假象的初衷打脸。
- **MUST FIX-2（豁免清单计数 + 实代码 vs 纯 harness 拆分缺失）** 关系到 17 个 dataplat change 在 SKILL 文档里的"诚实标注"——若不修，未来读者会误以为本项目 18-19 个 change 都是"纯 harness"才不需要 behavioral AC。
- 其余 5 个 MUST FIX（数字一致、自递归门禁、豁免标准、fixture 真跑机制、reviewer 字段约束）都是 spec 当前细节不足以支撑 stage 3 编码者把 lint 函数写对。

修完 v2 重提评审；预计修改集中在 spec.md AC-4/AC-5/AC-7/AC-8 + 风险表 + 决策栏 + tasks.md T-4/T-6 描述。

## 复检指引（generator 修 v2 后自查命令）

```bash
cd /data/home/zhhdzhang/nta/nta-lake

# MUST FIX-1: 用修正后的 awk 表达式跑全部 closed spec，期望每个返回 >5 行
for f in .harness/changes/*/request_analysis/spec.md; do
  [[ "$f" == *_template* ]] && continue
  [[ "$f" == *harness-ac-behavioral-tier* ]] && continue
  n=$(awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' "$f" | wc -l)
  echo "$(basename $(dirname $(dirname "$f"))): $n 行"
done
# 期望：每行 >5（实际 AC 表 + 表头 + 空行）

# MUST FIX-2/3: 豁免清单计数
ls .harness/changes/ | grep -v _template | grep -v harness-ac-behavioral-tier-20260518 | wc -l
# 期望：19；spec 全部"18"字样替换为"19"

# MUST FIX-4: development-process.md stage 9 文案与 self-attest 模板
grep -A 40 "## 阶段 9" .harness/rules/development-process.md | grep -qE "verdict.*PASS" && grep -A 40 "## 阶段 9" .harness/rules/development-process.md | grep -qE "self-attest" && echo PASS
# 期望：PASS

# MUST FIX-5: 豁免判定标准 / reviewer 复核
grep -q "ac_kind_lint: exempt" .harness/skills/request-analysis/SKILL.md && grep -q "豁免判定" .harness/skills/request-analysis/SKILL.md && echo PASS
# 期望：PASS

# MUST FIX-6: AC_KIND_LINT_SCAN_DIR / OVERRIDE 入口（编码后才能验，spec 阶段只验文字）
grep -qE "AC_KIND_LINT_SCAN_DIR|AC_KIND_LINT_EXEMPT_OVERRIDE" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md
# spec 阶段期望：1（AC-4 描述中提及）

# MUST FIX-7: AC kind 列表头校验
grep -q "kind 列表头\|kind 列存在" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md
# 期望：1（spec 风险表新增一行 + AC-4 验证扩展）

# 跨 AC 自审 #6: 反向 grep + test -f
grep -nE "! *grep" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md
# 命中处期望每行邻近都有 test -f 前置

# 跨 AC 自审 #9: summary.md 占位符残留
grep -cE "<feature-slug>|<YYYY-MM-DDTHH:MM:SSZ>|<复述|<bullet list>" .harness/changes/harness-ac-behavioral-tier-20260518/summary.md
# 期望：0
```

复检 v2 spec 重提评审时，请同步开 `spec_review_v2.md`（不要覆盖本 v1 文件）。
