# CLAUDE.md

本项目正在按 **Harness Engineering** 范式开发。所有写代码、改代码、评审、测试、CI、部署的工作都必须走 `.harness/` 下定义的流程，**不要绕过**。

## 你的第一件事

进入本项目的任何会话，**先读 `.harness/agents/application-owner.md`**。它定义了：

- 你作为 Application Owner 的角色与硬性约束
- 当前应当加载的 Rules / Skills / Wiki 索引
- 十阶段开发流程的入口、产物、质量门禁与回退路径
- 任何任务的标准操作流程：先做需求分析 → 再写计划 → 评审 → 实现 → 评审 → 单测 → CI → 部署 → 用户确认

## 项目背景

目标系统是一个**面向 LLM 训练的数据管理平台**（Bronze/Silver/Gold 三层、类 Git 版本控制 + CAS、可插拔 Adapter/Processor、统一 LLM 网关）。完整设计见 [.harness/design.md](.harness/design.md)。

`.harness/harness.md` 是我们引入 Harness Engineering 的方法论参考。

## 关键文件导航

| 你想做什么 | 去哪里 |
|---|---|
| 理解当前流程怎么跑 | [.harness/agents/application-owner.md](.harness/agents/application-owner.md) |
| 看十阶段流程定义 | [.harness/rules/development-process.md](.harness/rules/development-process.md) |
| 写代码前对齐风格 | [.harness/rules/coding-style.md](.harness/rules/coding-style.md) |
| 了解目录约束 | [.harness/rules/engineering-structure.md](.harness/rules/engineering-structure.md) |
| 用某个阶段的 SOP | [.harness/skills/README.md](.harness/skills/README.md) |
| 看历史变更/启动新变更 | [.harness/changes/](.harness/changes/)（模板在 `_template/`） |
| 查领域术语 / 系统总体设计 | [wiki/](wiki/) 与 [.harness/design.md](.harness/design.md) |

## 硬性约束（违反即视为流程失败）

1. **任何对代码或目录结构的修改都必须挂在一个 change 下**。change 目录在 `.harness/changes/<feature-slug>-<yyyymmdd>/`，从 `_template/` 拷贝。
2. **不允许跳过需求分析直接写代码**。即使是 "加一行 log" 这种小改动，也要在对应 change 的 `request_analysis/spec.md` 里留下一两句说明和验收标准。
3. **不允许在评审未通过时进入下一阶段**。阶段间用 `summary.md` 串联状态。
4. **不允许声称完成而没有机械化证据**：CI 报告、测试通过数、部署验证截图/输出，缺一不可。
5. **发现 Agent / 流程缺陷，把防复发机制补回 `.harness/`**（rules 或 skills），不要只在当前会话临时绕过。

## 当下项目状态

当前仓库**还没有 dataplat 代码**，只有 `.harness/` 与 `wiki/` 骨架。第一个 change 建议是 `bootstrap-monorepo-<yyyymmdd>`：按 `design.md` §11.3 把 monorepo 目录骨架搭起来。**用这个 change 把整个 harness 流程 Dry Run 一遍**，发现流程缺陷立刻反哺到规则里。
