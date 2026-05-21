---
change_id: web-recipe-structured-config-20260521
phase: design
status: approved
authored_at: 2026-05-21T20:40:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：Recipe Builder 结构化算子配置 + Run Recipe 按钮（v3 mini-design）

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

新增 `GET /operators` 端点暴露 operator config_schema；`recipes/builder` 用结构化输入替代 YAML textarea；加"运行 recipe"按钮 POST `/pipelines/runs:from-yaml`。

## 背景

用户验收 W4 后投诉（原话）：**"当前能对 bronze 资产进行算子处理么？pipline 本质上是选不同的算子和参数，但是现在是填写 yaml，能更操作友好一点吗"**。

现状：
- W4-3 `recipes/builder.tsx` 每个算子卡用 `<textarea>configYaml` 让用户手填 YAML，体验差
- 已有端点 `POST /pipelines/runs:from-yaml`（admin only）能直接收 YAML 创建 run，但 builder 没有 Run 按钮，只有 Copy / Download / Validate
- packages/core 11 个 operator 每个都有 `OperatorSpec.config_schema`（JSON-Schema-like dict），可作为结构化输入的元数据
- 但目前**没有 API 暴露 operator schemas**；web 不知道每个 operator 需要什么参数

**约束**：
- 只支持有限 JSON-schema 类型：`string + enum → select` / `string → text input` / `integer → number input` / `number → number step=any` / `boolean → checkbox`；其他类型 / object / array → fallback 到原有 YAML textarea
- Loader 不做结构化：loader 通常 input 就一个 `blob_sha`，schema 不规整，且不在用户痛点路径
- D-1 永不做清单全部遵守

## 范围

In scope：

- **Backend**：
  - `apps/api/dataplat_api/routers/operators.py`（新，~40 行）：`GET /operators` → 返 list[{name, version, config_schema}]，按 name 字典序排
  - `apps/api/dataplat_api/main.py`：include router（1 行）
  - `apps/api/tests/test_operators_endpoint.py`（新，~30 行）：1 个 behavioral test 用 httpx ASGI 调 GET /operators 验返回 ≥ 11 个 entry + 含 `dedup` 的 schema 形状

- **Frontend**：
  - `apps/web/src/lib/api/queries.ts`（小改）：
    - 加 `OperatorMeta` 接口（name / version / config_schema）
    - 加 `useOperatorsQuery()` hook（react-query，5min staleTime）
    - 加 `useCreateRunFromYaml()` mutation hook（POST `/pipelines/runs:from-yaml`，body 为 text/yaml）
  - `apps/web/src/lib/recipe-v2-builder.ts`：删 `OPERATOR_NAMES` 硬编码（由 useOperatorsQuery 替代）；保留 `LOADER_NAMES` / `buildRecipeYaml`
  - `apps/web/src/components/operator-config-form.tsx`（新，~100 行）：根据 config_schema 渲染结构化输入；支持 5 种基础 type；其他 fallback YAML textarea；导出 `{schema, value, onChange, fallbackYaml, onFallbackYamlChange}` 接口
  - `apps/web/src/routes/recipes/builder.tsx`（改）：
    - 把 SortableOperatorCard 内的 `<textarea>configYaml` 换成 `<OperatorConfigForm>`（schema 来自 useOperatorsQuery）
    - state 每个 operator 加 `configObject: Record<string, unknown>` 字段（与 configYaml 并存：结构化输入更新 configObject，序列化时把 configObject 序列化为 yaml 注入 buildRecipeYaml；fallback 场景仍用 configYaml）
    - 加"运行 Recipe"按钮（仅 admin 显示）：点击后 `useCreateRunFromYaml.mutate(yamlText)`；成功显示 `run_id` + Link to `/jobs`；失败显示错误
  - `apps/web/src/routes/recipes/builder.test.tsx`（小改）：扩 RTL 测试覆盖 structured form 渲染 + Run 按钮

Out of scope：

- **不**改 Loader 的 input/config（仍 YAML textarea；用户痛点在 operator）
- **不**做 array / object 嵌套结构的可视编辑（fallback yaml 即可；follow-up `web-recipe-nested-config-*`）
- **不**做 operator descriptions / docs link（follow-up `web-operator-docs-*`）
- **不**对 GET /operators 加 admin gate（read-only 元数据；允许所有登录用户读）
- **不**做 Run 后跳到具体 run detail 页（先指向 /jobs 列表；run detail 路由 follow-up `web-pipeline-run-detail-*`）
- **不**做参数即时校验（min/max/required 等）：先信任后端 422；follow-up `web-recipe-config-client-validate-*`
- **不**改 backend 端 operator config_schema 本身
- **不**改 OperatorSpec / OperatorRegistry / Operator Protocol
- **不**违反 D-1 永不做清单

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | 新建 routers/operators.py 含 GET /operators；main.py 已 include | `test -f apps/api/dataplat_api/routers/operators.py && grep -qE '@router.get\(' apps/api/dataplat_api/routers/operators.py && grep -q 'operators_router' apps/api/dataplat_api/main.py` | 0 退出码 |
| AC-2 | behavioral | GET /operators 返 ≥ 11 个 entry，含 dedup 与其 config_schema | `cd apps/api && uv run pytest tests/test_operators_endpoint.py -x -q` | 1 passed |
| AC-3 | static | 新组件 operator-config-form.tsx 存在 + builder.tsx 引用 + queries.ts 加 hooks | `test -f apps/web/src/components/operator-config-form.tsx && grep -q 'OperatorConfigForm' apps/web/src/routes/recipes/builder.tsx && grep -qE 'useOperatorsQuery\|useCreateRunFromYaml' apps/web/src/lib/api/queries.ts` | 0 退出码 |
| AC-4 | behavioral | builder.test.tsx 验证结构化表单渲染 enum 为 select + Run 按钮触发 mutate | `cd apps/web && pnpm exec vitest run src/routes/recipes/builder.test.tsx` | PASS 含新 tests |
| AC-5 | static (lint + 全量回归) | typecheck + apps/web 全量测试 + apps/api 全量测试 | `cd apps/web && pnpm exec tsc --noEmit && pnpm exec vitest run` + `cd apps/api && uv run pytest -q` | 0 错误 / 全部 PASS / 0 回归 |

