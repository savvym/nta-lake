---
change_id: harness-remote-push-onboarding-20260518
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:harness-remote-push-onboarding-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T23:55:00Z
verdict: REVISION REQUIRED
must_fix_count: 1
should_fix_count: 2
nice_to_have_count: 1
---

# Spec Review v1

> 评审者声明：本 reviewer 是独立 sub-agent（claude-sonnet-4-6），未参与本 change spec/tasks 撰写。完整读了 reviewer-agent.md / expert-reviewer SKILL / request-analysis SKILL / development-process.md / summary.md / spec.md / tasks.md，并实读了 bootstrap-monorepo-20260516 spec.md AC-15、scripts/_self_check.sh L79-140（bootstrap-monorepo block）/ L1214-1311（ac_kind_lint）/ L1580-1598（汇总 summary 输出）/ L1424-1455（reviewer-lint）。所有 grep/bash 命令均在本机实跑验证。本次模型：**sonnet**（claude-sonnet-4-6），符合 reviewer-agent.md §8 默认规约。

---

## stage 2 AC kind 必查 3 项

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | AC 表存在 `kind` 列 | PASS | spec.md L67 表头 `\| ID \| kind \| 描述 \| 验证方式 \| 期望 \|`；`awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md \| grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|'` 命中 |
| 2 | 至少 1 行 AC kind 单元格真值 `behavioral`（锚定 AC 行 regex） | PASS | AC-8 `**behavioral**` 1 行；锚定 regex `^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|` 命中 |
| 3 | frontmatter 是否声明 `ac_kind_lint: exempt` | N/A | spec.md frontmatter L1-6 无 `ac_kind_lint: exempt`，无需 git diff 校验 |

三项全 PASS，AC 分层规约硬约束**未违反**。

---

## 检查清单结论（expert-reviewer SKILL §1 plan 模式）

### spec.md

- [x] 背景写明了为什么现在做（repo-files-tab-v2 关闭后 origin 加入，harness "无 remote" 假设需清算）
- [x] 问题陈述对外部读者可理解（6 条具体问题：SKILL 措辞过时 / stage 7 缺 push 步骤 / stage 8 self-attest 理由失效 / ci.yml 存在但政策拒绝 / self_check AC-15 需删 / .gitignore 漏 .claude/）
- [x] 范围 / 非范围都有（8 条 AC in-scope + 6 项明确 out-of-scope）
- [~] 每条验收标准可演示且可机械化——**AC-8 验证命令 `tail -3 | grep -q "FAIL: 0"` 有实质 bug**（详 MUST FIX-1）；AC-1..AC-7 机械化验证写法正确
- [x] 风险有缓解或显式 accept（5 条风险，含 ci.yml grep 漏 / bootstrap AC 数变化 / .claude/ 副作用，各有缓解）
- [x] 没有把已有架构当新提案（引用已有 SKILL L289 / L172 / self_check L132-133）

### tasks.md

- [x] 每个任务粒度合理（1-3 小时；T-1~T-7 实现 + T-8 验证）
- [x] depends_on 形成 DAG 无环（T-1..T-7 全并行 → T-8；手动 trace 确认无环，终点 T-8）
- [x] 评审 / 单测 / CI / 部署 process_tasks 都存在（P-spec-review/P-code-review/P-test-review/P-push/P-ci/P-deploy/P-user-confirm，含 stage-2/4/6/7/8/9/10；`grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md` = 6）
- [x] 无"实现整个系统"类目标性任务

---

## 跨 AC 一致性自审 9 条（reviewer 复核）

| # | checklist 条目 | 结果 | 备注 |
|---|---|---|---|
| 1 | schema 字段 ↔ hash ↔ idempotency ↔ fixture 四链路一致 | N/A | 无 hash/idempotency 链路（纯 harness 文档 + 配置修改） |
| 2 | 事务边界声明三处一字不差 | N/A | 无事务边界 |
| 3 | AC 验证命令一行式可执行 | FAIL | AC-8 `tail -3 \| grep -q "FAIL: 0"` 在 SKIP > 0 时假 FAIL（详 MUST FIX-1） |
| 4 | 风险缓解 ↔ AC 测试列表 | OK | 5 条风险各有缓解说明；风险 #2（bootstrap AC 数变化）与 T-7 + spec 背景说明对应 |
| 5 | commit 历史链连续性 | N/A | 无写 commit 路径 |
| 6 | 反向 grep 配 `test -f` 前置 + 不吞 stderr | OK | AC-1/AC-2/AC-7 反向 grep 的目标文件均永久存在（SKILL.md / self_check.sh）；AC-6 `test ! -f` 写法本身是 test 而非反向 grep，正确；无 `2>/dev/null` 吞 stderr |
| 7 | process_tasks 6 条必填 | PASS | `grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md` = 6；含 stage-8 self-attest 额外一项 |
| 8 | AC 验证命令 dry-parse | FAIL | AC-8 `tail -3 \| grep -q "FAIL: 0"` 语法合法但 semantic 假阴性（见 MUST FIX-1）；其他 AC 验证命令（awk/grep/test）语法正确 |
| 9 | summary.md frontmatter 无模板占位符 | PASS | `grep -cE "<feature-slug>\|<YYYY-MM-DDTHH:MM:SSZ>\|<复述\|<bullet list>" summary.md` = 0；frontmatter 全填实值 |

