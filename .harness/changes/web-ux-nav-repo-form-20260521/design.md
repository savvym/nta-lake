---
change_id: web-ux-nav-repo-form-20260521
phase: design
status: approved
authored_at: 2026-05-21T19:30:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：Web UX 修复——顶部导航 + 新建 repo schema 字段（v3 mini-design）

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

`__root.tsx` 顶部 nav 加 Repos / New Repo / Recipes Builder 入口；`repos.new.tsx` 在 layer=silver|gold 时显示 schema_id+row_format 下拉。

## 背景

用户验收 W4 部署后投诉两条 UX 缺陷（原话）：

1. **"当前部署的可视化页面，很多没有入口可以进去啊？只能通过 url 进去"**
   - `apps/web/src/routes/__root.tsx` nav 仅 3 项（dataplat home / Jobs / Observability），缺：Repos 列表 / 新建 Repo / Recipes Builder
   - 用户必须手输 URL 才能进 `/repos`、`/repos/new`、`/recipes/builder` 等 W4 落地页

2. **"我创建一个 silver 仓库提示我 {detail:layer=silver 必须传 schema_id}"**
   - `apps/web/src/routes/repos.new.tsx` zod schema 只含 6 字段，完全不暴露 schema_id+row_format
   - 后端 `apps/api/dataplat_api/services/repo.py:47-86`（W1-3 silver-schema-enforce）硬性要求 silver/gold 必传，缺则 HTTP 422
   - 已注册 schema：`silver-text-v1` / `gold-sft-v1`（`packages/core/src/dataplat_core/schemas/_builtin.py`）；row_format ∈ {`parquet`, `jsonl`}

**关键约束**：只动 web 表单 + nav；后端已就绪不改；不新增 GET /schemas 端点（schema 列表 ≤ 2，硬编码足够）；bronze 不传 schema_id/row_format（后端反向校验）。

## 范围

In scope：

- `apps/web/src/routes/__root.tsx`：登录态导航追加 3 个 `<Link>`：Repos（`/repos`）→ New Repo（admin only，`/repos/new`）→ Recipes Builder（`/recipes/builder`），放在 Jobs 之前；样式沿用 `text-sm text-gray-700 hover:underline`
- `apps/web/src/routes/repos.new.tsx`：
  - 加常量 `SCHEMA_IDS_BY_LAYER = { silver: ['silver-text-v1'], gold: ['gold-sft-v1'] }` 与 `ROW_FORMATS = ['parquet', 'jsonl']`，旁注释指向 `_builtin.py`
  - zod schema 加 `schema_id?: string` + `row_format?: enum(parquet, jsonl)`
  - layer=silver|gold 时渲染两个新 `<select>`（layer=bronze 隐藏并清空）
  - layer 切换默认值：silver → `silver-text-v1`+`parquet`；gold → `gold-sft-v1`+`parquet`；bronze → 清空
  - `onSubmit` 把 schema_id+row_format 传给 `createRepo.mutateAsync`
- `apps/web/src/lib/api/queries.ts`：`CreateRepoRequest` 接口加 `schema_id?: string | null` + `row_format?: 'parquet' | 'jsonl' | null`
- `apps/web/src/routes/repos.new.test.tsx`：扩 RTL 测试覆盖新行为（schema 字段渲染 + submit payload 含新字段）

Out of scope：