## 决策

1. **GET /operators 不加 admin gate**：纯只读元数据；任何登录用户能看；与 `/me` / `/healthz` 同安全级别。
2. **config_schema 类型支持有限**：JSON Schema 完整实现重；先覆盖 5 种核心类型（string+enum / string / integer / number / boolean）+ fallback yaml。当前 11 个 operator 的 config_schema 全部命中。
3. **state 双轨：configObject + configYaml**：结构化输入维护 `configObject`，序列化时 dump 进 yaml；fallback 路径用 configYaml（schema 不识别时）；同一时刻不混用避免数据丢失。
4. **buildRecipeYaml 兼容**：每个 operator 序列化时若 configObject 非空用它，否则 parse configYaml；保留 W4-3 测试不动。
5. **删 OPERATOR_NAMES 硬编码 + 用 useOperatorsQuery**：硬编码与后端注册脱钩（W4-8 加 eval_gen / W4-9 加 dpo_pair_gen 时 OPERATOR_NAMES 漏更新风险）；运行时拉取避免漂移。
6. **保留 LOADER_NAMES 硬编码**：loader 不在本次 scope；保留现状；后续 `web-loader-config-form-*` 时一起改。
7. **Run 按钮 admin-only**：后端 POST `/pipelines/runs:from-yaml` 已 admin only（require_admin）；非 admin 点了 403 体验差；前端 gate。
8. **Run 后跳 /jobs**：现有列表页支持按 status filter；用户能看到刚建的 run；不必加 run detail 路由。
9. **新组件放 components/ 而非 routes/recipes/**：可复用；与 `Button / Card` 同位置。
10. **不做客户端 schema validate**：信任后端 422；client validate 重复逻辑；follow-up 演化 zod from JSON-Schema。
11. **不动 LoaderRegistry / OperatorRegistry / Protocol**：只读元数据查询走 registry 已暴露的 list_names + 类 .spec 字段，零侵入。
12. **operator GET 排序**：按 name 字典序，让 UI 稳定排序。

## 风险

| 风险 | 缓解 |
|---|---|
| `OperatorRegistry.get(name)` 拿到的是类而非实例；`.spec` 是 class attr | 验证：所有 11 operator 都把 spec 定义为 class 级 `OperatorSpec(...)`（已确认 chunker/dedup/dpo_pair_gen 等） |
| config_schema 是 JSON-Schema dict；FastAPI 序列化 | response_model 定义 `config_schema: dict[str, Any]`；pydantic v2 支持 |
| W4-3 现有 builder.test.tsx 依赖 OPERATOR_NAMES 硬编码 | 新 hook 在 jsdom 下用 vi.mock；保留旧 fallback；不破坏现有 tests |
| 结构化表单与 fallback yaml 切换时数据丢失 | 同一 operator 卡只能用一种模式；默认结构化时不暴露 fallback，schema 不识别才回退 |
| operator schema "required" 项但用户未填 → 后端 422 | UI 标 required + 红色 *；提交时拦截缺字段（client 提示） |
| GET /operators 后端测试 startup 慢 | 与 W4-7 metrics endpoint test 同模式；用 httpx ASGI client |
| `useCreateRunFromYaml` 用 text/yaml content-type | 用 fetch 显式 `headers: {'Content-Type': 'text/yaml'}` 与 raw body；不复用 fetchJson（强制 json） |
| pdf-mineru 不在 LoaderRegistry → PDF→silver 入口不走 builder | 不在本次 scope；PDF 路径走 W4-1 pdf-mineru-ui |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/operators/registry.py`（OperatorRegistry.list_names / get）
  - `packages/core/src/dataplat_core/operators/*.py`（spec.config_schema 形状权威源）
  - `apps/api/dataplat_api/routers/pipelines.py:95-114`（已就绪的 POST /pipelines/runs:from-yaml；前端调用对接）
  - `apps/web/src/lib/recipe-v2-builder.ts`（buildRecipeYaml 仍复用；OPERATOR_NAMES 删除）
- 应当不动：
  - 后端 pipelines router / process router / pipeline 执行链
  - W1..W4-10 已 merge 产物
  - LoaderRegistry / Loader 相关（本次 scope 外）
  - W4-3 已写的 buildRecipeYaml 单测（必须保持 PASS）
- 引用的其他 change：W4-3 web-operator-chain-builder（结构基础）/ W4-8 W4-9 W2-1..W2-4（operator 来源）

## 关联 follow-up

- `web-loader-config-form-*`：Loader input/config 也走结构化（需先扩 LoaderSpec / 引入 config_schema 字段）
- `web-recipe-nested-config-*`：array / object 嵌套结构的 visual editor
- `web-operator-docs-*`：operator description + 用法示例
- `web-pipeline-run-detail-*`：run detail 路由 `/pipelines/runs/$id`
- `web-recipe-config-client-validate-*`：JSON-Schema → zod 实时校验
- `harness-operator-spec-description-*`：给 OperatorSpec 加 description 字段