---

## 必查 1：AC 验证命令 grep/awk 陷阱（全部实跑验证）

### AC-3 / AC-4：markdown 表格 `\|` 转义语义

**结论：不是 bug**。spec.md 是 markdown 文件，表格单元格内需将 `|` 写为 `\|` 以避免被解析为表格分隔符。`scripts/_self_check.sh` 将 AC 验证命令写入 bash -c 时，这些 `\|` 直接渲染为 `|`（shell pipe）。实跑：

```bash
awk '/^## 阶段 7/{p=1;next} p && /^## 阶段 /{exit} p' .harness/rules/development-process.md | grep -q "git push origin main"
# 当前输出：exit 1（预期：文件改前不含该字符串）
```

`awk ... | grep` 管道形式语义正确；`\|` 在 markdown 表格内是合法写法。

### AC-8：`tail -3 | grep -q "FAIL: 0"` 当 SKIP > 0 时假阴性（**MUST FIX**）

`scripts/_self_check.sh` 汇总输出结构（实读 L1589-1598）：

```
=== 汇总 ===
PASS: X
FAIL: 0
SKIP: Y       <- 条件行，SKIP > 0 时出现
跳过: ...     <- SKIP > 0 时追加此行
全部通过（FAIL=0；SKIP 不阻塞）。  <- 始终是最后一行（exit 0 时）
```

当 SKIP > 0（本仓库有 23 个 `run_ac_skipif_no_pg/minio/redis` 调用，开发环境中服务通常未运行），`tail -3` 取到的 3 行为：`跳过: ...` / `全部通过...` / （或 `SKIP: Y` / `跳过: ...` / `全部通过...`），均**不含 "FAIL: 0"** → `grep -q "FAIL: 0"` 返回 exit 1 → 即便全 PASS+SKIP 也被误判为 FAIL。

实跑反例确认：

```bash
printf "PASS: 200\nFAIL: 0\nSKIP: 50\n跳过: some\n全部通过（FAIL=0；SKIP 不阻塞）。\n" \
  | tail -3 | grep -q "FAIL: 0" || echo "FALSE NEGATIVE (confirmed)"
# → FALSE NEGATIVE (confirmed)
```

**修复**：将 `tail -3 | grep -q "FAIL: 0"` 改为 `grep -qE "^FAIL: 0$"` 或检查 exit 码：

```bash
DATAPLAT_PG_PORT=5433 ... bash scripts/_self_check.sh 2>&1 | grep -qE "^FAIL: 0$"
# 等价：直接检查 exit 码
DATAPLAT_PG_PORT=5433 ... bash scripts/_self_check.sh; echo "exit=$?"
```

`grep -qE "^FAIL: 0$"` 锚定行首尾，不受 SKIP 行数影响，不受 "FAIL: 0" 出现在其他位置的干扰。

### AC-1/AC-2：反向 grep 安全性

**结论：OK**。`! grep -q "无 remote 项目" .harness/skills/request-analysis/SKILL.md` 形式：目标文件永久存在（SKILL.md），grep 返回 exit 0（命中）或 exit 1（不命中），不会返回 exit 2（文件不存在）。实跑验证：

```bash
# 当前状态（文件含目标字符串）：
! grep -q "无 remote 项目" .harness/skills/request-analysis/SKILL.md; echo $?  # → 1（反向 FAIL，预期）
# 改完后（字符串删除）：
# → 0（反向 PASS，正确）
```

### AC-7：`.github/workflows/ci.yml` BRE dot metachar

**结论：NICE TO HAVE**（不阻塞）。`grep -q ".github/workflows/ci.yml"` 使用 BRE，`.` 匹配任意字符，理论上可误匹配 `Xgithub/workflows/ci.yml`。但 self_check.sh 中此类字符串不存在，过度匹配无实际影响。若要精确，可改为 `grep -qF ".github/workflows/ci.yml"`（固定字符串）。

