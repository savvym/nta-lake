---
change_id: harness-ac-behavioral-tier-20260518
version: 3
authored_at: 2026-05-18T09:30:00Z
status: draft
prior_version: 2
prior_review: request_analysis/review/spec_review_v2.md
---

# Spec：AC 分层规约 + stage 9 强制门禁 + behavioral AC lint

> **v3 修订说明**：闭 stage 2 spec_review_v2.md 的 2 MUST FIX + 5 SHOULD FIX。

## v2 review 闭环表

| # | 类别 | 位置 | v2 问题 | v3 状态 |
|---|---|---|---|---|
| MUST #1 | summary.md SSoT 不同步 | summary.md L57 | 仍写"18 个" | **CLOSED**：summary.md 改"19 个 closed change... 分两类（2 永久豁免 + 17 暂豁免）" |
| MUST #2 | 双条件 (ii) `grep -q behavioral` 语义破损 | AC-4/AC-6/T-4/T-6 | 裸 grep 被 AC 描述里 "behavioral" 字串误命中（本 spec 实测 8 次假命中 vs 真 2 行）→ lint 机械化保护失效，本 change 核心命题失守 | **CLOSED**：(ii) 改锚定 AC 行 kind 单元格 regex `^\| AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|`；AC-6 期望同步改；T-4/T-6 description 同步；T-6 fixture-bad 增加最隐蔽反例（全 static kind + 描述含 behavioral 字串） |
| SHOULD #1 | AC-7 缺 test -f | AC-7 | for loop 前缺 `test -f SKILL.md` 前置 | **CLOSED**：加 `test -f` 前置 |
| SHOULD #2 | AC-5 -A 60 偏大 | AC-5 | grep -A 60 把 stage 10 也吞下 | **CLOSED**：改用 awk 状态机抽 stage 9 段 `awk '/^## 阶段 9/{p=1;next} p && /^## 阶段 /{exit} p'` |
| SHOULD #3 | summary.md "18 个" 残留 | summary.md L57 | 同 MUST #1 | CLOSED via MUST #1 |
| SHOULD #4 | v1 闭环表 awk 行数描述不准确 | spec L17 | 单一样本 37 | **CLOSED**：改"最少 13 行（repo-api-mvp）/ 最大 102 行（commit-api-mvp）/ 19 spec 全覆盖 AC 表段" |
| SHOULD #5 | AC-6 内 `grep -c behavioral` 同型缺陷 | AC-6 | 继承 MUST #2 同型 | **CLOSED via MUST #2** |
| NICE #1 | 19 ID 硬编码未来失效 | T-1b | 第 20 change 后失效 | **CLOSED**：T-1b 注释明示本 change 自身**不豁免**（dogfood，自带 ≥2 behavioral AC）；未来新 change 也不豁免；硬编码仅 19 历史 ID |
| NICE #2 | 引用段路径片段相对 | 引用段 | — | 接受 NICE，不修 |

## v1 review 闭环表

