---
change_id: web-operator-chain-builder-20260520
phase: design
status: approved
authored_at: 2026-05-21T12:00:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：Recipe v2 Chain Builder UI (W4-3，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

新增 `/recipes/builder` 路由：UI 拖拽组装 Recipe v2（1 Loader + N Operators 线性链）→ 实时生成 yaml → 复制 / 下载文件。Recipe v2 schema 在 packages/core 已有（W2-5），本 change 只在前端做 builder + yaml 序列化。

## 背景

W2-5 落了 `RecipeV2` schema + `load_recipe_v2` 解析器 + `run_recipe_v2` 执行器（packages/core/recipe.py），但 apps/api 当前的 pipeline 路由 (`POST /pipelines/runs`) 仍走 **v1 DAG-based Recipe**（apps/api/dataplat_api/pipelines/builders.py + load_recipe）。Recipe v2 仅在 packages/core 单测里被覆盖，没有 apps/api endpoint。

W4-3 roadmap 描述的"实际跑通"路径需要 apps/api 暴露 v2 执行 endpoint —— 那是一个独立改动（worker / persistence / 状态机），**不在本 change 范围**。本 change 仅做 **UI 端 builder + yaml 输出**：让 user 在 web 上组装 chain → 下载 / 复制 yaml；当前 paste 到老 pipelines textarea 跑不通（schema 不兼容），未来 `recipe-v2-execution-endpoint-*` follow-up 落地 endpoint 后 yaml 直接送进去。

技术选型：roadmap 文本提及 react-flow，但 Recipe v2 schema **是严格线性的**（loader + ordered operators），不存在 DAG / 分支，没有 edge 编辑需求。react-flow ~80KB gzipped 是为通用 graph 编辑而生，对线性 chain 过重。改用 `@dnd-kit/sortable`（~20KB）做垂直可拖序的 operator 列表，更切合 Recipe v2 schema 语义。这是与 roadmap 的显式偏离，列入决策。

yaml 序列化用 `js-yaml`（~25KB），是 npm 上最稳定的 yaml stringify 库，apps/web 当前不依赖。

## 范围

In scope：

- `apps/web/package.json`：新增 3 个依赖：
  - `@dnd-kit/core@^6`（拖拽核心）
  - `@dnd-kit/sortable@^8`（垂直可拖序列表 preset）
  - `js-yaml@^4`（yaml stringify；TypeScript types 走 `@types/js-yaml@^4` dev dep）
- `apps/web/src/routes/recipes/builder.tsx`（新；flat-dot 风格，路径 `/recipes/builder`；因为 `recipes/` 目录不存在，flat-dot 不与既有 route 冲突）：
  - zod search schema（可选）：`loader?: string`、`recipe_name?: string`（用于通过 URL 预填）
  - state（local React state，不入 URL）：
    - `recipeName: string`（默认 `"my-recipe"`）
    - `loader: { name: string; configYaml: string; inputYaml: string } | null`
    - `operators: Array<{ id: string; name: string; configYaml: string }>`（id 用于 dnd-kit 排序）
  - 三栏布局（flex row）：
    - 左栏（240px）：**Palette**
      - "Loader" section：dropdown 选择 loader（来自 hard-coded LOADER_NAMES 数组，与 W3-1..6 注册的 loaders 对齐）
      - "Operator" section：dropdown + "Add" 按钮，把选中 operator 追加到链尾（OPERATOR_NAMES hard-coded，与 W2-1..4 注册对齐）
    - 中栏（flex 1）：**Chain**
      - 顶部：recipe_name 文本框
      - Loader 卡片：name + config (textarea, yaml) + input (textarea, yaml)；空时显示 "未选 Loader"
      - Operator 列表：`<SortableContext>` 包裹；每个 Operator 渲染为可拖拽卡片，含 name + config (textarea) + 删除按钮 + 拖手 (`<GripVertical />` icon)
    - 右栏（360px）：**YAML preview**
      - `<pre data-testid="yaml-preview">`：实时反映当前 state 的 yaml 文本
      - "复制" 按钮（`navigator.clipboard.writeText(yaml)`）
      - "下载" 按钮（创建 Blob + a[href] 触发下载 `${recipeName}.yaml`）
      - "校验" 按钮：尝试 `yaml.load(yaml)` → 显示 valid / 错误信息（不做 schema 校验，仅 yaml 语法）
- `apps/web/src/lib/recipe-v2-builder.ts`（新）：
  - `buildRecipeYaml(state) -> string`：组装 RecipeV2 schema 结构 → js-yaml stringify
    - schema：`{ name, version: 2, loader: { name, config, input }, operators: [{ name, config }, ...] }`
    - config / input 字段：caller 传 yaml string，本函数先 `yaml.load` 成 obj 再嵌入；空 yaml 视为 `{}`
    - 异常处理：`yaml.load` 失败 throw `Error(detail)`；caller (UI) catch 显示 inline 错误
  - 导出 `LOADER_NAMES` / `OPERATOR_NAMES` 常量数组（hard-coded；与 W2-1..W3-7 注册一致）
- `apps/web/src/routes/recipes/builder.test.tsx`（新）：3 个 vitest+RTL 用例（不引 dnd-kit 模拟拖拽，只测序列化 / 添加 / 删除 / yaml preview）
- `apps/web/src/lib/recipe-v2-builder.test.ts`（新）：3 个 vitest 单测（pure 函数测）

Out of scope：

- **不**接 apps/api：v2 execution endpoint 是独立 change，留 follow-up `recipe-v2-execution-endpoint-*`
- **不**做 schema 校验（pydantic 在前端跑不动）：留 follow-up `web-recipe-v2-schema-validate-*`（用 zod 镜像 schema）
- **不**做 react-flow 风格 graph 编辑（recipe v2 schema 线性，无需）：留 follow-up `web-recipe-v2-dag-builder-*` (如果未来 RecipeV3 引入 DAG)
- **不**做 operator config 的字段级表单（per-operator 专属 UI）：MVP 用 textarea 让 user 写 yaml；留 follow-up `web-operator-config-form-*`
- **不**做 LoaderRegistry / OperatorRegistry 从 apps/api 动态拉取（hard-coded 列表先用着）：留 follow-up `web-registry-discovery-api-*`
- **不**做 dry-run 预览（拉 silver row 看结果）：留 follow-up `web-recipe-v2-dry-run-*`（依赖 v2 execution endpoint）
- **不**接 LLM Gateway 真跑（W4-5 引入 cost-budget；本 change 不接）
- **不**改 W4-1 / W4-2 / W3-* / W2-* / W1-* 任何 merged 产物
- **不**做 dataset-card.yaml / manifest.yaml（D-1）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | builder 路由文件存在 + createFileRoute path 正确 | `test -f apps/web/src/routes/recipes/builder.tsx && grep -q 'createFileRoute("/recipes/builder")' apps/web/src/routes/recipes/builder.tsx` | 0 退出码 |
| AC-2 | behavioral | buildRecipeYaml pure 函数：传入 `{name:"r",loader:{name:"pdf_mineru",configYaml:"",inputYaml:"blob_sha: abc"},operators:[{id:"1",name:"normalize_unicode",configYaml:""}]}` → 返回 yaml 字符串，js-yaml.load 解出含 `name: r`、`version: 2`、`loader.name: pdf_mineru`、`loader.input.blob_sha: abc`、`operators[0].name: normalize_unicode` | `cd apps/web && pnpm vitest run src/lib/recipe-v2-builder.test.ts -t "serializes minimal recipe"` | 1 passed |
| AC-3 | behavioral | builder UI 渲染：选 loader pdf_mineru + 添加 operator normalize_unicode 后，`<pre data-testid="yaml-preview">` 文本含 "name: pdf_mineru" + "name: normalize_unicode" 子串 | `cd apps/web && pnpm vitest run src/routes/recipes/builder.test.tsx -t "yaml preview reflects loader and operator"` | 1 passed |
| AC-4 | behavioral | builder UI 删除 operator：先添加 2 个 operators，点其中 1 个的删除按钮，yaml-preview 只剩 1 operator | `cd apps/web && pnpm vitest run src/routes/recipes/builder.test.tsx -t "remove operator"` | 1 passed |

## 决策

1. **不用 react-flow，改用 @dnd-kit/sortable**（**roadmap 显式偏离，记入此处**）：Recipe v2 schema 线性（`loader + operators: list[...]`），无 DAG 需求；react-flow 80KB 是为通用 graph 编辑；dnd-kit/sortable 20KB 专为可拖序列表设计。语义贴 + 体积小 + 学习曲线低。未来若 RecipeV3 引入 DAG，再单独切换。
2. **builder UI 与 apps/api 完全解耦**：本 change 仅生成 yaml；执行能力是独立 change（recipe v2 execution endpoint）。MVP 用户体验 = "拼装好后下载 yaml + 复制 / 后端跑得通的链路 W4-x 落地"。这避免本 change 同时改前后端，符合 v3 单 change 单 layer 边界。
3. **flat-dot 路由 `recipes/builder`**：`recipes/` 目录当前不存在；flat-dot 形式不与既有路由冲突。**不**与 `repos.*` flat-dot 共享 prefix，无父 Outlet 困扰。
4. **state 不入 URL**：builder state 包含可能很长的 yaml 配置；放 URL 会爆炸。MVP 不支持"分享一个搭好的 chain URL"；留 follow-up `web-recipe-builder-share-url-*`。
5. **hard-coded loader / operator 名称列表**：与 registry 自动同步留 follow-up；MVP 阶段名称列表稳定（W2-1..W2-4 / W3-1..W3-7 落地后 6 loaders + ~9 operators），hard-coded 在 `lib/recipe-v2-builder.ts` 顶层；新 loader / operator 加入时手动同步。
6. **per-operator config 用 textarea (yaml string)**：避免每个 operator 写一个表单组件；交互成本 = "user 自己粘 yaml 配置"。MVP 实用够用；字段级 UI 留 follow-up。
7. **yaml stringify 用 js-yaml**：业界标准；apps/web 引入它仅本 change；体积 ~25KB；TypeScript types 通过 `@types/js-yaml` dev dep。
8. **不做 schema 校验**：pydantic 在前端跑不动；用 zod 镜像 RecipeV2 schema 是独立改动量（要维护双份 schema）；MVP 让用户依赖后端 422。
9. **复制 + 下载分两个按钮**：复制用 `navigator.clipboard.writeText`（HTTPS 必需，dev/prod 都满足）；下载用 Blob + URL.createObjectURL 创建 a[href]。test 中 mock clipboard。
10. **router config 用 zod search schema** (可选 `loader?` + `recipe_name?`)：留 future "从 wave 4 别处跳来预填"用，本 change 不实际用。

## 风险

| 风险 | 缓解 |
|---|---|
| dnd-kit 在 jsdom 下拖拽事件不可触发 | 测试不模拟真实拖拽；只测"添加 / 删除 / yaml 序列化"语义；拖排序的 UI 真跑由 user final acceptance + W4-6 playwright 验 |
| js-yaml stringify 与 pydantic 解析的 yaml 兼容性 | pydantic 走的是 PyYAML，与 js-yaml stringify 输出（block style，2-space indent）兼容；AC-2 通过 `yaml.load` round-trip 验证 |
| operator config textarea 输入空字符串 / 仅空白 | `buildRecipeYaml` 把 `""` 当 `{}`；yaml.load("") 返 undefined，需在 builder 里 default `{}` |
| 用户在 textarea 写非法 yaml | "校验" 按钮先解析；非法时显示错误 inline；不阻止下载（让 user 自决） |
| recipe_name 为空导致 yaml `name: ` 非法 | UI 输入框 required + minLength 1；下载按钮在 invalid 状态禁用 |
| 与 W4-1 / W4-2 同名 testid 冲突 | 本 change testid 用 `yaml-preview` / `operator-card-{idx}` 前缀；不与 `row-{idx}` 等冲突 |
| LOADER_NAMES / OPERATOR_NAMES hard-coded 在 packages/core 注册变更时漂移 | 在 builder.tsx 顶部加 comment 指向 .harness/changes/W2-1..4 / W3-1..7 的 design.md，提醒同步；漂移检测留 follow-up |
| pnpm install 锁文件抖动 | 与 W4-2 同模式；sonnet 跑 `pnpm install` |
| @dnd-kit transitive deps（含 react-aria 风格 a11y） | 仅 dnd-kit 自身 + tiny-invariant 等小依赖；不引入大库 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/recipe.py`（RecipeV2 schema 参考）
  - `packages/core/src/dataplat_core/loaders/__init__.py`（LoaderRegistry 名称对照 hard-coded list）
  - `packages/core/src/dataplat_core/operators/__init__.py`（OperatorRegistry 名称对照 hard-coded list）
  - `apps/web/src/routes/repos/$owner.$name/pdf-mineru.tsx`（W4-1 UI 风格参考）
  - `apps/web/src/routes/snapshots/$owner.$name.$hash/rows.tsx`（W4-2 UI 风格参考）
- 应当不动：
  - `apps/api/*`（全部不动；不接 v2 execution）
  - W1-* / W2-* / W3-* / W4-1 / W4-2 已 merge 产物
  - 既有 `apps/web/src/routes/repos*` 路由
- 引用的其他 change：W2-5（RecipeV2 schema）、W4-1（folder form / vi.mock pattern）、W4-2（@tanstack ecosystem pinning）

## 关联 follow-up

- `recipe-v2-execution-endpoint-*`：apps/api 加 POST /repos/{owner}/{name}/recipes-v2/runs（sync 或 async）
- `web-recipe-v2-schema-validate-*`：zod 镜像 RecipeV2 schema 前端校验
- `web-recipe-builder-share-url-*`：state 序列化到 URL fragment 支持分享
- `web-registry-discovery-api-*`：apps/api 暴露 GET /registry/loaders + /registry/operators 让 UI 动态拉
- `web-operator-config-form-*`：每个 operator 字段级 UI 表单
- `web-recipe-v2-dry-run-*`：构建完直接预览 silver row 输出（依赖 execution endpoint）
- `web-recipe-v2-dag-builder-*`：若未来 RecipeV3 引入 DAG，react-flow 切换