### AC-8：behavioral 判定合规性

AC-8 真跑 `bash scripts/_self_check.sh` 全链路（含 bootstrap-monorepo block / reviewer-lint / ac-kind-lint），属于 L3 behavioral（bash fixture 真跑断言），符合 "behavioral 三层" 第三层。判定**合规**（仅验证命令格式需修）。

---

## 必查 2：bootstrap-monorepo AC-15 撤销影响

### 实读 `scripts/_self_check.sh` L79-140（bootstrap block）

```
# Block: bootstrap-monorepo-20260516
# 17 条 AC（详见 .harness/changes/bootstrap-monorepo-20260516/request_analysis/spec.md）
run_bootstrap_monorepo() {
  echo "=== bootstrap-monorepo-20260516 :: 17 AC ==="
  ...
  run_ac AC-15 "ci.yml 合法 + 5 job + concurrency" \
    python3 -c "import yaml; ..."  # L132-133
  ...
```

**关键发现：块头注释已写 "17 条 AC"，echo 也已写 "17 AC"，但当前实际含 18 个 `run_ac` 调用**（含 AC-15；AC-2 拆为 AC-2a/AC-2b 计 2 次）。T-7 删除 AC-15 后实际调用数 = 17，与注释和 echo 一致。因此：

- 块头注释不需要从 "18" 改到 "17"（注释已经是 "17"）
- T-7 description 中 "（如有 '18 AC' 之类需改 '17 AC'）" 是条件语句（"如有"），现状无需修改注释

**结论：T-7 实现只需删 AC-15 行（L132-133），无需改块头注释**。Spec 风险表第 2 条（"bootstrap block AC 总数变化"）已被 reviewer 实读确认处置方式正确。

### ac_kind_lint 影响

bootstrap-monorepo-20260516 在 `_ac_kind_lint_exempt_changes_inline` 豁免清单（L1292），删 AC-15 后不影响 ac_kind_lint 扫描逻辑。reviewer-lint 不扫 bootstrap-monorepo（其 reviewer 值是 `self-attest` 或历史合规值）。

---

## 必查 3：development-process stage 7/8 改动对齐既有句式

### stage 7 当前结构（实读）

```markdown
## 阶段 7 · 代码推送（push）
- **Entry Criteria**：...
- **Skill Injection**：...
- **产出物**：...（commit + push 到远端分支 + summary.md 更新）
- **Quality Gate**：commit message / 不在 main 直接 push
- **Rollback Route**：...
```

T-3 在 §产出物 + §Quality Gate + §Rollback Route 各加一项，格式与既有 bullet 一致，**对齐**。

**SHOULD FIX：T-3 description 重新引入 "无 remote 项目时跳过" 措辞**。tasks.md T-3 description 建议将以下文字加入 development-process stage 7：

> `git push origin main（无 remote 项目时跳过；本仓库 origin = git@github.com:savvym/nta-lake.git）`

此措辞中的 "无 remote 项目时跳过" 与本 change 的核心目标（清算 "无 remote" 假设）语义矛盾——本 change 目的是移除 "无 remote 时降级" 的分支描述，而 T-3 在实现产物（development-process.md）中重新添加了类似措辞。同时括号内的 "本仓库 origin = ..." 是实例信息，不适合写入通用规则文档。AC-3 的验证只检查 "git push origin main" + "up to date with" 关键词，不测试 "无 remote 项目时跳过" 是否存在，故 AC-3 无法守门此问题。

### stage 8 当前结构（实读）