| # | 类别 | 位置 | v1 问题 | v2 状态 | 证据 |
|---|---|---|---|---|---|
| MUST #1 | awk 表达式错误 | AC-4 + 风险表 | `awk '/## 验收标准/,/^## /'` range 操作符在起始模式行就关闭，对所有正常 spec 返回 1 行 | **CLOSED** | 改为状态机：`awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p'`；v2 reviewer 本机对 19 个 closed spec 逐个 dry-run：最少 13 行（repo-api-mvp）/ 最大 102 行（commit-api-mvp）/ 全部覆盖 AC 表段无假阳性 |
| MUST #2 | 豁免清单计数错 | 多处 | 写"18 个"实为 **19 个** closed change；17 个含 dataplat 实代码却被一并豁免 | **CLOSED** | 全文 18→19；豁免名单显式分两类：**永久 2 个** 纯 harness + **暂豁免 17 个** 实代码（必须 backfill）；follow-up `harness-ac-kind-backfill-*` 标 P1 |
| MUST #3 | AC-7 grep pattern 不可命中 | AC-7 | 三 ID 单行 grep 假设 SKILL 把 ID 顺序写一行，实跑 NOT MATCH | **CLOSED** | 改 for loop 逐 ID grep；豁免段最低行数断言 ≥ 19 |
| MUST #4 | self-attest vs deferred 语义未闭合 | AC-5 | 文案没说 self-attest 与 deferred 区别 + 缺必填字段 | **CLOSED** | AC-5 验证扩展到 4 checkpoint：(i) 默认 verdict=PASS；(ii) self-attest 替代路径 + 4 必填字段（理由 / 本机证据列表 / 跑过命令 / 时间）；(iii) 禁止纯 deferred；(iv) SKILL 引用 |
| MUST #5 | 豁免判定标准缺失 + reviewer 复核机制缺 | AC-2 + 风险表第 3 行 | 自声明 `ac_kind_lint: exempt` 滥用面大；reviewer 看不看不知道 | **CLOSED** | AC-2/AC-3 扩展：(a) SKILL 加"豁免判定标准"（代码改动量化阈值）；(b) `expert-reviewer/SKILL.md` 加"若 spec 声明 `ac_kind_lint: exempt` → reviewer 必跑 `git diff --stat origin/main..HEAD` 验证改动符合标准，附结果到 review"；(c) 风险表新增"豁免被滥用"+ 缓解 |
| MUST #6 | fixture 真跑机制未具象 | AC-4 | `run_ac_kind_lint` 无 SCAN_DIR/EXEMPT 入口；fail-fast 让 fixture 撞墙 | **CLOSED** | AC-4 验证扩展：(a) 加 `AC_KIND_LINT_SCAN_DIR` + `AC_KIND_LINT_EXEMPT_OVERRIDE` 两个 env 注入入口；(b) fixture 在 `run_harness_ac_behavioral_tier()` 内部用 subshell 隔离两次跑（PASS / FAIL）+ trap cleanup；(c) 拆出 `scripts/lint/test_ac_kind_lint_fixture.sh`（SHOULD #1 修） |
| MUST #7 | reviewer 字段约束缺机械化 | 风险表 | 仅靠 SKILL 文档约束 reviewer 必查 = 重蹈 harness-reviewer-agent-separation 治理前同型 | **CLOSED** | AC-4 lint 函数**双条件断言**：(i) AC 表头含 `kind` 列字面、(ii) AC 表段至少 1 行含 `behavioral`，二者缺一 FAIL；风险表新增对应条目 |
| SHOULD #1 | AC-4 描述过长违反"一行式" | AC-4 | fixture 步骤塞在 AC-4 描述里 | **CLOSED** | AC-4 验证命令拆出 `scripts/lint/test_ac_kind_lint_fixture.sh`，AC-4 验证只剩一行 `bash scripts/lint/test_ac_kind_lint_fixture.sh` |
| SHOULD #2 | AC-5 grep 缺 test -f | AC-5 | 反 SKILL §6 模式 | **CLOSED** | AC-5 改写为 `test -f ... && grep ...` 链 |
| SHOULD #3 | AC-7 单行 grep 不可命中 | AC-7 | 同 MUST #3 子项 | **CLOSED via MUST #3** |
| SHOULD #4 | 混合型 AC 拆分指引无示例 | 决策栏 | 只说"拆为两条"，没示例 | **CLOSED** | 决策栏附伪代码示例：原"AC-N: 路由存在 + POST → 200" 拆为 AC-Na (static, grep router) + AC-Nb (behavioral, ASGITransport POST → assert 200) |
| SHOULD #5 | AC-8 期望 self_check 总数易脆 | AC-8 | 写"`PASS: 238 + 8 + 1`"撞动态 | **CLOSED** | AC-8 改为"退码 0 + 本 change block 8/8 PASS" |
| SHOULD #6 | behavioral 三层判定 | 决策栏 | 决策"ASGITransport 算 behavioral" 没在 SKILL 判定指引落地 | **CLOSED** | T-1a 描述明确含 behavioral 三层：(L1) 真起服务 curl smoke / (L2) ASGITransport in-process / (L3) load_recipe pydantic parse；纯 grep/test -f/dry-import 全 static |
| NICE #1 | 引用段缺 CLAUDE.md 章节定位 | 引用段 | — | CLOSED | 见 v2 引用段，已写"落 skills + scripts，不动 rules/coding-style" |
| NICE #2 | 决策栏混合 AC 示例 | 决策栏 | — | CLOSED via SHOULD #4 | — |
| NICE #3 | tasks DAG T-3 注释 | tasks.md | — | tasks v2 处理 | — |

## 背景

