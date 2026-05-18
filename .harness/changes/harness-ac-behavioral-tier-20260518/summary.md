---
change_id: harness-ac-behavioral-tier-20260518
title: AC 分层规约（static / behavioral）+ stage 9 强制门禁 + behavioral AC lint
owner: application-owner-agent
started_at: 2026-05-18T08:15:00Z
stage: done
status: closed
last_updated: 2026-05-18T10:35:00Z
related_changes:
  - pipeline-orchestrator-mvp-20260518
  - harness-reviewer-agent-separation-20260518
---

# Summary

> 这是本变更的 Single Source of Truth。任何阶段开始 / 通过 / 失败都必须同步更新这里。

## 一句话目标

让 self_check "全 PASS" 不再是 grep 假象——通过 AC 分层（static / behavioral）+ 每个 change 至少 1 条 behavioral AC + stage 9 不允许 deferred（除非显式 self-attest）的硬约束，杜绝刚被 pipeline-orchestrator-mvp stage 9 暴露的 "PASS 但真跑挂" 漏洞。

## 范围摘要

- **In scope**：
  - 在 `.harness/skills/request-analysis/SKILL.md` 加 AC 分层规约（`acceptance_kind: static | behavioral`）；每个 spec.md AC 表必须有 `kind` 列
  - 每个非纯文档/纯 harness change **至少 1 条 behavioral AC**（真跑代码：HTTP roundtrip / pytest 集成 / load_recipe / curl smoke 等）
  - `.harness/rules/development-process.md` stage 9 加硬约束：有部署面的 change `deploy_verify.verdict` 必须 `PASS`（或显式 `self-attest (理由)`），不允许 `deferred`
  - `scripts/_self_check.sh` 加 `run_ac_kind_lint` global function：扫所有 closed change 的 `spec.md` AC 表，要求至少 1 条标 `kind: behavioral`（纯 harness / 纯文档 change 可显式 `self-attest (...)` 豁免）
  - 把 pipeline-orchestrator-mvp stage 9 暴露的 3 个 follow-up 作为**实证章节**写入 spec.md「问题陈述」
  - dogfood：本变更自身按新规约走（spec.md 含 ≥1 behavioral AC，其形式为"真跑一次 `run_ac_kind_lint`，遇违规 change 必须 FAIL"）

- **Out of scope**：
  - 回填所有历史 closed change 的 AC `kind` 字段 → follow-up `harness-ac-kind-backfill-*`（grandfather 期：旧 change 暂豁免 lint，新 change 强制）
  - AC behavioral 测试的覆盖率指标（如"每 AC ≥1 测试"）→ 已被 SKILL §4「风险缓解 ↔ AC 测试列表」覆盖，本 change 不再扩展
  - test-fixture-isolation / pipeline-cache-fk-cascade 两个具体 bug 修复 → 单独 change（本 meta-change 治本，不掺杂治标）
  - stage 8 CI deferred 治理（git remote 未配置）→ 长期未决项，需要项目级别决策（不在本 harness change 范围）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done | v3 | — | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | done | v3 | APPROVED | v1: [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) ; v2: [spec_review_v2.md](request_analysis/review/spec_review_v2.md) · [tasks_review_v2.md](request_analysis/review/tasks_review_v2.md) ; v3: [spec_review_v3.md](request_analysis/review/spec_review_v3.md) · [tasks_review_v3.md](request_analysis/review/tasks_review_v3.md) |
