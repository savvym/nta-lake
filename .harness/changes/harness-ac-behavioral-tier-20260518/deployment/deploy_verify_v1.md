---
change_id: harness-ac-behavioral-tier-20260518
version: 1
env: n/a
deployed_at: 2026-05-18T10:30:00Z
commit_sha: TBD-on-stage-7-commit
verifier: claude-agent:harness-ac-behavioral-tier-20260518-stage9-verifier-v1
verdict: PASS via self-attest (纯 harness 变更：仅改 .harness/* + scripts/* + scripts/lint/* + _template/spec.md；无 dataplat 代码 / DB schema / 路由 / worker / web 资产；deploy_verify 用 self-attest 替代，按 development-process.md stage 9 §"替代路径" 4 必填字段已闭合)
self_attest:
  理由: |
    本 change 是 harness meta-change（第二个，第一个是 harness-reviewer-agent-separation-20260518），目的是把"AC 真实跑通性"机械化，落地于 SKILL 文档 + self_check shell 脚本 + bash fixture。
    没有任何 dataplat 业务代码 / DB schema / 路由 / worker job / web 资产改动；不存在"部署面"。
    按本 change 自身在 development-process.md stage 9 段引入的硬约束"(ii) self-attest 替代路径 + 4 必填字段"走 dogfood：
      - 理由：本节
      - 本机证据列表：见下方
      - 跑过的命令：见下方
      - 时间：2026-05-18T10:30:00Z
  本机证据列表:
    - /tmp/dataplat-dev-logs/self-check-v3.log（全仓 self_check 输出，含本 change block 8/8 PASS + ac-kind-lint global PASS + reviewer-lint global PASS）
    - scripts/lint/test_ac_kind_lint_fixture.sh（fixture 3 场景脚本）
    - .harness/changes/harness-ac-behavioral-tier-20260518/coding/coding_report_v1.md（编码报告含 fixture 真跑输出）
    - .harness/changes/harness-ac-behavioral-tier-20260518/coding/review/code_review_v1.md（stage 4 reviewer 独立实跑 8/8 AC PASS 证据）
    - .harness/changes/harness-ac-behavioral-tier-20260518/unit_test/review/test_review_v1.md（stage 6 reviewer 6 类独立探针全过证据）
  跑过的命令:
    - "bash scripts/lint/test_ac_kind_lint_fixture.sh"
    - "DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh"
    - "bash scripts/_self_check.sh harness-ac-behavioral-tier"
    - "bash scripts/_self_check.sh ac-kind-lint"
    - "bash scripts/_self_check.sh reviewer-lint"
    - "awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md | grep -cE '^\\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\\|[[:space:]]*(\\*\\*)?behavioral(\\*\\*)?[[:space:]]*\\|'  # 期望 2"
  时间: 2026-05-18T10:30:00Z
---

# Deploy Verification v1 (self-attest)

> 本 change 是 harness meta-change，无部署面；按本 change 自身在 development-process.md stage 9 引入的"self-attest 替代路径"走，必填 4 字段在 frontmatter 已闭合。本节展开行为型 AC 实证证据。

## 验证矩阵（重复实跑，独立于 self_check 与 stage 4/6 reviewer 跑过的）

| ID | kind | 验收项 | 本机证据 | 实跑命令 |
|---|---|---|---|---|
| AC-4 | behavioral | fixture 3 场景守门正确（合规 PASS / 缺 kind 列 FAIL / **全 static + 描述含 behavioral 字串 FAIL**） | `=== ALL 3 FIXTURES PASS ===` | `bash scripts/lint/test_ac_kind_lint_fixture.sh` |
| AC-8 | behavioral | 全仓 self_check 本 change block 8/8 + 2 global lint PASS | `PASS  ac-kind-lint` + `PASS  reviewer-lint` + 本 change 8/8 PASS | `bash scripts/_self_check.sh` |

## Self_check 完整输出（节选）

```text
=== global :: reviewer-lint ===
PASS  reviewer-lint  reviewer 字段独立性守门（反向×2 + 白名单）

=== harness-ac-behavioral-tier-20260518 :: 8 AC ===
PASS  AC-1        SKILL.md 新增 § AC 分层规约（含 kind 定义 + behavioral 三层 + 豁免判定）
PASS  AC-2        SKILL.md 含 '每个非豁免 change 至少 1 条 behavioral AC' 硬约束 + ac_kind_lint: exempt 自声明格式
PASS  AC-3        expert-reviewer SKILL 加 stage 2 必查 3 项 + git diff 复核
PASS  AC-4        run_ac_kind_lint fixture 真跑（3 场景：合规 PASS / 缺 kind 列 FAIL / 全 static 但描述含 behavioral FAIL）
PASS  AC-5        development-process.md stage 9 含 4 checkpoint + self-attest 模板
PASS  AC-6        self_check main 含 run_ac_kind_lint 调用 + 本 spec AC 行 behavioral ≥ 2 + _template 含 kind 列
PASS  AC-7        SKILL.md 豁免清单分两类（永久 2 + 暂豁免 17）且 19 个 ID 全命中
PASS  AC-8        self_check 含 run_harness_ac_behavioral_tier 调用（自递归确认本 block 在 main 调用链中）

=== global :: ac-kind-lint ===
PASS  ac-kind-lint  AC 分层规约守门（kind 列存在 + AC 行 kind=behavioral 锚定 regex）
```

## 风险评估

- [x] 涉及 schema 不兼容？**否**。无 DB / API schema 改动。
- [x] 涉及不可回滚操作？**否**。改动文件可纯回滚（git revert）。
- [x] 需要 follow-up？**是**：
  - `harness-ac-kind-backfill-*`（P1）：17 个实代码 closed change 的 backfill
  - `harness-lint-fail-fast-scope-*`：`run_ac_kind_lint` fail-fast 全局计数器误归因
  - `harness-lint-dedup-*`：`_ac_kind_lint_exempt_changes` vs `_inline` 重复

## Verdict

**PASS via self-attest**

理由：纯 harness 变更，无部署面；本 change 自身按新规约 dogfood 跑通（self_check 8/8 + 2 global lint PASS、fixture 3 场景实跑、stage 4/6 独立 reviewer 真跑 PASS）；4 必填字段已闭合在 frontmatter。

## 处理动作

- ✅ PASS via self-attest → 进入阶段 10 用户确认。
- 同步：把本 change 全部产物 + scripts/lint/test_ac_kind_lint_fixture.sh + scripts/_self_check.sh 改动 + 三个 SKILL 文档改动一起 commit；summary.md stage 9=done。
