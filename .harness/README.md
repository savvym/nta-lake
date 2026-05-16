# .harness/

这是本项目的 **Harness 体系**——AI Coding 的运行环境。它把团队经验、工程规范、流程编排、质量门禁外部化为可执行文件，让 Agent 能在长周期、跨会话中稳定推进工作。

## 目录约定

```
.harness/
├── README.md                       # 本文件
├── harness.md                      # Harness Engineering 方法论笔记（背景阅读）
├── design.md                       # 目标系统：LLM 训练数据管理平台架构设计
│
├── agents/
│   └── application-owner.md        # 编排中枢：流程总调度、Skill 加载策略、硬性约束
│
├── rules/                          # "标准是什么"——Agent 必须遵守
│   ├── development-process.md      # 十阶段开发流程 + 进入/产出/门禁/回退
│   ├── engineering-structure.md    # monorepo 结构约束（依据 design.md §11.3）
│   └── coding-style.md             # Python/TS 风格、命名、注释、错误处理底线
│
├── skills/                         # "应该怎么做"——可复用 SOP，按需加载
│   ├── README.md                   # Skill 索引
│   ├── request-analysis/SKILL.md
│   ├── coding-skill/SKILL.md
│   ├── expert-reviewer/SKILL.md
│   ├── unit-test-write/SKILL.md
│   ├── unit-test-ci/SKILL.md
│   ├── deploy-verify/SKILL.md
│   ├── code-review/SKILL.md
│   ├── project-analysis/SKILL.md
│   └── ci-generate/SKILL.md
│
├── changes/                        # "做了什么"——每个需求一个独立目录
│   ├── README.md                   # 变更管理说明
│   └── _template/                  # 复制此目录开启一个 change
│
└── mcp/
    └── README.md                   # MCP server 配置占位（Phase 1 之后启用）
```

`wiki/` 在仓库根目录下，承载"系统是什么样的"——领域术语、架构总览、ADR。

## 加载策略

参考 `harness.md` §3.1 的分层加载：

| 层 | 何时加载 | 文件 |
|---|---|---|
| **常驻** | 每次会话启动 | `CLAUDE.md` → `agents/application-owner.md` |
| **阶段触发** | 进入对应阶段时 | `rules/development-process.md` + 对应阶段的 `skills/<name>/SKILL.md` |
| **按需查询** | 涉及具体设计/术语时 | `design.md` / `wiki/*` / `changes/<id>/summary.md` |

**入口文件像索引和地图，不是百科全书**。具体细节按需进入相应文件阅读。

## 与目标系统的关系

`.harness/` 是**开发过程**的载体；`apps/` `packages/` `worker/` `plugins/` 等（尚未创建）是**产物**。两者并行存在：每一次代码改动都会在 `.harness/changes/` 留下一个完整的"需求→实现→验证"档案。

## 演进原则

1. **规范是活文档**。每次 Agent 犯错，把防复发机制（新增 rule、修订 skill、加门禁）补回 `.harness/`。
2. **门禁必须可程序化验证**。能用脚本检查的不要只写自然语言建议。
3. **执行与评判分离**。同一个变更里，coding 阶段的 Agent ≠ review 阶段的 Agent。
4. **小需求也不跳阶段**。流程一致性优先于短期效率。