`.harness/` 范式自 `harness-bootstrap-20260516` 起累积了 **19 个** closed change。在 `harness-reviewer-agent-separation-20260518`（meta-change #1）中已经把"评审者独立性"机械化为 `run_reviewer_lint` 硬守门。本次 meta-change #2 解决另一个 evaluator-quality 漏洞：**"验收标准（AC）真实跑通性"**。

`scripts/_self_check.sh` 是 harness 的最终质检关。**它认定 PASS 的依据**应该是"这个 change 的行为正确"，但实际上历史 AC 大量使用 `grep`、`test -f`、`uv run python -c "import X"` 类静态检查——这些 PASS 不能证明业务路径真跑得通，只能证明源码骨架存在。

落 skills（SKILL.md 加段）+ scripts（self_check lint），不动 rules/coding-style；development-process.md 只在 stage 9 段加门禁文案（不重写 SOP）。

## 问题陈述

`pipeline-orchestrator-mvp-20260518` stage 9 是项目史上**第一次**真正部署起来跑端到端 demo（POST /pipelines/runs:from-yaml → worker 跑 → Bronze→Silver→Gold 全链路），结果一次跑就抓到 3 个真 bug：

1. **`demo-bronze-to-gold.yaml` 字段名误用**（`model` 应为 `model_id`、`samples_per_doc` 应为 `records_per_doc`）。AC-11 验证是 `grep "llm-qa-gen" recipes/examples/demo-bronze-to-gold.yaml`——文件存在 + 关键字命中即 PASS，但 yaml 内容是否能被 `LLMQAGenSpec` 接受根本没验证。**Spec stage 6 review PASS、self_check 11/13 PASS 时，这个 demo 实际跑不通**。
2. **`test_cache_hit_*` fixture 撞 hash**：测试 `_seed_bronze` 用 hardcoded `b"x\n"` 创建 commit，跟 stage 9 demo 同 byte content 产生相同 sha256 commit hash → unique constraint violation。
3. **`pipeline_cache.output_commit_hash` FK 缺 `ON DELETE CASCADE`**：删 repo 时触发 FK violation 500。pipeline 主路径没触发，AC 没覆盖。

更系统的问题：**self_check 226/226 PASS 是 grep 假象**。如果不在 harness 层引入"AC 必须至少有一条真行为"的硬约束，未来每个 change 都会带着这种漏洞 close，stage 9 这种昂贵的真跑验证只能靠 Owner 自觉触发。

## 范围

In scope：

- **AC-1**：`.harness/skills/request-analysis/SKILL.md` 加 §"AC 分层规约"，定义 `kind: static | behavioral` 二分；要求 spec.md AC 表新增 `kind` 列。
- **AC-2**：每个非豁免 change **至少 1 条 `kind: behavioral` AC**；豁免判定标准定义在 SKILL（git diff 量化阈值 + 自声明 `ac_kind_lint: exempt` 格式），违反者 stage 2 reviewer 必拒。
- **AC-3**：`.harness/skills/expert-reviewer/SKILL.md` 加段 stage 2 reviewer 必查项：(i) AC 表是否有 `kind` 列；(ii) 至少 1 条 behavioral；(iii) 若 spec 声明 `ac_kind_lint: exempt`，reviewer 必跑 `git diff --stat` 验证改动只在 `.harness/*` / `wiki/*` / `scripts/*` / `*.md` 范围内，附结果到 review。
- **AC-4**：`scripts/_self_check.sh` 加 `run_ac_kind_lint` global function：
  - 默认 scan `.harness/changes/<id>/`，可由 env `AC_KIND_LINT_SCAN_DIR` 覆盖（fixture 注入）。
  - 默认豁免清单硬编码（19 个历史 + `_template`），可由 env `AC_KIND_LINT_EXEMPT_OVERRIDE` 覆盖（fixture 注入，逗号分隔 change_id）。
  - 对未豁免 change 的 `spec.md`：
    - 用 awk 状态机抽 AC 表段：`awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md`。
    - **双条件断言**（v3 修：(ii) 改为锚定 AC 表行的 kind 单元格 regex，避免被 AC 描述里"behavioral"字串误命中）：
      - (i) 抽出的段含 `| kind ` 列表头：`grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|' <段>`
      - (ii) 段内至少 1 行 AC 的 kind 单元格真值为 `behavioral`：`grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|' <段>`
    - 任一不满足 → 输出 change_id + 失败原因 → 整个 lint FAIL。
  - 用单个 run_ac 计数（对外 1 个 global AC，与 reviewer-lint 同模式）。
  - 在 main 末尾（reviewer-lint 之后）调用。
