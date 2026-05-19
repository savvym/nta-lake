# 开发流程规则：十阶段

本文件是项目唯一的流程权威。Application Owner Agent 严格按此推进任何变更。

## 总览

```text
需求分析 → 需求评审 → 编码实现 → 编码评审 → 单测编写 → 单测评审
       → 代码推送 → CI 验证 → 部署验证 → 用户确认
```

每个阶段定义四要素：

- **Entry Criteria**：满足才能进入此阶段。
- **Skill Injection**：进入时加载哪个 `.harness/skills/<name>/SKILL.md`。
- **Quality Gate**：通过判定标准（必须可程序化或可机械化校验）。
- **Rollback Route**：失败时回退到哪个阶段。

所有产物按 `.harness/changes/<change-id>/` 下的对应子目录归档；`summary.md` 实时反映当前阶段与门禁状态。

### 自检分层

- **阶段内快检**：`bash scripts/_self_check.sh quick [change-id]`，只跑 reviewer/ac-kind 轻量守门和阶段产物 preflight。
- **当前 change 检查**：`bash scripts/_self_check.sh current [change-id]`，等价于 quick + 当前 change 已注册的 AC block；新 change 尚未注册 block 时只记 SKIP，不阻塞阶段内迭代。
- **最终门禁**：`bash scripts/_self_check.sh full`，跑全部历史回归。无参数入口为兼容旧流程，等价于 `full`，不要在阶段内循环使用。
- 全量 `ruff` / `mypy` / web build / 历史回归默认放到阶段 8；阶段 3/5 只跑与本次改动面直接相关的最小命令集。

### Git 边界

- 每个 change 只对应一个 `change/<change-id>` 分支。
- 每个阶段 Quality Gate 通过后提交一次该阶段产物，并把 commit SHA 记录到 `summary.md`。
- 阶段之间评估改动优先用 `git diff <上一阶段commit>...HEAD`；reviewer 不再靠人工翻历史文件判断增量。

---

## 阶段 1 · 需求分析（request_analysis）

- **Entry Criteria**：用户已提出明确诉求；已通过 `bash scripts/harness_new_change.sh <change-id> [title]` 创建 `.harness/changes/<change-id>/` 并切到 `change/<change-id>` 分支。
- **Skill Injection**：`skills/request-analysis/SKILL.md`。
- **产出物**：
  - `request_analysis/spec.md`：背景、问题陈述、范围、非范围、验收标准、风险。
  - `request_analysis/tasks.md`：任务拆解清单（含依赖关系、预计阶段）。
- **Quality Gate**：
  - `spec.md` 存在且包含必填章节：背景 / 范围 / 非范围 / 验收标准 / 风险。
  - 验收标准每一条都**可机械化或可演示验证**（不允许 "用户感觉良好"）。
  - `tasks.md` 任务粒度足够细：每个任务能在 1-3 小时内完成。
- **Rollback Route**：本阶段是起点，失败即终止变更或回到与用户的对话。

## 阶段 2 · 需求评审（request_analysis/review）

- **Entry Criteria**：阶段 1 产物齐全。
- **Skill Injection**：`skills/expert-reviewer/SKILL.md`（plan 模式）。
- **执行者要求（硬约束）**：**必须由独立 reviewer agent 执行**；不允许同一会话同时扮演 generator 与 reviewer（self-review）；Application Owner 通过 `Agent(subagent_type="general-purpose", ...)` spawn 子 agent。详见 `.harness/agents/application-owner.md` § 7.5 spawn 模板 + `.harness/agents/reviewer-agent.md` + `.harness/skills/expert-reviewer/SKILL.md` § reviewer 字段填写规约。违反者被 `scripts/_self_check.sh` `run_reviewer_lint` 硬 FAIL。
- **产出物**：
  - `request_analysis/review/spec_review_v{N}.md`
  - `request_analysis/review/tasks_review_v{N}.md`
  - 每份 review 必须有 `verdict: APPROVED | REVISION REQUIRED`，且 MUST FIX 项有具体行号引用。
  - reviewer 字段必须以 `claude-agent:` 起头（真 spawn 子 agent ID）或 `self-attest (<理由>)`（显式偏离声明）；裸 `application-owner-agent` 等价 self-review，被 lint 硬 FAIL。
