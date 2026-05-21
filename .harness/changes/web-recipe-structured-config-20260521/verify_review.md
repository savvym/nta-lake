---
change_id: web-recipe-structured-config-20260521
phase: verify
status: APPROVED
verdict: APPROVED
authored_at: 2026-05-21T13:50:00Z
author: verify-reviewer-agent
model_used: opus
verified_against_design: design.md (commit 3748095)
verified_impl_commit: 79f0503
---

# Verify Review：Recipe Builder 结构化算子配置 + Run 按钮

## 结论

**APPROVED**：5 条 AC 全部 PASS；无 MUST FIX；无 D-1 违反；范围严格遵守设计 In-scope 9 文件清单；可直接 merge。

## AC 验证（每条粘命令 + 实际输出）

| AC | kind | 命令 | 输出 | 状态 |
|---|---|---|---|---|
| AC-1 | static | `test -f apps/api/dataplat_api/routers/operators.py && grep -qE '@router.get\(' apps/api/dataplat_api/routers/operators.py && grep -q 'operators_router' apps/api/dataplat_api/main.py` | exit=0 | PASS |
| AC-2 | behavioral | `cd apps/api && uv run pytest tests/test_operators_endpoint.py -x -q` | `1 passed in 1.63s` | PASS |
| AC-3 | static | `test -f apps/web/src/components/operator-config-form.tsx && grep -q 'OperatorConfigForm' apps/web/src/routes/recipes/builder.tsx && grep -qE 'useOperatorsQuery\|useCreateRunFromYaml' apps/web/src/lib/api/queries.ts` | exit=0 | PASS |
| AC-4 | behavioral | `cd apps/web && pnpm exec vitest run src/routes/recipes/builder.test.tsx` | `Test Files 1 passed (1) / Tests 5 passed (5)` 含新 Test A（dedup enum→select）+ Test B（run-recipe-btn → mutateAsync called with yaml body） | PASS |
| AC-5 | static (lint + 全量回归) | `cd apps/web && pnpm exec tsc --noEmit` + `pnpm exec vitest run` + `cd apps/api && uv run pytest -q` | tsc 无输出（0 错误）；web `Test Files 22 passed (22) / Tests 66 passed (66)`；api `52 passed, 132 skipped in 1.88s` | PASS |

## 代码质量审查

### 后端 `routers/operators.py`

- `prefix="/operators"`，单 endpoint，仅 `Depends(get_current_user)`，**未** `Depends(require_admin)` — 与设计决策 #1（不加 admin gate）一致
- response_model 定义 `list[OperatorMetaResponse]`，schema `config_schema: dict[str, Any]` 满足设计风险表"pydantic v2 序列化 JSON-Schema dict"
- 按 `sorted(OperatorRegistry.list_names())` 字典序排（设计决策 #12）
- `import dataplat_core.operators as _ops_module  # noqa: F401` 触发自动注册 —— 与 cas-storage 时 main.py 的 adapter/processor noqa import 同模式
- `cls.spec` 直接拿类 attr —— 与设计风险表"OperatorRegistry.get(name) 返回类而非实例"的缓解一致

### 组件 `operator-config-form.tsx`

- `_shouldFallback` 三条件：`schema undefined / type≠object / 无 properties key` → fallback yaml。完整覆盖设计 § 约束的"其他类型 / object / array → fallback YAML textarea"
- `_hasUnsupportedProp` 遇到非 string/integer/number/boolean 立即整表单 fallback —— 与设计约束"5 种基础 type"匹配；string+enum 分支在 `renderInput` 中通过 `Array.isArray(propDef.enum)` 分流到 `<select>`
- 空 properties → "（无可配置参数）"占位 —— 妥善处理 schema 形状合法但无字段的边界
- required 字段红色 `*` —— 与设计风险表"required 未填后端 422"的"UI 标 required"一致
- 完全无 `any` 类型；用 `PropDef` / `SchemaLike` / `Record<string, unknown>`

### `builder.tsx` 集成