- **AC-5**：`.harness/rules/development-process.md` stage 9 段加硬约束文案（4 个 checkpoint）：
  - (i) 默认：有部署面的 change 必须 `verdict: PASS`。
  - (ii) 替代路径：允许 `self-attest (理由)`，必填 4 字段：`理由` / `本机证据列表`（命令输出路径或粘贴）/ `跑过的命令` / `时间`。
  - (iii) **禁止纯 deferred**（无 self-attest 或证据空）。
  - (iv) 引用本 SKILL "AC 分层规约" 段。
  - 附 self-attest 模板片段。
- **AC-6**：self_check main 含 `run_ac_kind_lint` 调用；本变更 spec.md 含 `kind` 列且至少 1 条 behavioral（即本表 AC-4 + AC-8）。
- **AC-7**：SKILL.md 豁免清单**显式分两类**：
  - **永久豁免（2 个，"纯 harness/纯文档"）**：`harness-bootstrap-20260516`、`harness-reviewer-agent-separation-20260518`。
  - **暂豁免 grandfather（17 个，实代码 change，仅因历史原因暂豁免，必须 backfill）**：`bootstrap-monorepo-20260516`、`core-domain-model-20260516`、`cas-storage-20260517`、`auth-scaffold-20260517`、`repo-api-mvp-20260517`、`commit-api-mvp-20260517`、`rq-worker-skeleton-20260517`、`processor-framework-20260517`、`adapter-framework-20260517`、`llm-gateway-mvp-20260517`、`adapter-firecrawl-20260517`、`llm-qa-gen-20260518`、`web-mvp-pages-20260517`、`web-write-flows-20260517`、`repo-files-tab-20260517`、`sdk-cli-mvp-20260518`、`pipeline-orchestrator-mvp-20260518`。
  - 后续 follow-up `harness-ac-kind-backfill-*` 标 **P1**（下个非紧急 sprint），不允许无限 deferred。
- **AC-8**：全仓 `bash scripts/_self_check.sh` 跑通（带正确 env），本变更 block 8/8 PASS、global `run_ac_kind_lint` PASS、退码 0；不强约束总 PASS 数（因为新加 lint 改变基线）。

## 非范围

- **不**回填 19 个历史 closed change 的 AC `kind` 字段。grandfather 期：17 个实代码 change + 2 个纯 harness change 全部入豁免清单。回填工作放 follow-up `harness-ac-kind-backfill-*`（P1）。
- **不**做 AC behavioral 测试的覆盖率指标（"每条 AC ≥1 测试"）。现有 SKILL `§ 跨 AC 一致性自审清单 #4` 已要求"风险缓解 ↔ AC 测试列表"，覆盖度问题归那里。
- **不**修 test-fixture-isolation / pipeline-cache-fk-cascade（治标 bug），它们在 change #2 单独处理；本 meta-change 只治本。
- **不**做 spec.md 的 schema 校验（如 yaml-frontmatter validator）；用 grep 即可，schema 化放 follow-up `harness-spec-schema-validator-*`。
- **不**改 stage 8 CI deferred 现状——是项目级别问题（git remote 未配置）；但本 change 自身 P-ci status 从 `deferred` 改 `self-attest` + 必填字段，以 dogfood 新规约。
- ~~**不**改 `_template/request_analysis/spec.md` 表头自动加 kind 列~~（v1 决策；**v2 翻转**：让 _template 加 `kind` 列利于扩散，T-5 转为"加列"任务）。

## 验收标准