- **Quality Gate**：
  - 评审报告存在且包含必填章节。
  - 所有 MUST FIX 已在新 spec/tasks 版本中关闭。
  - 最终一轮 verdict = APPROVED。
  - reviewer 字段合规（白名单 `claude-agent:` 或 `self-attest (...)`）。
- **Rollback Route**：REVISION REQUIRED → 回到阶段 1。

## 阶段 3 · 编码实现（coding）

- **Entry Criteria**：阶段 2 verdict = APPROVED；`engineering-structure.md` 与 `coding-style.md` 已加载。
- **Skill Injection**：`skills/coding-skill/SKILL.md`。
- **产出物**：
  - 实际代码改动（在 dataplat 代码区或 plugins/）。
  - `coding/coding_report_v{N}.md`：改了哪些文件、为何这样改、tasks.md 中对应任务状态。
- **Quality Gate**：
  - 改动文件清单与 `tasks.md` 任务对得上（每个任务有对应改动或显式标记 "deferred 见 xxx"）。
  - 本地最小校验通过：与本次改动面直接相关的 lint / type check / 测试为 0 错误，并通过 `bash scripts/_self_check.sh current <change-id>`。
  - 没有引入未在 spec 中授权的依赖或目录。
- **Rollback Route**：
  - 编译/类型错误未修 → 留在本阶段。
  - 发现 spec 缺失或自相矛盾 → 回阶段 1。

## 阶段 4 · 编码评审（coding/review）

- **Entry Criteria**：阶段 3 Quality Gate 通过。
- **Skill Injection**：`skills/code-review/SKILL.md`。
- **执行者要求（硬约束）**：**必须由独立 reviewer agent 执行**；不允许同一会话同时扮演 generator 与 reviewer（self-review）；Application Owner 通过 `Agent(subagent_type="general-purpose", ...)` spawn 子 agent。详见 `.harness/agents/application-owner.md` § 7.5 spawn 模板 + `.harness/agents/reviewer-agent.md`。违反者被 `scripts/_self_check.sh` `run_reviewer_lint` 硬 FAIL。
- **产出物**：
  - `coding/review/code_review_v{N}.md`：分类标 MUST FIX / SHOULD FIX / NICE TO HAVE，verdict。
  - reviewer 字段必须以 `claude-agent:` 起头或 `self-attest (<理由>)`；裸 `application-owner-agent` 被 lint 硬 FAIL。
- **Quality Gate**：
  - 评审报告存在；所有 MUST FIX 已关闭；最终一轮 verdict = APPROVED。
  - SHOULD FIX 若有未关闭项，须在 `summary.md` 显式说明 deferred 原因和跟进位置。
  - reviewer 字段合规。
- **Rollback Route**：REVISION REQUIRED → 回阶段 3。

## 阶段 5 · 单测编写（unit_test）

- **Entry Criteria**：阶段 4 通过。
- **Skill Injection**：`skills/unit-test-write/SKILL.md`。
- **产出物**：
  - 测试代码（与改动同 PR）。
  - `unit_test/test_report_v{N}.md`：测试用例清单、覆盖的 spec 验收项、本地运行结果。
- **Quality Gate**：
  - **改动驱动**：本次改动新增/修改的每一个公共函数或路由，至少有一条直接测试。
  - 本地 `pytest` / `vitest` 全部通过；测试数 > 0。
  - 测试**不允许**对核心数据访问层做无条件 mock（详见 `coding-style.md` §测试）。
- **Rollback Route**：本地测试失败 → 留在阶段 5 或回阶段 3。

## 阶段 6 · 单测评审（unit_test/review）

- **Entry Criteria**：阶段 5 Quality Gate 通过。
- **Skill Injection**：`skills/expert-reviewer/SKILL.md`（artifact 模式）。
- **执行者要求（硬约束）**：**必须由独立 reviewer agent 执行**；不允许同一会话同时扮演 generator 与 reviewer（self-review）；Application Owner 通过 `Agent(subagent_type="general-purpose", ...)` spawn 子 agent。详见 `.harness/agents/application-owner.md` § 7.5 spawn 模板 + `.harness/agents/reviewer-agent.md`。违反者被 `scripts/_self_check.sh` `run_reviewer_lint` 硬 FAIL。
- **产出物**：
  - `unit_test/review/test_review_v{N}.md`
  - reviewer 字段必须以 `claude-agent:` 起头或 `self-attest (<理由>)`；裸 `application-owner-agent` 被 lint 硬 FAIL。