Stage 8 当前无 self-attest 模板或备注段，仅有 Entry Criteria / Skill Injection / 产出物 / Quality Gate / Rollback Route。T-4 将 **新增** 一个说明段。这是新增而非改写，与"改写"措辞有轻微出入，但功能上可接受。

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md AC-8 验证方式（L76）：`tail -3 \| grep -q "FAIL: 0"` | 当 SKIP > 0（本仓库有 23 个 `run_ac_skipif_*` 调用，开发环境服务通常未运行），`tail -3` 取到的末 3 行为 `SKIP: Y` / `跳过: ...` / `全部通过...`，不含 "FAIL: 0"，grep 返回 exit 1 → 即便全 PASS+SKIP 也被误判为 FAIL。实跑反例确认（见上方"必查 1"节）。| 将 `tail -3 \| grep -q "FAIL: 0"` 改为 `grep -qE "^FAIL: 0$"`（全量搜索，锚定行首尾，不受 SKIP 行数影响）。完整修复后命令：`DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh 2>&1 \| grep -qE "^FAIL: 0$"` |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-3 description（"§产出物 加一项"）| T-3 建议在 development-process stage 7 §产出物加入 "`git push origin main（无 remote 项目时跳过；本仓库 origin = git@github.com:savvym/nta-lake.git）`"——其中 "无 remote 项目时跳过" 与本 change 核心目标（清算 "无 remote" 假设）语义矛盾；"本仓库 origin = ..." 是实例信息，不适合写入通用规则文档。AC-3 不守门此点。 | T-3 description 改为在 §产出物加入简洁形式："`git push origin main`（本项目为单作者直 push main；PR 流程作为 future change）"，去掉 "无 remote 项目时跳过" 及仓库地址。 |
| SHOULD FIX-2 | spec.md §验收标准 AC-4（L72 表格行）+ T-4 description（"删 '项目无 remote 长期未决' 措辞"）| AC-4 反向测试 `! awk ... | grep -q "无 remote 长期未决"` ——在 **当前** development-process.md stage 8 中该字符串**已经不存在**（实读 stage 8 全文确认）。实跑：反向 grep 现在已经 PASS（字符串缺席）。AC-4 的反向条件没有错误，但其正向部分（添加 "本项目策略" 等措辞）是真正需要实现的内容，spec 描述略有歧义（"不再含"暗示原有，但原本就没有）。 | 建议 T-4 description 改为清晰表述：stage 8 **新增** 项目策略说明段（而非"删旧改新"），避免 coding 阶段误解任务为"寻找并替换已不存在的字符串"。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | spec.md AC-7 验证方式（L75）：`grep -q ".github/workflows/ci.yml"` 使用 BRE | `.` 在 BRE 中匹配任意字符，理论上可误匹配 `Xgithub/workflows/ci.yml`（虽实际不存在此类字符串，无真实影响）。 | 可改为 `grep -qF ".github/workflows/ci.yml"` 使用 Fixed String 精确匹配。 |

---

## Verdict

**REVISION REQUIRED**

理由：1 条 MUST FIX 未关闭：

1. **MUST FIX-1**（AC-8 `tail -3 | grep -q "FAIL: 0"` 假阴性）：当 SKIP > 0（23 个 skipif ACs，开发环境普遍触发），`tail -3` 取不到 "FAIL: 0" 行，验证命令即便所有 AC PASS 也会返回 exit 1，造成假 FAIL。

stage 2 AC kind 必查 3 项**全 PASS**（kind 列存在 + AC-8 behavioral 行 + 无 exempt）。bootstrap block 注释已说 "17 AC"，T-7 删 AC-15 后一致（reviewer 实读确认）。DAG 无环，process_tasks 6 required stages 覆盖。AC 覆盖矩阵完整（AC-1..AC-8 各有 ≥1 非 process 任务）。

---

## 后续指引（generator 修 spec_v2 前自查）

```bash
cd /data/home/zhhdzhang/nta/nta-lake/.claude/worktrees/harness-remote-push

SPEC=.harness/changes/harness-remote-push-onboarding-20260518/request_analysis/spec.md

# MUST FIX-1：确认 AC-8 验证方式不含 tail -3
grep -n "tail -3" "$SPEC"  # 期望 0 行

# MUST FIX-1：验证修复后命令：SKIP > 0 场景下仍能正确 PASS
printf "PASS: 100\nFAIL: 0\nSKIP: 50\n跳过: some\n全部通过（FAIL=0；SKIP 不阻塞）。\n" \
  | grep -qE "^FAIL: 0$" && echo "AC-8 format PASS" || echo "STILL BROKEN"

# SHOULD FIX-1：确认 T-3 description 不含"无 remote 项目时跳过"
grep -n "无 remote 项目时跳过" .harness/changes/harness-remote-push-onboarding-20260518/request_analysis/tasks.md
# 期望 0 行

# AC kind 检查（v1 已 PASS，v2 不能回退）
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' "$SPEC" \
  | grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|' && echo "kind col OK"
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' "$SPEC" \
  | grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|' && echo "behavioral row OK"
```

修完 spec_v2.md 后，更新 summary.md 阶段 2 行（verdict = REVISION REQUIRED，报告路径），开 spec_review_v2.md 申请二次评审（只需复检 MUST FIX-1 是否真修）。

---

## 本次用模型

**sonnet**（claude-sonnet-4-6）。符合 reviewer-agent.md §8 默认规约。本次主要工作为：AC-8 `tail -3 | grep "FAIL: 0"` 实跑反例构造（SKIP > 0 场景）+ self_check.sh 末段输出结构实读 + bootstrap block AC 数逐一清点 + markdown `\|` 管道语义验证，sonnet 完全胜任，无需升级 opus。