**AC kind 分层（本 spec 自身已应用新规约）**：static = grep / test -f / dry-import；behavioral = HTTP roundtrip / pytest 集成 / load_recipe pydantic parse / bash fixture 真跑断言。

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | SKILL.md 新增 §"AC 分层规约" 段（含 kind 定义 + 判定指引含 behavioral 三层 + 豁免判定标准） | `test -f .harness/skills/request-analysis/SKILL.md && grep -q "AC 分层规约" .harness/skills/request-analysis/SKILL.md && grep -q "kind: behavioral" .harness/skills/request-analysis/SKILL.md && grep -q "豁免判定" .harness/skills/request-analysis/SKILL.md` | 全 grep 命中 |
| AC-2 | static | SKILL.md 同段含"每个非豁免 change 至少 1 条 behavioral AC"硬约束 + `ac_kind_lint: exempt` 自声明格式 | `test -f .harness/skills/request-analysis/SKILL.md && grep -qE "至少.*1 ?条.*behavioral" .harness/skills/request-analysis/SKILL.md && grep -q "ac_kind_lint: exempt" .harness/skills/request-analysis/SKILL.md` | grep 命中 |
| AC-3 | static | `expert-reviewer/SKILL.md` 加段 stage 2 必查 3 项：(i) AC 表 kind 列存在；(ii) 至少 1 条 behavioral；(iii) 若 `ac_kind_lint: exempt` 必跑 git diff 复核 | `test -f .harness/skills/expert-reviewer/SKILL.md && grep -q "至少 1 条 behavioral" .harness/skills/expert-reviewer/SKILL.md && grep -qE "git diff.*ac_kind_lint" .harness/skills/expert-reviewer/SKILL.md` | grep 命中 |
| AC-4 | **behavioral** | `scripts/_self_check.sh` 加 `run_ac_kind_lint`（含 `AC_KIND_LINT_SCAN_DIR` / `AC_KIND_LINT_EXEMPT_OVERRIDE` env 入口 + **双条件断言**：(i) kind 列表头存在；(ii) 锚定 AC 行 kind 单元格 regex `^\| AC-N \| behavioral \|`，**不被 AC 描述里出现的 "behavioral" 字串误命中**）；fixture 真跑用 `scripts/lint/test_ac_kind_lint_fixture.sh` 验证 3 个场景：合规 PASS / 缺 kind 列 FAIL / **kind 全 static 但描述含 behavioral 字串**（最隐蔽反例）FAIL | `test -f scripts/lint/test_ac_kind_lint_fixture.sh && bash scripts/lint/test_ac_kind_lint_fixture.sh` | 退码 0；fixture 内部构造 3 种临时 spec 分别跑 lint，期望 PASS / FAIL / FAIL，全部断言成功 |
| AC-5 | static | `.harness/rules/development-process.md` stage 9 段含 4 checkpoint：(i) verdict=PASS 默认；(ii) self-attest 替代 + 4 必填字段；(iii) 禁止纯 deferred；(iv) SKILL 引用 + self-attest 模板片段 | `test -f .harness/rules/development-process.md && S9=$(awk '/^## 阶段 9/{p=1;next} p && /^## 阶段 /{exit} p' .harness/rules/development-process.md) && echo "$S9" \| grep -qE "verdict.*PASS" && echo "$S9" \| grep -q "self-attest" && echo "$S9" \| grep -q "禁止.*deferred" && echo "$S9" \| grep -qE "必填.*字段\|理由.*证据.*命令.*时间"` | 4 个 grep 全命中（awk 状态机抽 stage 9 段，不再 -A 60 硬编码） |
| AC-6 | static | self_check main 含 `run_ac_kind_lint` 调用；本变更 spec.md 含 `kind` 列且**至少 2 条 AC 的 kind 单元格真为 behavioral**（用 AC 行 regex 锚定，不被字串误命中）；`_template` spec.md 示例 AC 表也含 `kind` 列 | `test -f scripts/_self_check.sh && grep -q "run_ac_kind_lint" scripts/_self_check.sh && SPEC=.harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md && test -f "$SPEC" && SEG=$(awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' "$SPEC") && echo "$SEG" \| grep -qE '^\\\|[^\|]*\\\|[[:space:]]*kind[[:space:]]*\\\|' && [ "$(echo "$SEG" \| grep -cE '^\\\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\\\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\\\|')" -ge 2 ] && grep -q "kind" .harness/changes/_template/request_analysis/spec.md` | 全 grep 命中；本 spec 的 AC 行 behavioral 计数 ≥ 2（AC-4 + AC-8） |
| AC-7 | static | SKILL.md 豁免清单分两类（永久 2 个 + 暂豁免 17 个），且 19 个 change ID 全部命中 | `test -f .harness/skills/request-analysis/SKILL.md && for cid in harness-bootstrap-20260516 harness-reviewer-agent-separation-20260518 bootstrap-monorepo-20260516 core-domain-model-20260516 cas-storage-20260517 auth-scaffold-20260517 repo-api-mvp-20260517 commit-api-mvp-20260517 rq-worker-skeleton-20260517 processor-framework-20260517 adapter-framework-20260517 llm-gateway-mvp-20260517 adapter-firecrawl-20260517 llm-qa-gen-20260518 web-mvp-pages-20260517 web-write-flows-20260517 repo-files-tab-20260517 sdk-cli-mvp-20260518 pipeline-orchestrator-mvp-20260518; do grep -q "$cid" .harness/skills/request-analysis/SKILL.md \|\| exit 1; done && grep -q "永久豁免" .harness/skills/request-analysis/SKILL.md && grep -q "暂豁免" .harness/skills/request-analysis/SKILL.md` | test -f 前置 + for loop 全 PASS + 分类字面命中 |
| AC-8 | **behavioral** | 全仓 `bash scripts/_self_check.sh`（带正确 env）退码 0；本 change block 8/8 PASS；global `run_ac_kind_lint` PASS | `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh; echo "EXIT=$?"` 后 grep 输出确认 `=== harness-ac-behavioral-tier-20260518` block 内 8 条 AC 全 PASS + `reviewer-lint` 与 `ac_kind_lint` 两个 global PASS | 退码 0；block 8/8 PASS；2 个 global lint PASS |