- `useOperatorsQuery()` 替代 `OPERATOR_NAMES` 硬编码，运行时拉取 —— 与设计决策 #5 一致
- `LOADER_NAMES` 保留硬编码 —— 与设计决策 #6 一致
- Operator card schema 由 `schemaForOp(op.name)` 动态查；`OperatorConfigForm` 收到 `value={op.configObject}` + `fallbackYaml={op.configYaml}` + 双 onChange —— 双轨切换正确
- `handleRun` 用 `runMutation.mutateAsync(displayYaml)` 提交序列化后的 yaml；成功 `runFeedback = "✓ 已提交 run_id=…"` + Link to `/jobs` —— 与设计决策 #8 一致
- "运行 Recipe" 按钮 `{isAdmin && (...)}` 由 `useMe().data?.role === "admin"` 控制 —— 与设计决策 #7 admin-only 一致
- `disabled={runMutation.isPending}` + 按钮文本"运行中…" —— UX 完备
- `operatorNames.length === 0` 时 `+ Add Operator` 按钮 `disabled` —— 防 add 空名 operator

### `queries.ts` `useCreateRunFromYaml`

- 显式 `fetch("/api/pipelines/runs:from-yaml", { headers: { "Content-Type": "text/yaml" }, body: yamlBody })` —— 不复用 `fetchJson` 避免被强制 JSON，与设计风险表一致
- 错误处理 `try { data.detail } catch { /* parse error */ }` —— 健壮
- 返回类型 `{ run_id: string; job_id?: string }` —— 与后端 `PipelineRunCreatedResponse`（pipelines.py）兼容（job_id 可选这点宽松些，不阻塞）

### `recipe-v2-builder.ts` 双轨序列化

- 第 71-73 行：`Object.keys(op.configObject).length > 0 ? op.configObject : parseYamlField(op.configYaml)` —— 严格的"configObject 非空时优先"逻辑；空对象退回 yaml parse；同一时刻只用一种 —— 与设计决策 #3 + #4 一致
- W4-3 三个旧 buildRecipeYaml unit test 全部 PASS（已直接复跑），添加 `configObject: {}` 是类型-only 补全（空 obj → 走 yaml parse 分支），断言逻辑不变 —— 与设计"保留 W4-3 测试不动"的意图一致

### 测试真实性

- **Test A（dedup enum→select）**：通过 `screen.getByTestId("op-cfg-0-key")` 拿到真实渲染的 DOM 节点；断言 `tagName === "SELECT"` + 选项数组含 `text` / `source_blob`。**非 mock passthrough**，验证了 OperatorConfigForm 真在 jsdom 里渲染了 `<select>` 节点 —— 真实行为测试
- **Test B（运行 Recipe → mutateAsync）**：`fireEvent.click(runBtn)` 后 `expect(mockRunMutateAsync).toHaveBeenCalledTimes(1)`，并断言传参 `calledYaml` 是 string 含 `"my-recipe"` —— 验证了 admin-gate 显示 + onClick 真实调用 + yaml payload。**非 mock passthrough**
- 测试 3（旧"shows error inline"）被修改为验证 chunker number input → yaml 联动（impl 报告 D-1 已声明）：测试名 vs 内容轻微脱节（NICE TO HAVE，见下）

## 范围 / D-1 合规审查

### 改动文件清单（与 design § In scope 对照）

| 文件 | design In-scope | 实际 | 一致 |
|---|---|---|---|
| `apps/api/dataplat_api/routers/operators.py` | new | new | ✓ |
| `apps/api/dataplat_api/main.py` | edit（include router 1 行） | +2 行 | ✓ |
| `apps/api/tests/test_operators_endpoint.py` | new | new | ✓ |
| `apps/web/src/lib/api/queries.ts` | edit（+OperatorMeta / +useOperatorsQuery / +useCreateRunFromYaml） | +40 行 3 个 export | ✓ |
| `apps/web/src/lib/recipe-v2-builder.ts` | edit（删 OPERATOR_NAMES / +configObject） | -10 +21 行 | ✓ |
| `apps/web/src/components/operator-config-form.tsx` | new | new | ✓ |
| `apps/web/src/routes/recipes/builder.tsx` | edit | -28 +113 行 | ✓ |
| `apps/web/src/routes/recipes/builder.test.tsx` | edit | -2 +128 行 | ✓ |
| `apps/web/src/lib/recipe-v2-builder.test.ts` | （未在 design 列出；impl D-2 声明） | -3 +5 行（fixture 加 configObject: {}） | ✓（minimal 类型修复；不改断言） |

