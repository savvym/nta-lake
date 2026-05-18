---
change_id: harness-ac-behavioral-tier-20260518
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-agent:harness-ac-behavioral-tier-20260518-stage6-reviewer-v1
reviewed_at: 2026-05-18T10:55:00Z
verdict: APPROVED
---

# Test Review v1

## 评审范围与方法

本评审是 **artifact 模式**（评 `unit_test/test_report_v1.md` + 实测载体 `scripts/lint/test_ac_kind_lint_fixture.sh` + `scripts/_self_check.sh::run_ac_kind_lint`/`run_harness_ac_behavioral_tier`），核心责任是**不依赖 test_report 自述**，独立验证：

1. 每条 spec v3 AC 是否真有测试载体打靶
2. fixture (3) 关键打靶反例是否真"诱使"裸 grep 命中（spec v3 MUST FIX #2 的实证靶）
3. mock 边界 / cleanup trap / negative path / 字串误命中边缘 case

为此 reviewer **独立跑了** 6 类探针（不只看 test_report）。

## 独立探针验证记录

### 探针 P1：fixture (3) 打靶反例真"诱使"裸 grep 命中（核心命题）

任务 prompt 要求 reviewer 必须自己跑 `awk ... | grep -c behavioral` 验证打靶反例的 spec.md 内容能否被裸 grep 假命中。

构造临时 spec.md（复刻 fixture (3) `FIXTURE_BAD_STATIC_MENTION` 的内容）后跑：

```
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' /tmp/test-spec.md | grep -c behavioral
→ 4
```

**结论**：裸 `grep -c behavioral` 命中 **4 次**（描述里的 "behavioral 三层"、"behavioral 集成测试"、"behavioral 测试"、"算 behavioral"），**全部假命中**——无任何 AC 行 kind 单元格真为 behavioral。

继续跑锚定 regex：

```
awk ... | grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|'
→ 退码 1（正确拒绝）
```

**这证明 fixture (3) 设计真有效**：如果 lint 用裸 grep，会 PASS（=漏洞）；spec v3 改用锚定 regex 才真守门。这正是 stage 2 v2 MUST FIX #2 的核心 invariant，stage 5 单测把它落到机械化打靶——**完美打靶**。

### 探针 P2：fixture 3 场景真跑结果

```
$ bash scripts/lint/test_ac_kind_lint_fixture.sh
=== fixture (1) 合规 spec → 期望 PASS（exit 0） === exit=0
=== fixture (2) 缺 kind 列 → 期望 FAIL（exit != 0） === exit=1
=== fixture (3) **关键打靶** 全 static + 描述含 behavioral 字串 → 期望 FAIL（exit != 0） === exit=1
=== ALL 3 FIXTURES PASS ===
```

退码 0，断言齐全 ✓。

### 探针 P3：frontmatter `ac_kind_lint:` 非 `exempt` 字面是否被错跳过（negative path）

任务 prompt 明示问"是否漏了 spec frontmatter 含 `ac_kind_lint: exempt: yes/no`，非 `exempt` 字面，是否被跳过 lint 误识别"。

构造 `ac_kind_lint: yes_not_exempt` 的 spec 并跑 lint：

```
head -20 spec.md | grep -qE "^ac_kind_lint:[[:space:]]+exempt"
→ NO MATCH（不会被跳过 ✓）
lint 结果 → FAIL（正确，因为 AC 表缺 kind 列）
```

`run_ac_kind_lint` inline 用 `grep -qE "^ac_kind_lint:[[:space:]]+exempt"` 严格锚定单词 `exempt`，非 `exempt` 字面（如 `yes_not_exempt`、`maybe`）**不会**被误跳——negative path 正确。

### 探针 P4：扩展字串误命中（`behavioralism` 等）

构造 kind 单元格为 `behavioralism` 的 spec：

```
| AC-1 | behavioralism | foo | grep | hit |
→ lint FAIL（正确拒绝）
```

锚定 regex 后缀含 `[[:space:]]*\|`，不被 `behavioral` 前缀子串扩展误命中 ✓。

### 探针 P5：edge case（AC-Na 字母后缀 + `**` 加粗 + 多空格）

