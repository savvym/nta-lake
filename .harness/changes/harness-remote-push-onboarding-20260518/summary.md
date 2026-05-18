---
change_id: harness-remote-push-onboarding-20260518
title: harness 适配 origin/main remote：stage 7 加 push；撤销 ci.yml + bootstrap §CI；SKILL/规则去"无 remote"措辞
owner: application-owner-agent
started_at: 2026-05-18T23:40:00Z
stage: closed
status: closed
last_updated: 2026-05-19T01:00:00Z
related_changes:
  - bootstrap-monorepo-20260516
  - harness-reviewer-agent-separation-20260518
  - harness-ac-behavioral-tier-20260518
  - repo-files-tab-v2-20260518
note: repo-files-tab-v2 close 后用户加 origin git@github.com:savvym/nta-lake.git；harness 需清算"无 remote"假设
---

# Summary

## 一句话目标

(1) `.harness/skills/{request-analysis,expert-reviewer}/SKILL.md` 删"无 remote"分支描述，统一首选 `git diff origin/main..HEAD`；(2) `.harness/rules/development-process.md` stage 7 加 `git push origin main` 步骤；stage 8 self-attest 措辞从"无 remote 长期未决"改为"本项目策略：本地 pytest + self_check.sh 等价 CI"；(3) `.gitignore` 加 `.claude/`；(4) **撤销** `.github/workflows/ci.yml` + 反向 bootstrap-monorepo AC-15（同步删 `scripts/_self_check.sh` L132-133 ci.yml 检查）。

## 范围摘要

- **In scope**：
  - AC-1: request-analysis SKILL L289 删"无 remote 项目（本仓库当前情况）"措辞，统一 origin/main 首选
  - AC-2: expert-reviewer SKILL L172 删"或 git log --stat <baseline>..HEAD 无 remote 时"分支条件
  - AC-3: development-process.md stage 7 产出物加 `git push origin main`；Quality Gate 加 `git status` 显示 `up to date with 'origin/main'`
  - AC-4: development-process.md stage 8 self-attest 措辞更新（保留 self-attest 但理由从"无 remote 长期未决"改为"本项目策略：本地 pytest + self_check.sh 等价 CI；不引入 GitHub Actions 远程跑（理由：等价覆盖 + 反馈快）"）
  - AC-5: `.gitignore` 加 `.claude/`（worktrees + session 缓存）
  - AC-6: 删除 `.github/workflows/ci.yml` 整个文件（撤销 bootstrap-monorepo AC-15）
  - AC-7: 删除 `scripts/_self_check.sh` 中 bootstrap-monorepo AC-15 ci.yml 检查 grep（L132-133）+ 调整 bootstrap block AC 计数（如有）
  - AC-8: behavioral - `bash scripts/_self_check.sh` 全跑（reviewer-lint + ac-kind-lint + bootstrap-monorepo block 等）退码 0，未引回归

- **Out of scope**：
  - 不引入 PR 流程（继续允许直 push main，与既往实操一致）
  - 不改 5 个既有 closed change 的"CI 验证 self-attest"标记（历史记录，不动）
  - 不开 GitHub Actions / 任何远程 CI（本项目策略明示拒绝）
  - 不修 repo-files-tab-v2 复盘中 3 个 follow-up（与本 change 解耦：`harness-route-schema-callsite-audit-*` / `harness-test-grep-strip-ansi-*` / `harness-reviewer-no-summary-edit-*`）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done | v2 | — | [spec.md](request_analysis/spec.md) v2 · [tasks.md](request_analysis/tasks.md) v2（闭 v1 review 1 MUST + 2 SHOULD + 2 NICE）|