**Behavioral AC 数：2（AC-4 / AC-8）**，满足 "≥1 条 behavioral" 自约束（dogfood）。

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| **19 个 closed change 全要回填 `kind` 列，工作量大** | 高 | 高 | grandfather 豁免名单分两类（2 永久 + 17 暂豁免）；follow-up `harness-ac-kind-backfill-*` 标 P1（下个非紧急 sprint）；本 change 只对新 change 强制 |
| **awk 抽段误判**（kind 在评论而非 AC 表里） | 中 | 中 | 用状态机抽段（`awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p'`）锁定 AC 表段范围，不全文 grep；本机 dry-run 已验证（pipeline-orchestrator/spec.md 抽出 37 行含 AC 表）；reviewer 复核 |
| **新规约导致小型 PR 流程过重** | 中 | 低 | 文档/纯 harness change 可显式 `ac_kind_lint: exempt` 自豁免；只需在 spec.md frontmatter 加一行；豁免判定标准量化（代码改动只在 `.harness/*` / `wiki/*` / `scripts/*` / `*.md`） |
| **`kind: behavioral` 的判定主观** | 中 | 中 | SKILL.md 加 behavioral 三层判定指引（L1 真起服务 curl smoke / L2 ASGITransport in-process / L3 load_recipe pydantic parse）；纯 grep / test -f / dry-import 全 static；混合型必须拆为两条独立 AC（决策栏附伪代码示例） |
| **`run_ac_kind_lint` 自身漏过本 change（自递归）** | 低 | 高 | AC-8 强制全仓 self_check 通过；本 change spec.md 自身就是 lint 的第一个真用例（AC-4 + AC-8 两条 behavioral） |
| **`ac_kind_lint: exempt` 自声明被滥用** | 中 | 中 | `expert-reviewer/SKILL.md` 加 stage 2 必查：若 spec 声明 exempt，reviewer 必跑 `git diff --stat` 验证改动只在豁免范围内，附结果到 review（AC-3） |
| **reviewer 字段约束仅靠 SKILL 文档约束 = 重蹈 harness-reviewer-agent-separation 治理前同型** | 中 | 高 | `run_ac_kind_lint` **双条件断言（v3 加固）**：(i) AC 表头含 `kind` 列字面、(ii) **AC 行 kind 单元格 regex** `^\| AC-N \| behavioral \|` 真值至少 1 行——**不接受裸字串 `grep -q behavioral`**（会被 AC 描述里"behavioral 三层"等字串误命中，机械化保护失效）；二者缺一 FAIL；fixture 第 3 种场景（kind 全 static + 描述含 behavioral 字串）专项打靶 |

## 受影响模块

