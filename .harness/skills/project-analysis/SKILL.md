---
name: project-analysis
description: 梳理项目结构 / 链路 / 依赖 / 核心模块，产出可被后续会话复用的结构索引
applicable_stage: 支援型（非阶段 SKILL）
inputs:
  - 当前仓库代码
  - .harness/design.md
  - wiki/architecture.md（如有）
outputs:
  - wiki/architecture.md 的更新 / 补充
  - 或独立的分析报告 .harness/changes/<id>/analysis_v{N}.md
---

# project-analysis Skill

## 进入条件

> 本 Skill 是**支援型**，不在十阶段主流程内自动触发。出现以下任一情形时显式加载：

- **新成员上手**：让 Agent 先跑一遍 project-analysis，输出当前真实结构，避免基于过时设计写代码。
- **大重构前**：列出"会被影响的模块 / 链路 / 依赖"。
- **跨 change 一致性审计**：周期性检查代码现状与 `wiki/architecture.md` / `design.md` 是否有漂移。
- **debug 复杂链路问题**：把"从用户请求到落库"的完整链路画出来，让排查有据可依。

不在标准十阶段流程内——主流程不会自动加载。

## 输入

1. 当前仓库代码（实际状态，不是设计文档）。
2. `.harness/design.md`（设计意图）。
3. 既有 `wiki/architecture.md`（如已写）。
4. 必要时：`docker-compose.dev.yml`、`pyproject.toml` / `package.json`（依赖关系真相）。

## 步骤

### 1. 顶层结构梳理

跑：

```bash
find . -maxdepth 3 -type d -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.venv/*'
```

输出：

- 当前实际存在的顶层目录
- 与 `engineering-structure.md` 声明的差异（增 / 缺 / 错位）

差异都列出来，**不要静默修复**。

### 2. 模块依赖图

- Python：用 `pydeps` 或手动 grep `import dataplat_*` 找跨包依赖。
- TS：检查 `packages/*/package.json` 的 dependencies。
- 关键产出：一张依赖 DAG（mermaid 或 ASCII），节点是 package / app / plugin。

检查规则：

- `apps/api` ⟂ `apps/web`（不互相 import；只通过 OpenAPI）。
- `plugins/*` ⟂ `apps/*`（plugin 只依赖 `packages/core`）。
- `packages/api-types` 单向依赖：`apps/web` → `api-types`，无反向。

发现违反 → MUST FIX 提到对应 change。

### 3. 关键链路梳理

至少覆盖：

- **资产录入链路**：HTTP 上传 → router → service → CAS blob 写入 → commit → lineage 记录。
- **Pipeline 执行链路**：用户提交 → 队列入 RQ → worker 消费 → subprocess plugin → workspace commit。
- **LLM 调用链路**：plugin / processor → `ctx.llm.call` → LLM Gateway → provider → cache 命中 / 入 audit log。

每条链路用一张顺序图（mermaid sequenceDiagram）描述，标出涉及的文件路径与关键函数。

### 4. 数据模型梳理

列出 DB schema + 关键关系：

- `repositories` / `commits` / `refs` / `blobs` / `tree_entries` / `lineage_edges` / `users` / `acls` …
- 每张表关键字段、外键、索引。
- 与 design.md §2 / §4.4 的 CAS 模型对齐情况。

差异作为 wiki/architecture.md 的更新项。

### 5. 部署拓扑

- 哪些服务、跑在哪、用什么镜像、暴露什么端口。
- Phase 1 用 docker-compose；Phase 2+ 用 k8s。
- 用一张拓扑图。

### 6. 缺口与风险

列出：

- 设计 vs 实现的漂移点
- 缺失的测试覆盖（按模块）
- 未关闭的 deferred SHOULD FIX
- 跨 change 的隐性依赖

## 产出

两种输出路径：

| 场景 | 写到哪里 |
|---|---|
| 周期性 / 上手 | 更新 `wiki/architecture.md` 与 `wiki/domain-glossary.md` |
| 重构准备 / 一次性分析 | 写 `.harness/changes/<id>/analysis_v{N}.md`，并在 PR description 链接 |

无论哪种，都必须包含：

- 顶层结构现状 + 差异
- 模块依赖 DAG
- 关键链路顺序图（至少 1 个）
- 数据模型 ER 摘要
- 缺口与风险清单

## 质量门禁

```text
报告含必填章节：结构 / 依赖 / 链路 / 数据 / 缺口
依赖 DAG 与代码现状一致（评审会随机抽 1 个边核对 import）
列出至少 1 个具体可执行的 follow-up（task / change / ADR）
```

## 失败回退

- 代码现状与 `design.md` / `architecture.md` 漂移太大，本 Skill 单跑无法收敛 → 把漂移点写进报告，**新开一个 `harness-realign-wiki-<yyyymmdd>` 变更或一份 ADR 走主流程**；不要在本 Skill 内强行"调和"。
- 依赖 DAG 跑出循环（如 apps/api ↔ apps/web 互相 import）→ 报告中标红，**触发独立修复变更**；不要把"修循环依赖"塞进当前调用本 Skill 的上层任务。
- 关键链路梳理过程中发现安全 / 合规问题（如 secret 落进了代码） → **立即停止本 Skill 输出**，按事故处理流程上报，再决定能否公开归档。
- 分析需要的访问权限（DB / secret manager）缺失 → 在报告"缺口"段标注 BLOCKED 并停止；不要凭推测填空。
- 上层是"大重构前调研"使用本 Skill，调研结论是**不该重构** → 在报告明确写出，回到 spec 阶段调整方案。

## 反模式

- 直接复述 design.md 当分析报告。
- 画了一张"理想架构图"但与代码现状不符。
- 列了一堆"未来可以做"的 NICE TO HAVE，没有可执行的 follow-up。
