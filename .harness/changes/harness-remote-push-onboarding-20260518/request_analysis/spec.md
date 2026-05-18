---
change_id: harness-remote-push-onboarding-20260518
version: 2
authored_at: 2026-05-19T00:00:00Z
status: draft
prior_version: 1
prior_review: request_analysis/review/spec_review_v1.md
---

# Spec：harness 适配 origin/main remote + 撤销 ci.yml/bootstrap AC-15

> **v2 修订说明**：闭 spec_review_v1 的 1 MUST FIX + 2 SHOULD FIX + 2 NICE。

## v1 review 闭环表

| # | v1 问题 | v2 状态 |
|---|---|---|
| MUST #1 | AC-8 `tail -3 \| grep -q "FAIL: 0"` 假阴性（SKIP > 0 时末 3 行非 "FAIL: 0"）| **CLOSED**：去掉 `tail -3`，改为 `grep -qE "^FAIL: 0$"` 直接搜全 log（防 SKIP 干扰）|
| SHOULD #1 (tasks T-3) | T-3 description 引入"无 remote 项目时跳过"措辞 + 把 origin URL 硬编码进 rules 文档 | **CLOSED**：tasks_v2 T-3 description 去掉"如有 remote / 跳过"与具体 URL；rules 通用文档只说 "git push origin main"|
| SHOULD #2 (spec AC-4) | "不含 无 remote 长期未决" 反向 grep 在既有 stage 8 中本就为 0 命中（描述措辞误导：T-4 实际是新增非"替换"）| **CLOSED**：AC-4 描述明示"防回归断言（既有 stage 8 已无此措辞，断言确保未来不重新引入）"，避免误导 |
| NICE #1 | （reviewer 提到第 5 点 AC 分层全 PASS，无 NICE 行动项）| N/A |
| NICE #2 | bootstrap block 注释预确认 17 AC 与 self_check 实际 18 调用一致 | **已确认**：T-7 description "如有 18 → 改 17" 准确 |

## 背景

`repo-files-tab-v2-20260518` 关闭后用户加了 origin：

```bash
git remote add origin git@github.com:savvym/nta-lake.git
git push -u origin main
```

至此项目从"无 remote"演进到"有 remote（GitHub）"。但 harness 多处假设无 remote：

- `.harness/skills/request-analysis/SKILL.md` L289："无 remote 项目（本仓库当前情况）：用 `git log --stat <baseline-commit>..HEAD` 等价"
- `.harness/skills/expert-reviewer/SKILL.md` L172："reviewer 必跑 `git diff --stat origin/main..HEAD`（或 `git log --stat <baseline>..HEAD` 无 remote 时）"
- `.harness/rules/development-process.md` stage 7：未明示 push 远端的步骤；stage 8 CI 验证 self-attest 措辞引"无 remote 长期未决"
- 5 个 closed change 的 summary 标 "CI 验证 self-attest（项目无 remote 长期未决）"（历史记录，不动）

同时，**项目策略**：用户明示**不引入远程 CI**（GitHub Actions 本质 = 跑 pytest，与本地 `self_check.sh` 等价，反馈快、无依赖；保留 `ci.yml` 仅会让每次 push 红叉）。

因此本 change 范围二合一：
1. **harness 规约层**清算"无 remote"措辞，加 stage 7 push 步骤
2. **代码层**撤销 `.github/workflows/ci.yml` + 反向 bootstrap-monorepo AC-15

## 问题陈述

1. SKILL.md / development-process.md 中"无 remote"分支描述与现状矛盾，新读者会困惑。
2. stage 7 "Quality Gate" 没有"push 到 remote"的硬约束，单作者直 push main 与 PR 流程的策略选择隐式。
3. stage 8 self-attest 理由"无 remote 长期未决"已失效；但项目策略仍 self-attest（不要远程 CI），需要新理由。
4. `.github/workflows/ci.yml` 现存且第一次 push 已触发跑（28s）；缺 MinIO service → 大概率 pytest 失败 → GitHub commit status 红；与"项目策略不要远程 CI"决策矛盾。
5. `scripts/_self_check.sh` L132-133 检查 `ci.yml` 存在合法（bootstrap-monorepo block run_bootstrap_monorepo 中的 AC-15）；删 ci.yml 必须同步删 grep 否则 main 调用链 FAIL。
6. `.gitignore` 不忽略 `.claude/`（worktrees + session 缓存），上次 push 差点漏推。