- **不**新增后端 `GET /schemas` 端点（schema ≤ 2 时硬编码足够；follow-up `web-schemas-api-*`）
- **不**改后端 routers / services / schemas
- **不**做 schema 字段 tooltip / 文档链接（follow-up `web-schema-id-tooltip-*`）
- **不**改 Recipes Builder 内部逻辑（操作友好度问题由 Change B 处理）
- **不**加 repo 详情页上下文链接（follow-up `web-repo-detail-contextual-links-*`）
- **不**做 mobile / hamburger nav
- **不**改 W1..W4-10 已 merge 产物
- **不**违反 D-1 永不做清单

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | __root.tsx 含 `/repos` + `/repos/new` + `/recipes/builder` 三个 Link 入口 | `grep -cE 'to="(/repos\|/repos/new\|/recipes/builder)"' apps/web/src/routes/__root.tsx` | `>= 3` |
| AC-2 | static | repos.new.tsx 含 SCHEMA_IDS_BY_LAYER 常量；CreateRepoRequest 扩 schema_id + row_format | `grep -q 'SCHEMA_IDS_BY_LAYER' apps/web/src/routes/repos.new.tsx && grep -q 'schema_id' apps/web/src/lib/api/queries.ts && grep -q 'row_format' apps/web/src/lib/api/queries.ts` | 0 退出码 |
| AC-3 | behavioral | layer 切到 silver 时 schema_id+row_format select 出现 + 默认值正确；submit 时 mutate 收到含两字段的 payload | `cd apps/web && pnpm exec vitest run src/routes/repos.new.test.tsx` | 新增 test PASS |
| AC-4 | static (lint + 整体回归) | typecheck + 全量 web 测试 | `cd apps/web && pnpm exec tsc --noEmit && pnpm exec vitest run` | 0 错误 / 全部 PASS（含原有 62） |

## 决策

1. **硬编码 schema 列表**：当前注册 schema 只 2 个；新增 GET /schemas 引入 router+service+sdk type 增量过大；同步成本一两行常量改动可忍受。
2. **layer=bronze 隐藏并清空 schema 字段**：后端不允许 bronze 传 schema_id/row_format（传了 422）；隐藏 + reset 避免误填。
3. **layer 切到 silver|gold 默认填值**：避免漏填；默认 `silver-text-v1`/`gold-sft-v1` + `parquet`。
4. **row_format 默认 `parquet`**：与 dataplat 主语义对齐（silver 行 = parquet 列存优先）。
5. **nav 顺序**：Repos / New Repo / Jobs / Observability / Recipes Builder；Repos 是日常入口放最左，Recipes Builder 偏工具放右。
6. **New Repo 仅 admin 可见**：后端 POST /repos 已 admin only（403）；普通用户点入只会报错，前端 `me.role === 'admin'` gate。
7. **不动 repos.new 现有字段顺序**：schema 字段插入在 visibility 下方，主表单视觉变化最小。
8. **schema_id 用 `<select>` 而非 Combobox**：≤ 2 项；与现有 layer/subtype select 一致，零新组件依赖。

## 风险

| 风险 | 缓解 |
|---|---|
| 用户切换 layer 后未清空 schema_id → bronze 带 schema_id 被 422 | layer change handler 显式 reset 这两字段 |
| 硬编码常量与 `_builtin.py` 不同步 | 注释指向源；follow-up `web-schemas-api-*` 改运行时拉取 |
| jsdom select 行为 | 用 `screen.getByLabelText('schema_id')` + `fireEvent.change`，与现有 layer select 同模式 |
| nav 窄屏溢出 | 现 nav 已水平 flex；偶尔换行可接受；mobile 留 follow-up |
| `CreateRepoRequest` 字段扩展破坏既有 caller | 新字段都 optional |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `apps/api/dataplat_api/services/repo.py:47-86`（schema 校验语义来源）
  - `packages/core/src/dataplat_core/schemas/_builtin.py`（schema 权威源）
  - `apps/api/dataplat_api/schemas/repo.py:26-27`（payload 已含 schema_id/row_format）
- 应当不动：后端 routers / services / schemas；W1..W4-10 已 merge 产物；`packages/api-types/src/generated.ts`
- 引用的其他 change：W1-3 silver-schema-enforce / W4-1..W4-4 W4-7（nav 入口涉及它们的路由）

## 关联 follow-up

- `web-schemas-api-*`：schema 注册数 ≥ 5 时新增 GET /schemas + 动态加载
- `web-schema-id-tooltip-*`：schema 选项加 hover 说明
- `web-repo-detail-contextual-links-*`：repo 详情页跳转 pdf-mineru / snapshots / recipes builder 的上下文按钮
- `web-nav-mobile-*`：窄屏 hamburger menu
