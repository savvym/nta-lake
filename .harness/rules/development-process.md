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

---

## 阶段 1 · 需求分析（request_analysis）

- **Entry Criteria**：用户已提出明确诉求；`.harness/changes/<id>/` 目录已创建并复制自 `_template/`。
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
- **执行者要求**：**与阶段 1 不同的 Agent / 子会话**，避免自审。
- **产出物**：
  - `request_analysis/review/spec_review_v{N}.md`
  - `request_analysis/review/tasks_review_v{N}.md`
  - 每份 review 必须有 `verdict: APPROVED | REVISION REQUIRED`，且 MUST FIX 项有具体行号引用。
- **Quality Gate**：
  - 评审报告存在且包含必填章节。
  - 所有 MUST FIX 已在新 spec/tasks 版本中关闭。
  - 最终一轮 verdict = APPROVED。
- **Rollback Route**：REVISION REQUIRED → 回到阶段 1。

## 阶段 3 · 编码实现（coding）

- **Entry Criteria**：阶段 2 verdict = APPROVED；`engineering-structure.md` 与 `coding-style.md` 已加载。
- **Skill Injection**：`skills/coding-skill/SKILL.md`。
- **产出物**：
  - 实际代码改动（在 dataplat 代码区或 plugins/）。
  - `coding/coding_report_v{N}.md`：改了哪些文件、为何这样改、tasks.md 中对应任务状态。
- **Quality Gate**：
  - 改动文件清单与 `tasks.md` 任务对得上（每个任务有对应改动或显式标记 "deferred 见 xxx"）。
  - 本地 lint / type check 通过（`ruff check`、`mypy`、`tsc --noEmit`、`pnpm lint` 按 stack 适用）。
  - 没有引入未在 spec 中授权的依赖或目录。
- **Rollback Route**：
  - 编译/类型错误未修 → 留在本阶段。
  - 发现 spec 缺失或自相矛盾 → 回阶段 1。

## 阶段 4 · 编码评审（coding/review）

- **Entry Criteria**：阶段 3 Quality Gate 通过。
- **Skill Injection**：`skills/code-review/SKILL.md`。
- **执行者要求**：与阶段 3 不同的 Agent / 子会话。
- **产出物**：
  - `coding/review/code_review_v{N}.md`：分类标 MUST FIX / SHOULD FIX / NICE TO HAVE，verdict。
- **Quality Gate**：
  - 评审报告存在；所有 MUST FIX 已关闭；最终一轮 verdict = APPROVED。
  - SHOULD FIX 若有未关闭项，须在 `summary.md` 显式说明 deferred 原因和跟进位置。
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
- **Skill Injection**：`skills/expert-reviewer/SKILL.md`（review 模式）。
- **执行者要求**：与阶段 5 不同的 Agent / 子会话。
- **产出物**：`unit_test/review/test_review_v{N}.md`。
- **Quality Gate**：
  - 每条 spec 验收标准都能追溯到具体测试用例（review 报告列出映射表）。
  - 没有"空跑"测试（断言空、只 assert True、把异常 swallow）。
  - verdict = APPROVED。
- **Rollback Route**：REVISION REQUIRED → 回阶段 5。

## 阶段 7 · 代码推送（push）

- **Entry Criteria**：阶段 6 通过；本地 git 状态干净（无未追踪的应入库文件）。
- **Skill Injection**：无（直接 git 操作）。
- **产出物**：
  - 一次或多次 commit；推送到远端分支。
  - `summary.md` 更新 commit SHA、分支名。
- **Quality Gate**：
  - commit message 遵循约定（详见 `coding-style.md` §git）。
  - 不在 `main` / `master` 上直接 push（除非项目策略允许且明示）。
- **Rollback Route**：推送失败 → 解决冲突、回到对应改动阶段。

## 阶段 8 · CI 验证（ci_result）

- **Entry Criteria**：阶段 7 完成且远端 CI 已触发。
- **Skill Injection**：`skills/unit-test-ci/SKILL.md`。
- **产出物**：
  - `ci_result/ci_result_v{N}.md`：CI 运行链接、status、total_tests、passed_tests、failed_tests、coverage（如有）。
- **Quality Gate**（**机械化**）：
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
- **Quality Gate**：
  - 关键验证步骤每一条都有具体证据。
  - 涉及数据库迁移的变更：迁移前后的 schema 对比、回滚脚本验证。
  - 不留 "应该没问题" 类自然语言结论。
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