## 范围

In scope（**8 条 AC，含 1 条 behavioral**）：

- **AC-1** static：`.harness/skills/request-analysis/SKILL.md` 不再含 "无 remote 项目（本仓库当前情况）" 措辞；L289 附近段落改为统一"首选 `git diff --stat origin/main..HEAD`；离线 / 异常时降级 `git log --stat <baseline>..HEAD`"。
- **AC-2** static：`.harness/skills/expert-reviewer/SKILL.md` 不再含 "（或 `git log --stat <baseline>..HEAD` 无 remote 时）" 条件分支；L172 附近统一 `git diff --stat origin/main..HEAD`。
- **AC-3** static：`.harness/rules/development-process.md` stage 7 §产出物含 `git push origin main`（字面），§Quality Gate 含"`git status` 显示 `up to date with 'origin/main'`"或等价短语。
- **AC-4** static：`.harness/rules/development-process.md` stage 8 §self-attest 模板措辞含 "本项目策略" + "本地 pytest" + "self_check.sh" 三个关键词；不再含 "无 remote 长期未决"。
- **AC-5** static：`.gitignore` 含 `.claude/`（独立一行；可附行内注释）。
- **AC-6** static：`.github/workflows/ci.yml` 文件**不存在**（`test ! -f .github/workflows/ci.yml`）；`.github/workflows/` 目录可空或不存在。
- **AC-7** static：`scripts/_self_check.sh` 不含 ci.yml 检查（`! grep -q ".github/workflows/ci.yml" scripts/_self_check.sh`）；bootstrap-monorepo block 的 AC-15 row 整体删除（不再有 `run_ac AC-15 "ci.yml 合法 + 5 job + concurrency"` 这行）。
- **AC-8** **behavioral**：`bash scripts/_self_check.sh` 全跑（main 调用链含 bootstrap-monorepo / reviewer-lint / ac-kind-lint / 既有所有 block）退码 0，未引回归。

## 非范围

- 不引入 PR 流程；继续允许直 push main。
- 不动 5 个既有 closed change 的"CI 验证 self-attest"标记（历史记录）。
- 不重新启用任何形式的远程 CI（项目策略明示拒绝）。
- 不修 repo-files-tab-v2 复盘中 3 个 follow-up（独立解耦）：`harness-route-schema-callsite-audit-*` / `harness-test-grep-strip-ansi-*` / `harness-reviewer-no-summary-edit-*`。
- 不改 bootstrap-monorepo spec.md / tasks.md 自身（AC-15 历史 spec 内容不动；只在 self_check 层撤销其检查 + 在 summary 复盘里登记本 change 反向了它）。
- 不更新 wiki / design.md 中 CI 拓扑描述（如有，下次 wiki 维护轮次清理）。

## 验收标准