```
| AC-1a |  **behavioral**  | foo | pytest | 0 |   → PASS ✓
| AC-99z | behavioral | foo | pytest | 0 |        → PASS ✓
```

regex `AC-[0-9]+[a-z]?` 真覆盖字母后缀（spec v3 决策栏 SHOULD #4 拆分示例 AC-Na/AC-Nb），`(\*\*)?behavioral(\*\*)?` 真覆盖加粗。

### 探针 P6：trap cleanup 在 `set -e` 提前 exit 时是否真触发

构造 mktemp 后立刻 `false` 触发 `set -e` 的脚本：

```
$ bash /tmp/probe-trap-test.sh
T1=/tmp/probe-trap-t1.HSzvnW
TRAP RAN: 清理 /tmp/probe-trap-t1.HSzvnW /tmp/probe-trap-t2.s2LhGx
退码=1
$ ls /tmp/probe-trap-t* → 已全清
```

bash 的 EXIT trap 在 `set -e` 触发的 exit 路径**确实触发**。fixture 用 `trap cleanup EXIT` 是 robust 的清理写法 ✓。

补充探针：把 fixture 的 `rc2` 强制改 0 让 fixture 在 (2) 处 exit 1 → `ls /tmp/ac-kind-fixture-*` 仍清干净 ✓。

## 检查清单结论（artifact 模式 SKILL §1）

| 检查项 | 结论 |
|---|---|
| 每条 spec 验收标准都映射到至少一条具体测试用例 | **PASS**。AC-1..AC-8 全有载体（详下 AC 覆盖矩阵） |
| 没有空跑断言（`assert True`、断言任意 != None） | **PASS**。fixture 3 个场景退码断言精确（== "0" / != "0"）；self_check 用 `run_ac` 跑真命令；唯一 `true` 是历史 `AC-13 自递归` 模式（本 block 无 AC-13） |
| mock 范围与 coding-style §1.7 一致 | **PASS**。无 Python/TS 业务代码 mock；fixture 用 mktemp + env 注入（`AC_KIND_LINT_SCAN_DIR` / `AC_KIND_LINT_EXEMPT_OVERRIDE`），与生产 `.harness/changes/` 物理隔离，**这是合理的 mock 边界**（mock 的是"扫描范围"和"豁免清单"两个**输入**，被测代码路径完全相同——`run_ac_kind_lint` 函数本身**不 mock**） |
| 测试名能反映场景 | **PASS**。fixture (1)(2)(3) 各自配 "合规 PASS / 缺 kind 列 FAIL / 全 static + 描述含 behavioral 字串 FAIL"，语义明确无 test_1/test_a |

## AC 覆盖矩阵（每条 spec v3 AC 逐项独立核查）

| AC | spec 验证命令 | 实测载体位置 | 是否真覆盖 | 评注 |
|---|---|---|---|---|
| AC-1 | 4-grep SKILL `.harness/skills/request-analysis/SKILL.md` | `run_harness_ac_behavioral_tier::run_ac AC-1` | ✓ | 4-grep + test -f；static 性质，grep 即足 |
| AC-2 | 2-grep（"至少 1 条 behavioral" + "ac_kind_lint: exempt"） | `run_ac AC-2` | ✓ | 2-grep；static |
| AC-3 | 3-grep `expert-reviewer/SKILL.md` | `run_ac AC-3` | ✓ | 3-grep；static |
| AC-4 | **fixture 3 场景真跑** | `scripts/lint/test_ac_kind_lint_fixture.sh` | ✓✓ | **核心 behavioral**；P1 独立验证打靶反例真有效（裸 grep 命中 4 次假命中 vs 锚定 regex 退码 1） |
| AC-5 | awk 抽 stage 9 段 + 4-grep | `run_ac AC-5` | ✓ | awk 状态机锚定段落（v2 闭 SHOULD #2）+ 4 checkpoint 全覆盖 |
| AC-6 | 复合：run_ac_kind_lint 调用 + 本 spec AC 行 behavioral ≥ 2 + _template 含 kind 列 | `run_ac AC-6` | ✓ | 自递归 dogfood；regex 真锚定 |
| AC-7 | 19 ID for-loop grep + 分类字面 | `run_ac AC-7` | ✓ | for-loop（v2 闭 MUST #3）；19 ID 全覆盖 |
| AC-8 | **self_check 自递归** | `run_ac AC-8` 内 `grep -q "run_harness_ac_behavioral_tier"` | ✓ | **behavioral**：证明本 block 在 main 调用链中（不是 dead code） |