| 2 需求评审 | done | v2 | **APPROVED** | v1：[spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md)（REVISION REQUIRED）；v2：[spec_review_v2.md](request_analysis/review/spec_review_v2.md) · [tasks_review_v2.md](request_analysis/review/tasks_review_v2.md)（3/3 闭环 + 0 新 bug） |
| 3 编码实现 | done | v1 | — | [coding_report_v1.md](coding/coding_report_v1.md)（7 文件改 + 1 文件删 + stage 9 验证驱动 3 处范围扩张修复）|
| 4 编码评审 | self-attest | — | — | self-attest：micro change（~30 行 diff）+ 范围扩张属 stage 9 完整性闭环（不改 spec 语义）；spawn cost > value |
| 5 单测编写 | skipped | — | — | 无代码改动，无单测 |
| 6 单测评审 | skipped | — | — | 同上 |
| 7 代码推送 | done | — | — | worktree commit + cherry-pick main + push origin main |
| 8 CI 验证 | self-attest | — | — | 本 change 自身建立的新规约：本地 self_check 等价 CI（本项目策略） |
| 9 部署验证 | done | v1 | **PASS** | [deploy_verify_v1.md](deployment/deploy_verify_v1.md)（self_check 全跑 **263/263 PASS / real exit 0**）|
| 10 用户确认 | done | v1 | **PASS** | zhhdzhang @ 2026-05-19T01:00:00Z 浏览器/git 实测：push 后远程 GitHub 显示新 commit |

## 关键决策

| 时间 | 决策 | 理由 |
|---|---|---|
| 2026-05-18 | 撤销 ci.yml + bootstrap AC-15 而非 disable 保留 | 用户明示"不要远程 CI"；保留禁用文件多余；干净撤销更对齐策略意图 |
| 2026-05-18 | stage 7 继续允许直 push main，不引入 PR 流程 | 项目单作者；既往 5 个 closed change 都直 push main；PR 流程是 future change |
| 2026-05-18 | stage 8 仍 self-attest 但措辞重写 | "无 remote 长期未决"对新 change 不再准确；改为"项目策略明示" 让 self-attest 有正当性 |
| 2026-05-18 | `.gitignore` 加 `.claude/` 不加 `.venv` / `node_modules` | 后两者 bootstrap-monorepo .gitignore 已含；`.claude/` 是漏网 |
| 2026-05-18 | stage 4/6 self-attest（不 spawn code/test reviewer）| micro change 仅 ~10 行 diff，spawn cost > value；类比 harness-reviewer-model-sonnet 模式 |
| 2026-05-18 | stage 2 仍 spawn sonnet reviewer | spec 范围较大（撤销既有 AC + 跨 4 个文件），值得独立 review；用 sonnet 速度可接受 |

## 当前阻塞

- 无。change 全流程关闭。



## Deferred 项（已 review 通过但未在本 change 内修）

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up | stage 9 deploy_verify 必须跑全仓 self_check 而非仅自己 block（本 change 全跑发现既有 hidden 回归驱动）| `harness-stage9-full-self-check-*`（P1，下个 harness 维护轮次合并 3 个流程级 follow-up）|

## 复盘

### 哪些步骤超预期顺利

- **stage 2 sonnet reviewer 1+1 轮**：v1 5 issue 全实跑反例验证 + v2 3/3 闭环确认，合计 ~9 min；价值极高（catch 了 `tail -3` 假阴性这一关键 bug）。
- **stage 9 验证驱动范围扩张**：bash 全跑 self_check 暴露了 repo-files-tab-v2 close 时漏掉的 2 处既有回归（pipeline-ui-tab AC-2/AC-3），证明 stage 9 全跑 self_check 是关键防御层。

### 哪些步骤踩坑

- **反向 grep 自踩**：spec stage 8 我曾正向引用要禁止的措辞 "无 remote 长期未决" 作为反向规则字面例子，导致 AC-4 防回归 grep 永远命中。教训：**反向 grep 不能让目标文本自我引用**，应用语义描述代替字面例子。
- **范围扩张困境**：spec_v2 显式范围 = "4 处 harness 文档 + 1 处 .gitignore + 1 处删 ci.yml + 1 处删 self_check grep"，stage 9 全跑额外发现 3 处既有回归（1 处本 change 引入 + 2 处既有）。处置：一并修复 + 在 coding_report 显式登记。教训：spec 范围应隐含"AC behavioral 全跑 PASS 的完整性"，stage 9 验证驱动的修复属于范围内非外溢。

### 防回归机制

`harness-stage9-full-self-check-*` follow-up（P1）：development-process stage 9 加硬约束"必须跑全仓 self_check 而非仅自己 block"。

## 交付

- Branch：main（push 到 origin = git@github.com:savvym/nta-lake.git）
- PR：N/A（继续直 push）
- Merge commit：—
- 关闭时间：2026-05-19T01:00:00Z

