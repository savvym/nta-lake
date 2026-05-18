---
change_id: harness-ac-behavioral-tier-20260518
version: 1
authored_at: 2026-05-18T10:20:00Z
status: waiting_review
---

# Test Report v1

> 本变更是纯 harness meta-change（rules + skills + scripts），无 Python / TS 业务模块；"单测"载体是 **`scripts/lint/test_ac_kind_lint_fixture.sh`** + **`scripts/_self_check.sh::run_harness_ac_behavioral_tier`**。Stage 3 编码时已经落地，stage 5 主要工作是**汇总测试覆盖矩阵 + 真跑证据**。

## 验收项 ↔ 测试映射

| AC ID | kind | 测试形态 | 测试位置 | 测试函数/步骤 |
|---|---|---|---|---|
| AC-1 | static | self_check bash 断言 | `scripts/_self_check.sh::run_harness_ac_behavioral_tier` | `run_ac AC-1` 4-grep `.harness/skills/request-analysis/SKILL.md`（"AC 分层规约" / "kind: behavioral" / "豁免判定" 三段命中 + test -f） |
| AC-2 | static | self_check bash 断言 | 同上 | `run_ac AC-2` 2-grep（"至少 1 条 behavioral" + "ac_kind_lint: exempt"） |
| AC-3 | static | self_check bash 断言 | 同上 | `run_ac AC-3` 3-grep `.harness/skills/expert-reviewer/SKILL.md`（必查 3 项 + git diff 复核 + ac_kind_lint） |
| AC-4 | **behavioral** | bash fixture 真跑 3 场景 | `scripts/lint/test_ac_kind_lint_fixture.sh` | `run_lint_in_subshell` × 3：合规 PASS / 缺 kind 列 FAIL / 全 static + 描述含 behavioral 字串 FAIL（**关键打靶反例**） |
| AC-5 | static | self_check awk + grep | 同 self_check | awk 抽 stage 9 段 + 4-grep（verdict=PASS / self-attest / 禁止 deferred / 必填字段） |
| AC-6 | static | self_check 复合断言 | 同 self_check | grep `run_ac_kind_lint` + awk 抽本 spec AC 表 + AC 行 regex 计数 ≥ 2 + grep `_template` 含 kind 列 |
| AC-7 | static | self_check for-loop | 同 self_check | for 19 ID 单独 grep + 永久豁免 / 暂豁免分类字面命中 |
| AC-8 | **behavioral** | self_check 自递归 | 同 self_check | grep `run_harness_ac_behavioral_tier` 在 main 调用链（自指证明本 block 在 main 调用） |

每条 AC 至少出现一次。**behavioral AC：AC-4（L3 bash fixture 真跑） + AC-8（自递归调用确认）**，满足"≥1 条 behavioral" 自约束。

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| `scripts/lint/test_ac_kind_lint_fixture.sh` | bash fixture | 3 场景（PASS/FAIL/FAIL） |
| `scripts/_self_check.sh::run_harness_ac_behavioral_tier` | self_check block | 8 AC |
| `scripts/_self_check.sh::run_ac_kind_lint` | self_check global lint | 1 global AC（扫所有未豁免 spec） |

## Mock 范围声明

- **允许 mock**：fixture 用 `mktemp -d /tmp/...` 构造临时 spec.md，与生产 `.harness/changes/` 物理隔离；`AC_KIND_LINT_SCAN_DIR` / `AC_KIND_LINT_EXEMPT_OVERRIDE` 两个 env 注入用于 fixture 隔离。
- **禁止 mock**：`run_ac_kind_lint` 函数本身不 mock；fixture subshell 跑的是真实 self_check 脚本（仅 SCAN_DIR + EXEMPT 注入），与生产相同代码路径。

## 测试真跑证据

### Fixture 真跑（AC-4 核心）

```text
$ bash scripts/lint/test_ac_kind_lint_fixture.sh
=== fixture (1) 合规 spec → 期望 PASS（exit 0） ===
exit=0

=== fixture (2) 缺 kind 列 → 期望 FAIL（exit != 0） ===
exit=1

=== fixture (3) **关键打靶** 全 static + 描述含 behavioral 字串 → 期望 FAIL（exit != 0） ===
exit=1

=== ALL 3 FIXTURES PASS ===
```

### self_check block + global lint（AC-1..AC-8 + ac-kind-lint + reviewer-lint）

```text
=== harness-ac-behavioral-tier-20260518 :: 8 AC ===
PASS  AC-1..AC-8 全部
=== global :: ac-kind-lint ===
PASS  ac-kind-lint
=== global :: reviewer-lint ===
PASS  reviewer-lint
```

详见 [coding_report_v1.md § 本地校验结果](../coding/coding_report_v1.md)。

## 覆盖维度

| 维度 | 是否覆盖 | 备注 |
|---|---|---|
| Happy path（合规 spec → PASS） | ✓ | fixture (1) |
| Negative path - 结构缺失（缺 kind 列） | ✓ | fixture (2) |
| Negative path - **语义陷阱**（kind=static + 描述含 behavioral 字串） | ✓ | fixture (3) **关键打靶** |
| 豁免清单（永久 / 暂豁免 / 自声明 frontmatter） | ✓ | AC-7 + ac-kind-lint inline |
| env 注入（SCAN_DIR / EXEMPT_OVERRIDE） | ✓ | fixture 真用 env 注入 |
| 自递归 dogfood（本 spec 自身过 lint） | ✓ | AC-6 + AC-8 + 全仓 self_check 跑过 |
| edge case - AC-Na 字母后缀 / 加粗 ** / 多空格 | ✓（v3 reviewer 实测） | regex pattern 已覆盖 |

## 已知未解决问题

- `run_ac_kind_lint` fail-fast 用全局 `$FAIL` 计数器（同型 reviewer-lint），被前面 FAIL（如 pipeline AC-8）触发误导日志 → SHOULD FIX deferred 到 follow-up `harness-lint-fail-fast-scope-*`。本身 lint 真值不受影响。
- `_ac_kind_lint_exempt_changes` 与 `_inline` DRY 违反 → SHOULD FIX deferred 到 follow-up `harness-lint-dedup-*`。

## 下一步

- 准备 stage 6 review：spawn `claude-agent:harness-ac-behavioral-tier-20260518-stage6-reviewer-v1`
- summary.md stage=`unit_test_review` status=`in_progress`
