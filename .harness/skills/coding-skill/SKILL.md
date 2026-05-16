---
name: coding-skill
description: 按已通过评审的 spec/tasks，分层、有节奏地实现代码
applicable_stage: 阶段 3（编码实现）
inputs:
  - request_analysis/spec.md（最新通过版本）
  - request_analysis/tasks.md
  - .harness/rules/coding-style.md
  - .harness/rules/engineering-structure.md
outputs:
  - 实际代码改动
  - coding/coding_report_v{N}.md
---

# coding-skill Skill

## 进入条件

- 阶段 2 评审 verdict = APPROVED；`tasks_review_v*.md` 最新一份已 APPROVED。
- `summary.md` stage=`coding`、status=`in_progress`。
- 已加载 `coding-style.md` 与 `engineering-structure.md`。

## 输入

1. **当前任务清单**：从 `tasks.md` 抓 estimated_stage=coding（或未声明）的任务。
2. **设计约束**：相关模块的 design.md 章节、已有代码的接口契约。
3. **依赖任务的产物**：上游任务 id 已 done 的对应代码。

## 步骤

### 1. 准备工作区

- 确认所在分支符合 `coding-style.md` §4.1（`<author>/<change-id>`）。
- 拉取 main 并 rebase（或 merge，看团队约定）。
- 起本地中间件 / 起 mock（看是否需要）。

### 2. 接口与数据结构先行

- 写新功能：**先定 Pydantic 模型 / TS type / API 路由签名**，跑通空实现的 type check 再填业务。
- 改老功能：**先列出受影响的接口/类型变化**，再动实现，避免"调用方爆破"。

### 3. 分层落地（后端 Python）

按 `apps/api/dataplat_api/` 的分层（参考 design.md §11.3）：

```
routers/   →  仅做参数解析 / 鉴权 / 错误转 HTTP
services/  →  业务编排，无 HTTP / SQL 细节
models/    →  SQLAlchemy 表定义 + Alembic migration
schemas/   →  Pydantic 模型（请求/响应 + 内部 DTO）
storage/   →  Blob CAS 抽象、对象存储客户端
llm/       →  LLM Gateway，全部 LLM 调用入口
```

不允许 router 直接写 SQL；不允许 service 直接 import HTTP 类型。

### 4. 分层落地（前端 TS）

- `routes/`：路由组件 + loader（用 TanStack Router）。
- `components/<domain>/`：业务组件。
- `components/ui/`：shadcn 拷下来的原生组件，不要业务化。
- `lib/api/`：调 `@dataplat/api-types` 的薄包装；查询 hooks 在 `hooks/`。
- 表单一律 react-hook-form + zod；不允许业务层手撸 onChange 校验。

### 5. plugin / processor

- 新建 `plugins/<adapter-或-processor>-<name>/`，包含：
  - `pyproject.toml`（含 `[project.entry-points."dataplat.adapter"]` 或 `dataplat.processor`）
  - `manifest.yaml`
  - `src/<pkg>/__init__.py` 实现 `SourceAdapter` 或 `Processor` 协议
  - `tests/`
  - `README.md`
- 通过 `packages/core` 的 Protocol 与 RunContext，不能 import `apps/api`。

### 6. 增量提交

- 每完成 1-2 个任务做一次 commit，message 按 `coding-style.md` §4.2。
- 不要把 lint/format 改动与业务改动混在同一 commit；先单独 commit 一次"chore: format X" 再做业务。
- **本阶段不需要 push**——push 在阶段 7。

### 7. 本地校验

每次进入 review 前必须本地跑：

```bash
# Python
uv run ruff check apps/api packages/core
uv run mypy apps/api/dataplat_api
uv run pytest apps/api  # 暂时不要求覆盖率，但必须不报错

# TS
pnpm --filter web lint
pnpm --filter web typecheck
```

失败先修，不要带病进 review。

### 8. 写 coding_report

按 `coding/coding_report_v{N}.md` 模板填：

- 改动文件列表（路径 + 一句话说明改了什么 / 为什么）
- 与 tasks.md 的任务映射表（每个 task 是否完成、对应 commit SHA、deferred 原因）
- 已知 trade-off / 偏离 spec 之处（必须说明并征求评审）
- 本地校验结果摘要

## 产出

- 代码改动（commit 在功能分支上）。
- `coding/coding_report_v{N}.md`。
- `summary.md` stage=`coding`、status=`waiting_review`。

## 质量门禁

```text
coding_report_v{latest}.md 存在
报告中"改动文件列表" 与 git diff --name-only main...HEAD 一致
本地 ruff / mypy / pnpm lint / pnpm typecheck 全部 0 错误
未引入未在 spec/tasks 中授权的目录或顶层依赖
所有改动属于本 change 的 scope（用 git log 抽查不出无关 commit）
```

## 失败回退

- spec 与现实代码冲突 → 回阶段 1，更新 spec 或拆 change。
- 类型/编译错误反复 → 留在本阶段，**先回简化设计**而不是堆 type: ignore。
- 任务粒度比预想大很多 → 回阶段 1 重切 tasks，不要在 coding 阶段隐式扩大 scope。

## 反模式

- 边写代码边改 spec 不留痕迹。
- 一个 commit 几百行覆盖多个文件多个目的。
- 拆抽象只为"将来扩展"，当前 spec 用不到。
- 在 plugin 里直接 import provider SDK（应走 LLM Gateway）。
- mock 数据库 / blob 存储以"加速开发"，导致评审时无法验证真实行为。
