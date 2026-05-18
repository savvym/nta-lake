---
change_id: harness-ac-behavioral-tier-20260518
version: 1
authored_at: 2026-05-18T10:00:00Z
branch: main（无 remote）
base_commit: cf7ae60
head_commit: (uncommitted; 见 git status --short)
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `.harness/skills/request-analysis/SKILL.md` | mod | 加 §"AC 分层规约"：kind 定义 + behavioral 三层 + 豁免清单（永久 2 / 暂豁免 17） + 自声明机制 + 豁免判定标准 + 混合 AC 拆分示例 | T-1a / T-1b / T-1c |
| `.harness/skills/expert-reviewer/SKILL.md` | mod | 加 §"stage 2 AC kind 字段必查"：必查 3 项 + MUST FIX 模板 + self_check 守门指引 | T-2 |
| `.harness/rules/development-process.md` | mod | stage 9 段加硬约束 4 checkpoint：verdict=PASS / self-attest 替代 + 4 必填字段 / 禁止纯 deferred / SKILL 引用 + self-attest 模板片段 | T-3 |
| `scripts/_self_check.sh` | mod | 加 `run_ac_kind_lint` global function（双条件断言 + env 入口 `AC_KIND_LINT_SCAN_DIR` / `AC_KIND_LINT_EXEMPT_OVERRIDE`）+ `run_harness_ac_behavioral_tier` 本 change block（8 AC）+ main 调用链 + case 分支 | T-4 / T-7 |
| `scripts/lint/test_ac_kind_lint_fixture.sh` | new | AC-4 fixture 真跑脚本：3 场景（合规 PASS / 缺 kind 列 FAIL / **全 static 但描述含 behavioral 字串 FAIL** — 最隐蔽反例打靶） | T-6 |
| `.harness/changes/_template/request_analysis/spec.md` | mod | 示例 AC 表加 `kind` 列（AC-1: static / AC-2: behavioral）+ 表头上方加 kind 定义说明 + 拆分硬约束引用 | T-5 |

> **门禁**：本表与 `git diff --name-only` 一致（5 个 modified + 1 个 new；本 change 目录 6 个 spec/tasks/review/summary/coding_report/deployment 文件本身不算"源码"改动）。

## 与 tasks.md 的映射

| Task ID | 状态 | 备注 |
|---|---|---|
| T-1a | done | SKILL kind 定义 + behavioral 三层 + 不算 behavioral 反例 |
| T-1b | done | 豁免清单 19 ID 分两类 + 自声明 frontmatter 格式 + 豁免判定标准 |
| T-1c | done | 混合 AC 拆分伪代码示例 |
| T-2 | done | expert-reviewer SKILL 加段（必查 3 项 + MUST FIX 模板） |
| T-3 | done | development-process.md stage 9 加段 |
| T-4 | done | `run_ac_kind_lint` 含 fail-fast + env 入口 + 双条件断言 + 共享 `_ac_kind_lint_exempt_changes_inline` |
| T-5 | done | `_template/spec.md` 加 kind 列 |
| T-6 | done | fixture 真跑 3 场景**全 PASS**（含关键打靶反例） |
| T-7 | done | `run_harness_ac_behavioral_tier` 8 AC 全 PASS |
| T-8 | done（见下"本地校验结果"） | 全仓 self_check 跑通，本 block 8/8 + 2 个 global lint PASS |

## 偏离 spec / trade-off

无 spec 偏离；spec v3 全部 8 个 AC 实现到位。

## 本地校验结果

### Fixture 真跑（AC-4 核心证据）

```text
$ bash scripts/lint/test_ac_kind_lint_fixture.sh
=== fixture (1) 合规 spec → 期望 PASS（exit 0） ===
exit=0

=== fixture (2) 缺 kind 列 → 期望 FAIL（exit != 0） ===
exit=1

=== fixture (3) **关键打靶** 全 static + 描述含 behavioral 字串 → 期望 FAIL（exit != 0） ===
exit=1

=== ALL 3 FIXTURES PASS ===
  (1) 合规 PASS ✓
  (2) 缺 kind 列 FAIL ✓
  (3) 全 static + 描述含 behavioral 字串 FAIL ✓（机械化锚定 regex 真守门）
```

反例 (3) 是 v2 reviewer 的 MUST FIX #2 实证：v2 spec 原设计裸 `grep -q behavioral` 会被描述里 "behavioral 三层" 字串误命中；v3 改用 AC 行 regex `^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|` 锚定 kind 单元格，**实跑证明真守门**。

### 全仓 self_check

```text
$ DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat \
  DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 \
  bash scripts/_self_check.sh

=== harness-ac-behavioral-tier-20260518 :: 8 AC ===
PASS  AC-1        SKILL.md 新增 § AC 分层规约
PASS  AC-2        SKILL.md 含 "每个非豁免 change 至少 1 条 behavioral AC" + ac_kind_lint: exempt
PASS  AC-3        expert-reviewer SKILL 加 stage 2 必查 3 项 + git diff 复核
PASS  AC-4        run_ac_kind_lint fixture 真跑（3 场景）
PASS  AC-5        development-process.md stage 9 含 4 checkpoint + self-attest 模板
PASS  AC-6        self_check main 含 run_ac_kind_lint 调用 + 本 spec AC 行 behavioral ≥ 2 + _template 含 kind 列
PASS  AC-7        SKILL.md 豁免清单分两类（永久 2 + 暂豁免 17）且 19 ID 全命中
PASS  AC-8        self_check 含 run_harness_ac_behavioral_tier 调用

=== global :: ac-kind-lint ===
PASS  ac-kind-lint  AC 分层规约守门（kind 列存在 + AC 行 kind=behavioral 锚定 regex）

=== global :: reviewer-lint ===
PASS  reviewer-lint  reviewer 字段独立性守门
```

self_check 总 exit code 1 是因为 `pipeline-orchestrator-mvp-20260518 AC-8 (test_cache_hit_*)` FAIL —— 这是 stage 9 暴露的 fixture-isolation bug（commit hash 撞库），**与本 change 无关**，正是 change #2 的治理目标（已记 follow-up `test-fixture-isolation-*`）。

## 已知未解决问题

- pipeline-orchestrator-mvp AC-8 FAIL（fixture isolation，不属本 change）：change #2 `stage9-followup-cleanup-*` 处理。
- 17 个历史 closed change 中含 dataplat 实代码却暂豁免：**已记 follow-up `harness-ac-kind-backfill-*` P1**（spec.md AC-7 已硬编码 19 ID 分两类）。

## 下一步

- 准备 stage 4 review：spawn `claude-agent:harness-ac-behavioral-tier-20260518-stage4-reviewer-v1`
- summary.md stage=`coding_review` status=`in_progress`
