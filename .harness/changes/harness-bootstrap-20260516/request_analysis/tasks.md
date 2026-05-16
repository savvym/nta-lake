---
change_id: harness-bootstrap-20260516
version: 1
authored_at: 2026-05-16T03:10:00Z
---

# Tasks

> 本变更为追溯式记录：所有 T-* 任务在 spec 写定前已实际完成。状态填 `done` 并补 commits 字段（仓库尚未 git init，故 commits 暂留空，stage 7 推送时补）。

## 任务清单

```yaml
tasks:
  - id: T-1
    title: 写顶层 CLAUDE.md，定义会话入口与硬性约束
    description: |
      产出 `CLAUDE.md`，必须包含：项目背景一句话、Application Owner Agent 路径、
      关键文件导航表、6 条硬性约束、当前项目状态说明。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: done
    commits: []

  - id: T-2
    title: 写 .harness/agents/application-owner.md
    description: |
      Application Owner Agent 定义文件，必须包含：角色定位、项目背景速览、
      Rules/Skills/Wiki/MCP 配置索引、工作流调度（任务起点、阶段推进、Generator/Reviewer 分离、summary.md SSOT）、
      沟通原则、硬性约束、新变更启动模板化指引。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-2]
    status: done
    commits: []

  - id: T-3
    title: 写 .harness/README.md（harness 自身导航）
    description: 列出 .harness/ 目录约定与分层加载策略，作为 harness 入口。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-11]      # 仅被"文件非空"兜底；spec 未为 .harness/README.md 单列 AC（review v1 SHOULD FIX #1 调整）
    status: done
    commits: []

  - id: T-4
    title: 写 .harness/rules/development-process.md
    description: |
      完整定义十阶段开发流程，每个阶段 4 要素（Entry / Skill / Quality Gate / Rollback）齐全；
      末尾给典型回退路径速查表与跨阶段约束。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-3, AC-4]
    status: done
    commits: []

  - id: T-5
    title: 写 .harness/rules/engineering-structure.md
    description: 落实 design.md §11.3 的 monorepo 结构，明确强约束、命名规则、新增目录/包/plugin 的门槛。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-3]
    status: done
    commits: []

  - id: T-6
    title: 写 .harness/rules/coding-style.md
    description: |
      Python / TS / SQL / Git / LLM 调用 / 安全 / 性能 共 7 大类风格底线。
      每条都要可被代码评审引用。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-3]
    status: done
    commits: []

  - id: T-7
    title: 写 9 个 .harness/skills/<name>/SKILL.md
    description: |
      request-analysis / coding-skill / expert-reviewer / unit-test-write / unit-test-ci /
      deploy-verify / code-review / project-analysis / ci-generate。
      每个 SKILL.md 含：YAML frontmatter（name/description/applicable_stage/inputs/outputs）+
      进入条件 + 输入 + 步骤 + 产出 + 质量门禁 + 失败回退 + 反模式。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-5, AC-10]
    status: done
    commits: []

  - id: T-8
    title: 写 .harness/skills/README.md（Skill 索引）
    description: 提供 Skill 概览表 + Skill 之间的关系图 + 新 Skill 约定。
    depends_on: [T-7]
    estimated_stage: coding
    covers_ac: [AC-5]
    status: done
    commits: []

  - id: T-9
    title: 写 .harness/changes/_template/ 全套变更模板
    description: |
      含 summary.md / request_analysis/{spec.md,tasks.md,review/*.md} /
      coding/{coding_report_v1.md,review/code_review_v1.md} /
      unit_test/{test_report_v1.md,review/test_review_v1.md} /
      ci_result/ci_result_v1.md / deployment/deploy_verify_v1.md / README.md。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-6]
    status: done
    commits: []

  - id: T-10
    title: 写 .harness/changes/README.md
    description: 变更命名约定 / 启动流程 / 子目录结构 / summary.md 作用 / 版本号约定 / 关闭条件。
    depends_on: [T-9]
    estimated_stage: coding
    covers_ac: [AC-7]
    status: done
    commits: []

  - id: T-11
    title: 写 .harness/mcp/README.md（Phase 0 占位）
    description: 标注当前状态 / 何时启用 / 落地约定（先 ADR、secret 不入库）/ 不要做的事。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-8]
    status: done
    commits: []

  - id: T-12
    title: 写 wiki/ 全套
    description: README + architecture.md（顶层组件 / 目录映射 / 关键链路 / 数据模型 / CI / 部署拓扑 / 漂移记录）+ domain-glossary.md（核心术语全列）+ adr/README.md（ADR 模板与工作流）。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-9]
    status: done
    commits: []

  - id: T-13
    title: 写入项目记忆
    description: |
      MEMORY.md 索引 + project_overview.md（项目当前 Phase 0、技术栈、用户选择）+
      harness_constraints.md（流程硬约束 feedback）+ feedback_doc_language.md（中文为主）。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-12]
    status: done
    commits: []
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: pending      # 等待独立 Reviewer 子会话

  - id: P-code-review
    estimated_stage: coding_review
    status: pending      # 追溯式：评审已落地的骨架文件本身

  - id: P-test-write
    estimated_stage: unit_test
    status: pending      # 计划用 shell 自检脚本充当"测试"，验证 12 条 AC

  - id: P-test-review
    estimated_stage: unit_test_review
    status: pending

  - id: P-push
    estimated_stage: push
    status: pending
    blocked_by: 仓库尚未 git init；推送到远端可后置评估是否本变更内做（review v1 SHOULD FIX #2 字段对齐）

  - id: P-ci
    estimated_stage: ci_result
    status: skipped
    reason: 本变更不引入 CI 配置；CI 由 bootstrap-monorepo 中的 ci-generate Skill 产出

  - id: P-deploy
    estimated_stage: deployment
    status: skipped
    reason: 纯文档变更，无部署面

  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG 健全性

依赖：

- T-8 → T-7（索引依赖 9 个 SKILL）
- T-10 → T-9（changes/README 依赖 _template 已建好）
- 其余 T-* 互相独立

P-* 阶段任务按 development-process.md 顺序流转，无内部循环。

## 验收覆盖矩阵

| AC | 关联任务 |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3 | T-4, T-5, T-6 |
| AC-4 | T-4 |
| AC-5 | T-7, T-8 |
| AC-6 | T-9 |
| AC-7 | T-10 |
| AC-8 | T-11 |
| AC-9 | T-12 |
| AC-10 | T-7 |
| AC-11 | 全部 T-*（特别地，T-3 仅由 AC-11 覆盖） |
| AC-12 | T-13 |

> 每条 AC 都至少有一个 T-* 关联，无孤立 AC。