- `.harness/skills/request-analysis/SKILL.md`（加 AC 分层规约段 + 豁免名单分两类 + behavioral 三层判定）
- `.harness/skills/expert-reviewer/SKILL.md`（加 stage 2 reviewer 必查 3 项 + `ac_kind_lint: exempt` 复核机制）
- `.harness/rules/development-process.md`（stage 9 强制门禁文案 4 checkpoint + self-attest 模板）
- `scripts/_self_check.sh`（加 `run_ac_kind_lint` global function + main 末尾调用 + 本 change block `run_harness_ac_behavioral_tier`）
- `scripts/lint/test_ac_kind_lint_fixture.sh`（**新增**，AC-4 fixture 真跑用）
- `.harness/changes/_template/request_analysis/spec.md`（示例 AC 表加 `kind` 列）

## 不受影响但易混淆的模块

- `.harness/agents/reviewer-agent.md`：不动 reviewer agent 的角色定义；只在 SKILL 层加规约。
- `.harness/skills/deploy-verify/SKILL.md`：不重写 stage 9 SOP，只在 `development-process.md` 加门禁文案。
- 19 个历史 closed change 的 spec.md：全部豁免（分两类），不动它们的内容。
- `.harness/rules/coding-style.md` / `engineering-structure.md`：不动。

## 关键决策

| 时间 | 决策 | 理由 / 取舍 |
|---|---|---|
| 2026-05-18 | 不强制覆盖历史 change，新 change 起强制 lint；19 个历史中 2 个真纯 harness 永久豁免、17 个实代码暂豁免（P1 backfill） | 全量回填工作量超本 change 承载；显式分类让 SKILL 不至于误导未来读者本项目"19 个都是纯 harness" |
| 2026-05-18 | AC `kind` 字段从 `static` / `behavioral` 二分，不引入 `mixed` 第三类 | 二分简单可机械化；混合型 AC 应拆为两条独立 AC（例见下方拆分示例） |
| 2026-05-18 | behavioral AC 三层判定：(L1) 真起服务 curl smoke / (L2) ASGITransport in-process roundtrip / (L3) load_recipe pydantic parse 真跑——全算 behavioral | 现有 apps/api/tests 大量用 ASGITransport，已是事实标准；不破坏既有测试设计；纯 grep/test -f/dry-import 全 static |
| 2026-05-18 | 不用 yaml-schema 校验，用 grep 规则 | spec.md AC 表用 markdown 写不是 yaml；grep + awk 抽段足够；schema 化放 follow-up |
| 2026-05-18 | **混合型 AC 拆分示例（伪代码）** | 原"AC-N: POST /repos 返回 201 + 路由文件含 `@router.post(/repos)`"  → 拆为：<br>**AC-Na (static)**：`grep -q "@router.post(/repos)" apps/api/dataplat_api/routers/repos.py`<br>**AC-Nb (behavioral)**：`uv run pytest apps/api/tests/test_repos.py::test_create_201`（用 ASGITransport + JWT cookie + 201 assert） |
| 2026-05-18 | `_template/spec.md` 加 `kind` 列（v1→v2 翻转决策） | 让新 change 复制 _template 时自然带列，扩散更顺；v1 担心冲击旧 review 工具，但实际旧 change 不动 _template 影响 |
| 2026-05-18 | `run_ac_kind_lint` 用 fail-fast `exit 1`（与 `run_reviewer_lint` 同模式），但提供 env override 让 fixture 在 subshell 中安全跑 | 一致性优先；fixture 隔离用 subshell 包裹 `(AC_KIND_LINT_SCAN_DIR=... run_ac_kind_lint; echo $?)` 防止污染主进程退码 |

## 待澄清问题

无（v2 已澄清；评审若有问题在 v3 解决）。

## 引用

- `.harness/changes/pipeline-orchestrator-mvp-20260518/deployment/deploy_verify_v1.md` § "需要 follow-up" — 3 个 follow-up 是本 change 的直接证据
- `.harness/changes/harness-reviewer-agent-separation-20260518/` — 同型 meta-change（评判者独立性），同型机械化模式（global `run_*_lint` 函数 + 双条件断言）
- `.harness/skills/request-analysis/SKILL.md` § "跨 AC 一致性自审清单" — 本 change 的 AC 分层规约附在该清单之后
- `.harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/review/spec_review_v1.md` — v1 评审报告（本 v2 闭环来源）
- CLAUDE.md 硬约束 #5：发现 Agent / 流程缺陷，把防复发机制补回 `.harness/`（本 change 落 skills + scripts，不动 rules/coding-style）
