# wiki/

> "**告诉 Agent 系统是什么样的**"。
>
> `.harness/rules/` 说**标准是什么**；`.harness/skills/` 说**应该怎么做**；`.harness/changes/` 说**做了什么**。
> 本目录 `wiki/` 是第四块：**系统当前长什么样**。

## 索引

| 文件 | 用途 | 何时读 |
|---|---|---|
| [architecture.md](architecture.md) | 系统总体架构、模块依赖、关键链路、部署拓扑 | 新成员上手；跨模块开发；调试链路问题 |
| [domain-glossary.md](domain-glossary.md) | 领域术语（Repository / Asset / Adapter / Processor / Lineage 等） | 任何看到陌生术语时；写 spec.md 前对齐用词 |
| [adr/](adr/README.md) | 架构决策记录 | 做大决策前查先例；做小决策前看是否需要补 ADR |

`.harness/design.md` 是系统**设计意图**（v0.x 的整体蓝图）。`wiki/` 是**当前实现状态**与**长期沉淀**。两者并存：

- 看"为什么这么设计" → `.harness/design.md` + `wiki/adr/`
- 看"现在系统真实长什么样" → `wiki/architecture.md`

## 维护原则

1. **不复述 design.md**。需要的话**链接**到 design.md 的章节，并补充当前实际偏差。
2. **架构图与代码现状一致**。`project-analysis` Skill 跑完会更新 `architecture.md`；如果两者长期漂移，是架构 bug，开 ADR 决议。
3. **ADR 一旦 accepted 不修改原文**，新决议开新文件并 supersedes 旧的。
4. **glossary 是仓库内的唯一术语权威**。代码命名、文档措辞都以它为准。