`kind` 二分：static / behavioral。

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | request-analysis SKILL 不含"无 remote 项目（本仓库当前情况）" + 含 "origin/main" 描述 | `! grep -q "无 remote 项目" .harness/skills/request-analysis/SKILL.md && grep -q "origin/main" .harness/skills/request-analysis/SKILL.md` | 反向 grep 0 命中 + 正向 grep 命中 |
| AC-2 | static | expert-reviewer SKILL 不含"无 remote 时" + 含 "origin/main" | `! grep -q "无 remote 时" .harness/skills/expert-reviewer/SKILL.md && grep -q "origin/main" .harness/skills/expert-reviewer/SKILL.md` | 反向 0 + 正向命中 |
| AC-3 | static | development-process stage 7 含 "git push origin main" + "up to date with" | `awk '/^## 阶段 7/{p=1;next} p && /^## 阶段 /{exit} p' .harness/rules/development-process.md \| grep -q "git push origin main" && awk '/^## 阶段 7/{p=1;next} p && /^## 阶段 /{exit} p' .harness/rules/development-process.md \| grep -q "up to date with"` | 2 grep 全命中 |
| AC-4 | static | development-process stage 8 §self-attest 段含 "本项目策略" + "本地 pytest" + "self_check"（新增内容）+ 防回归断言：全文不含 "无 remote 长期未决"（既有 stage 8 已无此措辞；本断言确保未来不重新引入）| `awk '/^## 阶段 8/{p=1;next} p && /^## 阶段 /{exit} p' .harness/rules/development-process.md \| grep -q "本项目策略" && awk '/^## 阶段 8/{p=1;next} p && /^## 阶段 /{exit} p' .harness/rules/development-process.md \| grep -q "本地 pytest" && awk '/^## 阶段 8/{p=1;next} p && /^## 阶段 /{exit} p' .harness/rules/development-process.md \| grep -q "self_check" && ! grep -q "无 remote 长期未决" .harness/rules/development-process.md` | 3 正向命中 + 1 全文反向 grep 0 命中（防回归）|
| AC-5 | static | .gitignore 含 `.claude/` 行 | `grep -qE "^\.claude/" .gitignore` | 命中 |
| AC-6 | static | ci.yml 不存在 | `test ! -f .github/workflows/ci.yml` | exit 0（文件不存在）|
| AC-7 | static | self_check.sh 不再含 ci.yml 检查（反向 grep）+ 不再有 `AC-15.*ci.yml` row | `! grep -q ".github/workflows/ci.yml" scripts/_self_check.sh && ! grep -qE "run_ac AC-15.*ci\.yml" scripts/_self_check.sh` | 2 反向 grep 全过 |
| AC-8 | **behavioral** | self_check 全跑退码 0（含 bootstrap-monorepo block 在 AC-15 删除后 PASS；含全仓 reviewer-lint + ac-kind-lint；不限制 tail 防 SKIP 干扰）| `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh 2>&1 \| tee /tmp/dataplat-selfcheck-all.log >/dev/null; grep -qE "^FAIL: 0\$" /tmp/dataplat-selfcheck-all.log` | log 内出现 "FAIL: 0" 行（即便有 SKIP 也不影响匹配）|

**Behavioral AC：AC-8**（真跑 self_check 全链路）。

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 删 ci.yml 后某处仍引用（grep 漏） | 中 | 低 | AC-7 反向 grep 实际跑；spawn reviewer 复核 |
| bootstrap-monorepo block 删 AC-15 后总 AC 数变 17 而文件其他位置仍说 18 | 中 | 低 | reviewer 实读 self_check L100-200 bootstrap block 注释 + 入口 echo 修正；本 change 顺手改 |
| `.gitignore` 加 `.claude/` 会让既有 untracked `.claude/` 永久不可见 | 低 | 低 | 副作用预期（用户已表态 .claude 不应推） |
| repo-files-tab-v2 等既有 closed change 的 summary "CI 验证 self-attest" 措辞引用"无 remote"，与本 change 撤销该说法冲突 | 中 | 低 | 不动既有 closed change（历史记录）；本 change spec 明示"只改未来" |
| ci.yml 第一次 push 已触发 CI 跑，删除文件后 GitHub Actions 历史保留红叉 | 低 | 低 | 接受历史记录；后续 push 不触发新 run（文件不存在）|

## 受影响模块

- `.harness/skills/request-analysis/SKILL.md`：1 段改写
- `.harness/skills/expert-reviewer/SKILL.md`：1 行修
- `.harness/rules/development-process.md`：stage 7 加 push 步骤 + stage 8 self-attest 模板改写
- `.gitignore`：加 1 行
- `.github/workflows/ci.yml`：**删除**
- `.github/workflows/`：可能整目录删（如无其他文件）
- `scripts/_self_check.sh`：删 bootstrap AC-15 row（L132-133 + 块头注释 AC 计数）

## 不受影响

- 5 个既有 closed change 的 summary / coding_report（含 CI 验证 self-attest 措辞）：历史记录不动
- `.harness/changes/bootstrap-monorepo-20260516/request_analysis/spec.md` AC-15：原始 spec 不改写
- repo-files-tab-v2 复盘中 3 个流程级 follow-up：独立解耦
- wiki / design.md：未来 wiki 维护轮次清理

## 引用

- `.harness/changes/bootstrap-monorepo-20260516/request_analysis/spec.md` L49 AC-15（被撤销项）
- `scripts/_self_check.sh` L132-133（被删 grep）
- `.harness/changes/repo-files-tab-v2-20260518/summary.md` §复盘（触发本 change 的上下文）
- `.harness/skills/request-analysis/SKILL.md` § AC 分层规约