**结论**：9 文件全部在 design In-scope 范围内或属 minimal 类型修复（D-2 声明的合规偏离）。无任何 out-of-scope 改动：
- `packages/core/` 未触；OperatorRegistry / Loader / OperatorSpec 零修改
- `apps/api/dataplat_api/routers/pipelines.py` / `process.py` 未触
- `apps/web/src/routeTree.gen.ts` 未触（无新路由，Run 是已有 builder 页面的按钮）
- W1..W4-10 已 merge 产物未触

### D-1 永不做清单合规

- 新代码无 `manifest.yaml` / branch / merge / cherry-pick / rollback / row-diff / blob 派生图 / Asset 概念
- 后端只读 metadata endpoint；前端只是 form 渲染 + 调用已存在的 `POST /pipelines/runs:from-yaml`
- `grep -irE 'manifest\.yaml|branch|merge|cherry-pick|rollback|row.?diff|^Asset|delta_chunk|change_set'` 在新建两个文件中 zero match
- ✓ D-1 完全遵守

### 隐式偏离审计

impl § 偏离 已声明 D-1 / D-2 / D-3 三处：
- D-1：旧 test 3 改为验证结构化 input 联动 yaml —— 合理（原 test 依赖的 textarea 不再存在；保留测试意图）
- D-2：`recipe-v2-builder.test.ts` 三处加 `configObject: {}` —— 类型 only 修复（BuilderState 加了新字段必须补）；空 obj 走 yaml parse 分支，断言逻辑保持 —— 合规
- D-3：`useCreateRunFromYaml` 与现有 `useCreatePipelineRun` 行为重复 —— design.md 第 47 行明确要求新 hook 名；保留旧 hook 避免破坏 W4-3 pipeline-ui-tab 引用 —— 合规

**未发现隐式偏离**（design 没声明但实际发生）。

## 发现的问题（按严重度）

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

1. `builder.test.tsx` 第 202 行 it 名 "yaml preview shows error inline when operator config is invalid yaml" 已不再测试 "error inline"（测试体现在验证 number input → yaml 联动）。建议下个 change 顺手把 it 名改为 "structured number input updates yaml preview"。impl D-1 偏离已声明，仅为可读性建议，不阻塞。
2. `useCreateRunFromYaml` 返回类型 `{ run_id: string; job_id?: string }`（job_id 可选）；后端 `PipelineRunCreatedResponse` 实际总返 `run_id` + `job_id`，前端类型 `job_id?` 略宽松。可在 follow-up `web-pipeline-types-tighten-*` 中收紧。

## 建议下一步

直接 merge change 分支到 main。建议步骤：
1. application-owner 把 `summary.md` frontmatter `phase: design / status: in_progress` 更新为 `phase: completed / status: done`，并填表"阶段进度"中三阶段 verdict、commit、产物
2. `git checkout main && git merge --no-ff change/web-recipe-structured-config-20260521 -m "merge web-recipe-structured-config: Recipe Builder 结构化算子配置 + Run 按钮"`
3. close change 目录（确保 verify_review.md + summary.md 与 implementation.md 都 commit 到 main）
4. 通知用户验收：在 dev 环境跑 `pnpm dev` + `uv run uvicorn dataplat_api.main:app --reload`，打开 `/recipes/builder`，确认 admin 用户能看到"运行 Recipe"按钮，添加 dedup operator 后能看到 key 字段 select with text/source_blob 选项