- **Quality Gate**：
  - 每条 spec 验收标准都能追溯到具体测试用例（review 报告列出映射表）。
  - 没有"空跑"测试（断言空、只 assert True、把异常 swallow）。
  - verdict = APPROVED。
  - reviewer 字段合规。
- **Rollback Route**：REVISION REQUIRED → 回阶段 5。

## 阶段 7 · 代码推送（push）

- **Entry Criteria**：阶段 6 通过；本地 git 状态干净（无未追踪的应入库文件）。
- **Skill Injection**：无（直接 git 操作）。
- **产出物**：
  - 已按阶段形成的一组 commit；推送到远端分支。
  - `git push -u origin change/<change-id>`；禁止将未完成 change 直接推到 `main`。
  - `summary.md` 更新 commit SHA、分支名。
- **Quality Gate**：
  - commit message 遵循约定（详见 `coding-style.md` §git）。
  - 当前分支名匹配 `change/<change-id>`。
  - `git status` 显示当前分支 up to date with `origin/change/<change-id>`（验证本地与 remote 同步）。
- **Rollback Route**：
  - 推送失败（鉴权 / 网络）→ 检查 ssh-agent / remote URL，重试；不解决前不进入下一阶段。
  - 推送被拒（remote 有新 commit 未 pull）→ `git pull --rebase` 解决冲突后重试。

## 阶段 8 · CI 验证（ci_result）

- **Entry Criteria**：阶段 7 完成。
- **本项目策略（self-attest 默认）**：**本地 pytest + `bash scripts/_self_check.sh full` 等价 CI**；**不引入 GitHub Actions / GitLab CI 等远程 CI**（理由：等价覆盖 + 反馈快 + 单作者无 PR review 摩擦）。新 change 标 stage 8 = `self-attest` 时**必须**引用本节理由文案（"本项目策略：本地 pytest + self_check.sh full 等价 CI..."）；**禁用**早期"无远程"系列旧理由（详 `harness-remote-push-onboarding-20260518` 撤销说明）。
- **Skill Injection**：`skills/unit-test-ci/SKILL.md`（仅当未来引入远程 CI 时启用）。
- **产出物**（仅在引入远程 CI 时）：
  - `ci_result/ci_result_v{N}.md`：CI 运行链接、status、total_tests、passed_tests、failed_tests、coverage（如有）。
  - self-attest 路径：在 `summary.md` 阶段 8 行填 `self-attest`，notes 引用本节策略。
- **本地等价 CI 命令**：`bash scripts/_self_check.sh full` 必须通过；如本 change 涉及 Python/TS 代码，还需跑对应 workspace 的全量 lint/typecheck/build/test 命令并记录结果。
- **Quality Gate**（**机械化**，仅远程 CI 路径）：
  ```text
  status == SUCCESS
  total_tests > 0
  passed_tests == total_tests
  ```
- **Rollback Route**：
  - 失败属于代码 bug → 回阶段 3。
  - 失败属于测试 bug → 回阶段 5。
  - 失败属于 CI 配置 → 走 `ci-generate` Skill 修配置，可能开独立子变更。

## 阶段 9 · 部署验证（deployment）

- **Entry Criteria**：阶段 8 通过；变更涉及部署面（API、worker、web、plugin 镜像之一）。
- **Skill Injection**：`skills/deploy-verify/SKILL.md`。
- **产出物**：
  - `deployment/deploy_verify_v{N}.md`：环境、部署版本、验证步骤、验证证据（请求/响应、UI 截图、日志摘录）。