**覆盖结论**：AC 1..8 **8/8** 全有真测试载体；behavioral AC-4 + AC-8 是双 behavioral，满足 dogfood ≥1 自约束（实际 ≥2）。

## Mock 范围声明评估

test_report §"Mock 范围声明"声明：

- **允许 mock**：fixture 用 `mktemp -d` 构造临时 spec.md（与生产 `.harness/changes/` 物理隔离）；env 注入 `AC_KIND_LINT_SCAN_DIR` / `AC_KIND_LINT_EXEMPT_OVERRIDE`。
- **禁止 mock**：`run_ac_kind_lint` 函数本身不 mock；fixture subshell 跑真实 self_check 脚本（仅 SCAN_DIR + EXEMPT 注入），与生产相同代码路径。

**评估**：**合理且清晰**。这正是 dependency injection 式的 mock 边界——mock 的是函数**输入**（环境变量、scan 范围），不 mock 函数**实现**。比起改 `.harness/changes/` 真目录的做法（污染真目录、回滚困难），mktemp + env 注入是更 robust 的边界 ✓。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

（test_report 已显式登记 2 个 deferred SHOULD FIX：`run_ac_kind_lint` fail-fast 用全局 `$FAIL` 计数器 / `_ac_kind_lint_exempt_changes` 与 `_inline` DRY 重复——均已在 stage 4 code review v1 中识别并 deferred 到 follow-up `harness-lint-fail-fast-scope-*` / `harness-lint-dedup-*`，本 stage 6 不重复登记。）

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | `scripts/lint/test_ac_kind_lint_fixture.sh` fixture (3) | fixture (3) 是"全 static + 描述含 behavioral 字串"反例，**没有显式 fixture 覆盖**"AC 行 kind 单元格扩展字串"（如 `behavioralism`、`behavior` 截断）——P4 探针验证了 lint 自身正确拒绝，但 fixture 文档化打靶能更清楚 | 加 fixture (4): kind 单元格为 `behavioralism` 的反例，断言 lint FAIL。**非阻塞**——P4 已独立证明锚定 regex 真守门，本 NICE 仅为未来 regression 加保险 |
| NICE-2 | test_report v1 §"已知未解决问题" | 2 个 deferred SHOULD FIX 列了但未链接 follow-up change_id 占位 | 写明跟进 follow-up：`harness-lint-fail-fast-scope-<TBD>` / `harness-lint-dedup-<TBD>`。**非阻塞** |

## Verdict

**APPROVED**。理由：

1. fixture (3) 关键打靶反例**真**诱使裸 grep 命中（P1 独立验证：裸 `grep -c behavioral` 4 次假命中 vs 锚定 regex 退码 1）—— spec v3 MUST FIX #2 的核心 invariant 被机械化锁死，**stage 5 单测真完成了 stage 2 v3 闭环的最后一公里**。
2. AC-1..AC-8 **8/8** 全有真测试载体，behavioral AC-4 + AC-8 满足 dogfood ≥1 自约束。
3. mock 范围（mktemp + env 注入）边界合理且 test_report 声明清晰。
4. negative path（frontmatter 非 `exempt` 字面）+ edge case（字母后缀 / 加粗 / 扩展字串）+ trap cleanup 全独立验证通过。
5. 0 MUST FIX；2 NICE TO HAVE 不阻塞。

## 后续指引

APPROVED → 进入 stage 7（代码推送）。复检方式：

```bash
# 复检 fixture 真跑
bash scripts/lint/test_ac_kind_lint_fixture.sh                  # 期望退码 0
# 复检 self_check 本 block + global lint
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh harness-ac-behavioral-tier
bash scripts/_self_check.sh ac-kind-lint                        # 期望退码 0
# 复检本 review 自身 reviewer 字段独立性（守门）
bash scripts/_self_check.sh reviewer-lint                       # 期望 PASS
```
