# Harness Engineering 文章笔记

来源：[腾讯新闻：Harness Engineering：耗时一周，我是如何将应用的 AI Coding 率提升至 90% 的](https://news.qq.com/rain/a/20260507A020NO00)

发布时间：2026-05-07

发布账号：阿里技术

> 说明：本文档是基于原文整理的项目内参考笔记，不是原文全文转载。后续构建 `.harness/` 体系时，以本文档作为结构和流程参考。

## 1. 核心观点

文章讨论的是 AI Coding 从 Prompt Engineering、Context Engineering 演进到 Harness Engineering 的第三阶段。

Prompt Engineering 主要优化单次交互的提示词；Context Engineering 关注给 Agent 提供哪些上下文；Harness Engineering 则把 AI Coding 视为一个完整工程系统，围绕 Agent 构建约束、反馈、流程编排和持续改进机制。

原文给出的核心判断是：大型工程里，模型能力本身不是唯一瓶颈。Agent 往往能写出语法正确、风格统一的代码，但容易在业务语义、隐性约束、跨模块链路、测试验证和交付流程上出错。因此需要把团队经验、工程规范、工作流、质量门禁和变更追踪外部化、文件化、可执行化。

## 2. Harness Engineering 要解决的问题

文章总结了复杂项目中 Agent 的典型失败模式：

1. 试图在单个上下文里一次性完成复杂任务，导致上下文膨胀和输出质量下降。
2. 部分实现后过早宣布完成，没有真正通过编译、测试或端到端验证。
3. 功能看似完成，但没有覆盖真实业务路径。
4. 跨会话没有持久化记忆，每次都需要重新理解项目。
5. Agent 不能可靠评估自己的产出，需要外部评判机制。

对应的工程解法是：把 Agent 的工作环境设计成一个长期运行的系统，而不是一次聊天。

## 3. 四根支柱

### 3.1 上下文架构

Agent 不应该一次性加载所有文档，而应该加载当前任务刚好需要的内容。入口文件应像索引和地图，而不是百科全书。

推荐分层：

1. 常驻上下文：Agent 角色定义、核心规则、项目总览。
2. 阶段触发上下文：需求分析、编码、评审、测试、部署等阶段各自加载对应 Skill。
3. 按需查询上下文：业务 Wiki、链路文档、历史变更、接口说明等只在需要时查阅。

### 3.2 Agent 专业化

不要让一个通用 Agent 同时负责规划、编码和评判。更稳妥的方式是拆分角色：

1. Planner：理解需求、拆解任务、制定计划。
2. Generator：按计划实现代码和文档。
3. Evaluator：检查计划、实现、测试和交付证据。

执行者和评判者分离，是提升质量的关键杠杆。

### 3.3 持久化记忆

进度、决策、问题、评审结论不应只存在上下文窗口里，而应写入文件系统。每次新会话启动时，Agent 应先读取项目状态和变更摘要，再继续推进。

关键文件包括：

1. `summary.md`：当前变更的全流程摘要。
2. `spec.md`：需求分析和验收标准。
3. `tasks.md`：任务拆分和执行清单。
4. `review/*.md`：每一轮评审结论。
5. `ci_result/*.md`：CI、测试和验证结果。

### 3.4 结构化执行

Agent 不应在没有计划和质量门禁的情况下直接改代码。推荐流程是：

```text
理解需求 -> 规划方案 -> 执行实现 -> 验证结果 -> 记录反馈
```

每个阶段都应有进入条件、产出物、质量门禁和失败回退路径。

## 4. 文章中的 `.harness/` 四要素架构

原文将 Harness 落地为四类资产：

1. Rules：告诉 Agent 标准是什么。
2. Skills：告诉 Agent 应该怎么做。
3. Wiki：告诉 Agent 系统是什么样的。
4. Changes：记录 Agent 做了什么。

推荐项目结构：

```text
.harness/
  agents/
    application-owner.md
  rules/
    engineering-structure.md
    development-process.md
    coding-style.md
  skills/
    request-analysis/
    coding-skill/
    expert-reviewer/
    unit-test-write/
    unit-test-ci/
    deploy-verify/
    code-review/
    project-analysis/
    ci-generate/
  changes/
  mcp/
wiki/
```

## 5. Application Owner Agent

文章建议在 `.harness/agents/` 下定义一个 Application Owner Agent，作为整个开发流程的编排中枢。

这个 Agent 定义文件应包含：

1. 角色定位和项目背景。
2. Rules、Skills、Wiki、MCP 的配置索引。
3. 核心职责：需求理解、任务拆解、分发协调、验收、质量把关、文档维护、知识问答。
4. 工作流调度指令：每个阶段加载什么 Skill、产出什么文件、如何通过门禁、失败后回退到哪里。
5. 沟通原则和硬性约束：不能跳过需求理解、不能跳过验收、不能隐瞒问题、不能做无关重构。

Agent 文件的价值不在于堆满所有知识，而在于告诉 Agent 去哪里找知识、什么时候加载知识、如何推进流程。

## 6. 十阶段开发流程

文章中的完整流程可以整理为：

```text
需求分析
-> 需求评审
-> 编码实现
-> 编码评审
-> 单元测试编写
-> 单元测试评审
-> 代码推送
-> CI 验证
-> 部署验证
-> 用户确认
```

每个阶段应包含：

1. Entry Criteria：什么时候可以进入该阶段。
2. Skill Injection：该阶段加载哪个 Skill。
3. Quality Gate：该阶段通过的机械化条件。
4. Rollback Route：失败时回退到哪个阶段。

典型回退策略：

1. 需求不清晰：回到需求分析。
2. 计划评审不通过：回到需求分析或任务拆解。
3. 编码评审不通过：回到编码实现。
4. 单测为 0 或失败：回到单元测试编写。
5. 编译错误：回到编码实现。
6. 部署验证不通过：回到对应实现或配置阶段。

## 7. Skill 体系

Skill 本质上是可复用 SOP，用来把团队隐性知识显性化。

建议的 Skill 类型：

1. `request-analysis`：需求澄清、边界识别、验收标准、风险识别。
2. `coding-skill`：分层编码规范、接口实现、异常处理、依赖调用、数据访问。
3. `expert-reviewer`：计划评审和执行评审。
4. `unit-test-write`：改动驱动测试，基于真实接口和真实业务数据构造测试。
5. `unit-test-ci`：执行测试、校验测试数量、失败归因。
6. `deploy-verify`：部署参数确认、环境检查、验证证据收集。
7. `code-review`：代码风格、架构约束、潜在风险检查。
8. `project-analysis`：项目结构、链路、依赖、核心模块梳理。
9. `ci-generate`：生成或维护 CI 配置。

## 8. 变更管理

每个需求应在 `.harness/changes/` 下创建独立目录，记录从需求到交付的全过程。

推荐结构：

```text
.harness/changes/
  feature-example-20260516/
    summary.md
    request_analysis/
      spec.md
      tasks.md
      review/
        spec_review_v1.md
        tasks_review_v1.md
    coding/
      coding_report_v1.md
      review/
        code_review_v1.md
    unit_test/
      test_report_v1.md
      review/
        test_review_v1.md
    ci_result/
      ci_result_v1.md
    deployment/
      deploy_verify_v1.md
```

`summary.md` 是每个变更的 Single Source of Truth，记录当前阶段、评审轮次、关键决策、阻塞点、CI 状态和最终交付结论。

## 9. 质量门禁原则

文章强调：不能机械化验证的约束，在 Agent 执行中会逐渐失效。

因此，门禁要尽量写成可程序化检查的条件，例如：

```text
CI 通过条件：
status == SUCCESS
total_tests > 0
passed_tests == total_tests
```

评审报告通过条件：

```text
目标文件存在
包含必填章节
所有 MUST FIX 项已关闭
有明确结论：APPROVED 或 REVISION REQUIRED
```

变更完成条件：

```text
spec.md 存在且含验收标准
tasks.md 存在且任务全部关闭
coding_report 存在
unit_test_report 存在
ci_result 存在
summary.md 更新到最终状态
```

## 10. 关键经验

1. Harness 自身也要 Dry Run。先用虚拟需求完整跑一遍流程，修正流程缺陷。
2. 质量门禁必须可程序化验证，不能只写自然语言建议。
3. 执行与评判要分离，用 Reviewer Agent 检查 Generator Agent 的产出。
4. 流程一致性优先于短期效率，小需求也不应跳过关键阶段。
5. 规范是活文档，每次发现 Agent 犯错，都应该把防复发机制补回 Harness。

## 11. 效果数据

原文给出的实践结果是：引入 Harness 后，项目维度 AI 代码率从约 25% 提升到约 90%，个人维度也从约 14% 提升到约 88%。

文章同时强调，高 AI 代码率不是目标本身。真正有价值的是在需求分析、评审、单元测试、CI 和部署验证都可控的前提下，提高 AI 产出占比。

## 12. 对当前项目的启发

当前项目要构建 `.harness/` 体系时，可以优先落地以下内容：

1. `.harness/agents/application-owner.md`
2. `.harness/rules/development-process.md`
3. `.harness/rules/coding-style.md`
4. `.harness/rules/engineering-structure.md`
5. `.harness/skills/request-analysis/SKILL.md`
6. `.harness/skills/coding-skill/SKILL.md`
7. `.harness/skills/expert-reviewer/SKILL.md`
8. `.harness/skills/unit-test-write/SKILL.md`
9. `.harness/changes/_template/`
10. `wiki/`

第一版不需要追求完整自动化，先确保所有需求都有标准化的分析、计划、实现、评审、测试、CI 和交付记录。