| 3 编码实现 | done | v1 | — | [coding_report_v1.md](coding/coding_report_v1.md) — fixture 3/3 PASS + self_check 本 block 8/8 PASS + global ac-kind-lint PASS |
| 4 编码评审 | done | v1 | APPROVED | [code_review_v1.md](coding/review/code_review_v1.md) — 8/8 AC 真跑 PASS；2 SHOULD FIX 登记 deferred（fail-fast 全局计数 + 死代码 DRY） |
| 5 单测编写 | done | v1 | — | [test_report_v1.md](unit_test/test_report_v1.md) — 8 AC ↔ 测试映射 + fixture 3 场景真跑 + 覆盖维度 7 类 |
| 6 单测评审 | done | v1 | APPROVED | [test_review_v1.md](unit_test/review/test_review_v1.md) — 6 类独立探针全过；0 MUST/SHOULD FIX；2 NICE |
| 7 代码推送 | done | v1 | — | main 直接 commit（无 remote）；commit SHA 见 deploy_verify_v1.md 末更新 |
| 8 CI 验证 | self-attest | — | — | 项目无 remote 长期未决（spec 非范围 + tasks process_tasks P-ci.status=self-attest 已声明）|
| 9 部署验证 | done | v1 | PASS via self-attest | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) — 纯 harness 无部署面；按本 change 引入的 stage 9 self-attest 替代路径 dogfood：4 必填字段闭合在 frontmatter；行为型 AC-4 + AC-8 真跑证据 + stage 4/6 reviewer 独立实跑 PASS 证据 |
| 10 用户确认 | done | v1 | PASS via 授权 | zhhdzhang @ 2026-05-18T08:13:00Z（用户显式授权"按 1,2,3,4 你自行启动"——meta-change 无用户可见行为面，确认 = lint 守门按规约生效）|

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-18 | 不强制覆盖历史 closed change，新 change 起强制 lint | **19 个** closed change 全量回填工作量超本 change 承载；grandfather 旧 change 分两类（2 永久豁免 + 17 暂豁免，后续 backfill `harness-ac-kind-backfill-*` P1） | spec.md §范围 |
| 2026-05-18 | AC `kind` 字段从 `static` / `behavioral` 二分，不引入 `mixed` 第三类 | 二分简单可机械化；混合型 AC 应拆为两条独立 AC | spec.md §AC 分层 |
| 2026-05-18 | behavioral AC 不强求"必须跑 docker compose 全栈起服务"，可接受 ASGITransport + monkeypatch + in-process fake | 现有 apps/api/tests 大量用 ASGITransport，已是事实标准；不破坏既有测试设计 | spec.md §AC-3 |
| 2026-05-18 | 不在本 change 引入 AC 字段的 self_check schema 校验 | 用 grep 规则即可（spec v3：双条件 (ii) 锚定 AC 行 kind 单元格 regex `^\| AC-N \| behavioral \|` 而非裸字串 grep）；schema 化放 follow-up `harness-spec-schema-validator-*` | spec.md §AC-2 |

## 当前阻塞

无（stage 1 in_progress）。

## Deferred 项（已 review 通过但未在本 change 内修）

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX (tasks v2) | T-4/T-6 depends_on 隐式覆盖（reviewer 认可 acceptable） | stage 3 实施时自然落地 |
| SHOULD FIX (tasks v2) | T-8 rollback 路径（lint 对豁免误报回 T-1b 修豁免） | tasks v3 description 已含 3 类 rollback 路径 |
| SHOULD FIX (tasks v2) | T-1b 注释明示本 change 自身不豁免 | T-1b description 已含此意图（dogfood）|
| SHOULD FIX (code v1) | `run_ac_kind_lint` fail-fast 用全局 `$FAIL` 计数器，被前面 pipeline AC-8 FAIL 污染时输出误导日志 | follow-up `harness-lint-fail-fast-scope-*`（同型 reviewer-lint 一并修；非阻塞，AC 自身真值未受影响）|
| SHOULD FIX (code v1) | `_ac_kind_lint_exempt_changes` 与 `_inline` 死代码重复（DRY 违反） | follow-up `harness-lint-dedup-*`；当前 inline 版本是真使用，function 留作未来 Python migration 入口 |

## 交付

> 关闭本变更时填写。

- Branch：main（无 remote）
- PR：N/A
- Merge commit：本 commit（含 spec/tasks/coding_report/test_report/deploy_verify 全部产物 + .harness/skills/* + .harness/rules/* + scripts/_self_check.sh + scripts/lint/test_ac_kind_lint_fixture.sh + .harness/changes/_template/spec.md）
- 部署版本：N/A（纯 harness）
- 用户确认：zhhdzhang @ 2026-05-18 显式授权"按 1,2,3,4 你自行启动"
- 关闭时间：2026-05-18T10:35:00Z

## 复盘

> 关闭时填写。
