# CLAUDE.md

本项目正在按 **Harness Engineering** 范式开发。所有写代码、改代码、评审、测试、CI、部署的工作都必须走 `.harness/` 下定义的流程，**不要绕过**。

## 你的第一件事

进入本项目的任何会话，**先读 `.harness/agents/application-owner.md`**。它定义了：

- 你作为 Application Owner 的角色与硬性约束
- 当前应当加载的 Rules / Skills / Wiki 索引
- **三阶段开发流程**（v2，2026-05-20 起）的入口、产物、质量门禁与回退路径
- 任何任务的标准操作流程：**Phase 1 Design (opus) → Phase 2 Implementation (sonnet 端到端) → Phase 3 Verify (opus)**

## 项目背景

目标系统是一个**面向 LLM 训练的数据管理平台**（Bronze/Silver/Gold 三层、类 Git 版本控制 + CAS、可插拔 Adapter/Processor、统一 LLM 网关）。完整设计见 [.harness/design.md](.harness/design.md)。

`.harness/harness.md` 是我们引入 Harness Engineering 的方法论参考。

## 关键文件导航

| 你想做什么 | 去哪里 |
|---|---|
| 理解当前流程怎么跑 | [.harness/agents/application-owner.md](.harness/agents/application-owner.md) |
| 看**三阶段流程**定义（v2，2026-05-20 起） | [.harness/rules/development-process.md](.harness/rules/development-process.md) |
| 看 v1 十阶段定义（deprecated，仅供历史参考） | [.harness/rules/development-process-v1-deprecated.md](.harness/rules/development-process-v1-deprecated.md) |
| 写代码前对齐风格 | [.harness/rules/coding-style.md](.harness/rules/coding-style.md) |
| 了解目录约束 | [.harness/rules/engineering-structure.md](.harness/rules/engineering-structure.md) |
| 用某个阶段的 SOP | [.harness/skills/README.md](.harness/skills/README.md) |
| 看历史变更/启动新变更 | [.harness/changes/](.harness/changes/)（模板在 `_template/`） |
| 查领域术语 / 系统总体设计 | [wiki/](wiki/) 与 [.harness/design.md](.harness/design.md) |
| **理解平台北极星** | [.harness/design.md § 北极星](.harness/design.md#北极星)（"LLM 训练数据工厂" + 三层算子 Adapter/Loader/Operator + stats-first + 行级血缘 + 永不做清单） |

## 硬性约束（违反即视为流程失败）

1. **任何代码 / 目录结构修改都必须挂在一个 change 下**。`bash scripts/harness_new_change.sh <id> [title]` 创建。
2. **不允许跳过 Design（Phase 1）**。即使"加一行 log"也要在 `design.md` 留一句说明 + AC。
3. **不允许跳过 Phase 1 + Phase 3 reviewer**（除非极小变更且声明 self-attest verdict + 理由）。
4. **模型分配硬约束**：Phase 1 reviewer = **opus** / Phase 2 implementer = **sonnet** / Phase 3 reviewer = **opus**。违反 = 流程失败。
5. **不允许声称完成而没有机械化证据**：测试通过数、self_check 输出、curl 响应、PR 链接，缺一不可。
6. **发现 Agent / 流程缺陷，把防复发机制补回 `.harness/`**（rules 或 skills）；harness 框架本身的改动可以由用户授权直接落地（如 2026-05-20 的 v1→v2 pivot），但要在 `.harness/changes/harness-*-<yyyymmdd>/` 留 meta 记录。
7. **任何 change 不得违反 [.harness/rules/data-not-code-pivot.md](.harness/rules/data-not-code-pivot.md)** 的"永不做清单"（branch / merge / cherry-pick / rollback / row-diff / blob 派生图 / Asset / manifest.yaml 强制 / silver 文件树 / bronze 强 schema）。Phase 1 reviewer 必查。
8. **反复 spawn reviewer 是 v1 失败模式 v2 显式禁止**：Phase 1 SMALL REVISIONS 修一轮就进 Phase 2；Phase 3 MINOR FIX 修一轮就 merge。

## 当下项目状态

当前仓库**还没有 dataplat 代码**，只有 `.harness/` 与 `wiki/` 骨架。第一个 change 建议是 `bootstrap-monorepo-<yyyymmdd>`：按 `design.md` §11.3 把 monorepo 目录骨架搭起来。**用这个 change 把整个 harness 流程 Dry Run 一遍**，发现流程缺陷立刻反哺到规则里。