- **Quality Gate**（**硬约束，harness-ac-behavioral-tier-20260518 引入**）：

  > 实证背景：`pipeline-orchestrator-mvp-20260518` stage 9 第一次真跑端到端 demo 抓到 3 个真 bug。如果允许 verdict=deferred 或证据空，这种价值就会被绕过。

  - **(i) 默认**：`verdict: PASS`。`deployment/deploy_verify_v{N}.md` frontmatter `verdict` 字段非空且不为 `deferred` / `FAIL` / `unknown`。
  - **(ii) 替代路径**：允许 `verdict: PASS via self-attest (理由)`，但**必填 4 字段**（缺一不可）：
    - `理由`：一句话说明为什么用 self-attest（如"纯 harness 无部署面"、"本机已跑通但无 staging"）。
    - `本机证据列表`：命令输出路径或粘贴块（如 `/tmp/dataplat-dev-logs/evidence/` 下文件清单 + 关键输出片段）。
    - `跑过的命令`：bash 历史 / 命令列表（如 `bash scripts/lint/test_ac_kind_lint_fixture.sh`、`curl -X POST .../healthz` 等）。
    - `时间`：ISO8601 UTC。
  - **(iii) 禁止纯 `deferred`**：无 self-attest 或证据空 = self_check FAIL（未来 follow-up `harness-stage9-lint-*` 机械化此约束）。
  - **(iv) AC 真实性**：deploy_verify_v{N}.md 至少 1 条 AC 与 `request_analysis/spec.md` 的 `kind: behavioral` AC 对应（详见 `.harness/skills/request-analysis/SKILL.md` § "AC 分层规约"）。

  其他原有约束保留：
  - 关键验证步骤每一条都有具体证据。
  - 涉及数据库迁移的变更：迁移前后的 schema 对比、回滚脚本验证。
  - 不留 "应该没问题" 类自然语言结论。

- **self-attest 模板片段**（粘贴到 deploy_verify_v{N}.md frontmatter / 第一节）：

  ```yaml
  ---
  change_id: <feature-slug>-<yyyymmdd>
  version: 1
  env: dev | staging | prod
  deployed_at: <YYYY-MM-DDTHH:MM:SSZ>
  commit_sha: <sha>
  verifier: claude-agent:<change-id>-stage9-verifier-v1
  verdict: PASS via self-attest (理由：一句话)
  self_attest:
    理由: <复述 + 链接到本机证据>
    本机证据列表:
      - /tmp/dataplat-dev-logs/evidence/01-foo.txt
      - /tmp/dataplat-dev-logs/evidence/02-bar.json
    跑过的命令:
      - "bash scripts/lint/test_xxx_fixture.sh"
      - "curl -X POST http://127.0.0.1:8080/foo ..."
    时间: 2026-05-18T08:00:00Z
  ---
  ```

- **Rollback Route**：失败 → 回到对应实现或 CI 阶段；线上若已部署需附回滚步骤。

## 阶段 10 · 用户确认（user_confirmation）

- **Entry Criteria**：阶段 9 通过（无部署面则阶段 8 通过即可）。
- **Skill Injection**：无（与提出方对齐）。
- **产出物**：
  - `summary.md` 末段补上：用户确认时间、确认人、最终交付链接、关闭决议。
- **Quality Gate**：
  - 用户明确确认（不接受 "没有反对意见 = 默认通过"）。
- **Rollback Route**：用户提出新问题 → 视性质开新 change 或回到对应阶段做新一轮。

---

## 典型回退路径（速查）

| 触发场景 | 回退到 |
|---|---|
| spec 不清晰 / 自相矛盾 | 阶段 1 需求分析 |
| spec/tasks 评审不通过 | 阶段 1 需求分析 |
| 代码评审不通过 | 阶段 3 编码 |
| 单测为 0 或未覆盖关键路径 | 阶段 5 单测编写 |
| 编译/类型错误 | 阶段 3 编码 |
| 测试 mock 滥用被评审打回 | 阶段 5 单测编写 |
| CI 失败（代码 bug） | 阶段 3 编码 |
| CI 失败（CI 配置 bug） | 触发 `ci-generate` Skill |
| 部署验证不通过 | 视失败位置回到阶段 3/5/8 |
| 用户最终验收拒绝 | 视性质回到阶段 1 或开新 change |

---

## 跨阶段约束

1. **`summary.md` 实时更新**。每个阶段开始/通过/失败都要同步。
2. **review 版本号永远递增**。`spec_review_v1.md` 不通过 → 不要覆盖，写 `spec_review_v2.md`。
3. **多轮评审之间**：Generator 阶段产物也要新版本（`spec_v2.md` 等），保留历史。
4. **小变更不裁剪阶段**。可以让某些阶段产物极简（一两句话），但**不能不存在**。
5. **跨 change 依赖**：如果当前 change 依赖另一个未完成 change 的产物，在 `summary.md` 显式声明依赖与等待状态，不要在 `tasks.md` 偷偷绕过。
