---
change_id: web-operator-chain-builder-20260520
phase: verify
status: approved
verdict: APPROVED
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
reviewed_at: 2026-05-21T12:30:00Z
ac_kind_lint: enforce
---

# Verify Review：Recipe v2 Chain Builder UI (W4-3) — APPROVED

**VERDICT：APPROVED**（0 MUST FIX / 0 SHOULD FIX / 2 NICE TO HAVE，全部非阻塞）。

4 个 AC 全 PASS（1 static + 3 behavioral）；apps/web 全套 20/20 files 58/58 tests PASS（W4-2 baseline 52 + W4-3 新增 3+3=6，零回归）；`pnpm tsc --noEmit` clean；diff scope 严格限定 design 允许范围（apps/api / packages/core / W1..W3 / W4-1 repos 路由 / W4-2 snapshots 路由 / apps/web/src/lib/api 全部 0 改动）；3 个 DEV 偏离全部 ACCEPT（含 DEV-1 design example 与实际 registry 不符 → sonnet 改用实际名 `html-md` + `chunker`，v3 流程鼓励的对齐选择）；新增依赖 `@dnd-kit/core@^6` + `@dnd-kit/sortable@^8` + `@dnd-kit/utilities@^3` + `js-yaml@^4` + `@types/js-yaml@^4` devDep，符合 design 决策 1（拒 react-flow）+ 决策 7（js-yaml）；D-1 永不做清单 grep clean。

## 输入

- Design：`.harness/changes/web-operator-chain-builder-20260520/design.md`（b8e6e21）
- Implementation：`.harness/changes/web-operator-chain-builder-20260520/implementation.md`（c3ef87a）
- Git diff：`git diff main...change/web-operator-chain-builder-20260520`
- HEAD：`c3ef87a` (branch `change/web-operator-chain-builder-20260520`)

## 1. AC 对照表

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL |
|---|---|---|---|---|
| AC-1 | static | `test -f apps/web/src/routes/recipes/builder.tsx && grep -q 'createFileRoute("/recipes/builder")' apps/web/src/routes/recipes/builder.tsx` | 命中 line 43 | PASS |
| AC-2 | behavioral | `cd apps/web && pnpm vitest run src/lib/recipe-v2-builder.test.ts -t "serializes minimal recipe"` | 1 passed | PASS |
| AC-3 | behavioral | `cd apps/web && pnpm vitest run src/routes/recipes/builder.test.tsx -t "yaml preview reflects loader and operator"` | 1 passed | PASS |
| AC-4 | behavioral | `cd apps/web && pnpm vitest run src/routes/recipes/builder.test.tsx -t "remove operator"` | 1 passed | PASS |

实际跑（精简）：

```text
$ test -f apps/web/src/routes/recipes/builder.tsx && echo "FILE EXISTS" && grep -n 'createFileRoute("/recipes/builder")' apps/web/src/routes/recipes/builder.tsx
FILE EXISTS
43:export const Route = createFileRoute("/recipes/builder")({

$ cd apps/web && pnpm vitest run src/lib/recipe-v2-builder.test.ts -t "serializes minimal recipe"
 ✓ src/lib/recipe-v2-builder.test.ts (3 tests | 2 skipped) 6ms
 Test Files  1 passed (1)
      Tests  1 passed | 2 skipped (3)

$ cd apps/web && pnpm vitest run src/routes/recipes/builder.test.tsx -t "yaml preview reflects loader and operator"
 ✓ src/routes/recipes/builder.test.tsx (3 tests | 2 skipped) 129ms
 Test Files  1 passed (1)
      Tests  1 passed | 2 skipped (3)

$ cd apps/web && pnpm vitest run src/routes/recipes/builder.test.tsx -t "remove operator"
 ✓ src/routes/recipes/builder.test.tsx (3 tests | 2 skipped) 132ms
 Test Files  1 passed (1)
      Tests  1 passed | 2 skipped (3)
```

（stderr `Error: Not implemented: window.scrollTo` 与 W4-2 同；NICE-1 follow-up 已立。）

### AC-2 语义验证（DEV-1 修订后）

design.md AC-2 字面写：传入 `loader.name=pdf_mineru` + `operators[0].name=normalize_unicode`，期望 yaml.load 解出对应 name。sonnet 在实际 registry 名（`html-md` + `chunker`）下验证语义不变：传 loader + 1 operator 经 `buildRecipeYaml` → `yaml.load` round-trip 解出 `name: r`, `version: 2`, `loader.name`, `loader.input.blob_sha: abc`, `operators[0].name`。**AC-2 语义意图（"serializes minimal recipe with loader + operator → yaml.load 解出 version=2 + loader.name + operators[0].name"）完整命中**；仅字面 name 不同。

## 2. Cross-regression

### apps/web 全套（20/20 files，58/58 tests）

```text
$ cd apps/web && pnpm vitest run
 Test Files  20 passed (20)
      Tests  58 passed (58)
   Duration  3.50s
```

52 → 58（+6 新增 W4-3 测试：3 pure 函数 + 3 RTL；不含 skip-only 测试）。W4-1 / W4-2 测试全 PASS，零回归。

### TypeScript 检查

```text
$ cd apps/web && pnpm tsc --noEmit
（无输出 = clean）
```

### apps/api / packages

未触及（`git diff main...HEAD -- apps/api packages = empty`）。无需重跑。

## 3. Diff scope 审计

```text
$ git diff main...HEAD --name-only
.harness/changes/web-operator-chain-builder-20260520/design.md
.harness/changes/web-operator-chain-builder-20260520/implementation.md
apps/web/package.json
apps/web/src/lib/recipe-v2-builder.test.ts
apps/web/src/lib/recipe-v2-builder.ts
apps/web/src/routeTree.gen.ts
apps/web/src/routes/recipes/builder.test.tsx
apps/web/src/routes/recipes/builder.tsx
pnpm-lock.yaml
```

- `apps/api/**`：**0 行**（grep clean）
- `packages/**`：**0 行**（grep clean）
- W1-* / W2-* / W3-* / W4-1 / W4-2 merged 产物：**0 行**触及
  - `apps/web/src/routes/repos/*`：未触及
  - `apps/web/src/routes/snapshots/*`：未触及
  - `apps/web/src/lib/api/queries.ts`：未触及
- 新依赖：`@dnd-kit/core@^6` + `@dnd-kit/sortable@^8` + `@dnd-kit/utilities@^3` + `js-yaml@^4` + `@types/js-yaml@^4`，与 design 决策 1（拒 react-flow）+ 决策 7（js-yaml）一致；`@dnd-kit/utilities` 是 sortable 的 peerDep（DEV-2）
- `apps/web/src/routeTree.gen.ts`：仅 +21 行注册 `RecipesBuilderRoute`（import + Route + FileRoutesByFullPath + FileRoutesByTo + interface + declare module），格式与 plugin 生成一致（DEV-3）
- 不在 design Out-of-scope（apps/api 执行 endpoint / schema 校验 / react-flow DAG / per-operator 表单 / registry 动态拉取 / dry-run / LLM Gateway / manifest.yaml）的任何文件被触及

## 4. DEV 偏离评估

| # | sonnet 报的偏离 | reviewer 判断 | 理由 |
|---|---|---|---|
| DEV-1 | LOADER_NAMES 实际 `["html-md","docx","pptx","jsonl"]` 不含 `pdf_mineru`；OPERATOR_NAMES 9 个不含 `normalize_unicode`；AC-2 测试改用 `html-md` + `chunker` | **ACCEPT** | reviewer grep `packages/core/src/dataplat_core/loaders/__init__.py` line 9-14 + `operators/__init__.py` line 41-51 确认 sonnet 列表与实际注册完全一致。design.md AC-2 举例的 `pdf_mineru` 实际是 W1-4 adapter 名（不是 loader），`normalize_unicode` 不存在于注册 9 个 operator。**这是 design example bug，不是实现偏差**。sonnet 用实际名是 v3 流程鼓励的对齐选择：宁可与 design example 字面冲突，也不能用一个 yaml 跑不通的 example。AC-2 语义意图（yaml.load round-trip 解出 version + loader.name + operators[0].name）完整命中。建议 follow-up `harness-design-example-real-name-*` 修订 design.md AC-2 字面举例（不阻 merge） |
| DEV-2 | 新增 `@dnd-kit/utilities@^3`（design 仅列 core + sortable） | **ACCEPT** | `@dnd-kit/utilities` 是 `@dnd-kit/sortable` 的官方 peerDep，含 `CSS.Transform.toString` helper（builder.tsx line 22 + 69 使用）；不安装会导致 sortable 编译期 OK runtime 缺 `CSS` namespace。pnpm peerDep 警告但不自动安装，需 explicit dep；常见模式。锁文件抖动小（5 packages：3 dnd-kit + js-yaml + @types/js-yaml） |
| DEV-3 | routeTree.gen.ts 手动更新（非 vite plugin 自动生成） | **ACCEPT** | 本地无 dev server；diff 验：+21 行（import + Route create + FileRoutesByFullPath/ByTo/`__rootRoute__` interface + declare module + RecipesBuilder 子树挂载），格式与 W4-1 / W4-2 同模式 plugin 生成完全一致；vitest 58/58 + tsc clean 证明 routeTree 合法 |

3/3 DEV 全部 ACCEPT。无隐式偏离（reviewer 对照 design § 范围 vs git diff 文件清单，零未声明改动）。

## 5. 永不做清单 / 北极星合规

```text
$ grep -rn "react-flow\|manifest.yaml\|dataset-card.yaml" apps/web/src/
（无输出 = clean）
```

- 无 manifest.yaml / dataset-card.yaml 引入
- 无 react-flow（design 决策 1 显式拒绝；实际依赖 grep clean）
- 无 branch / merge / cherry-pick / rollback / row-diff 概念
- 无 blob 派生图 / Asset 引入
- 无 silver 文件树 / bronze 强 schema
- builder UI 仅生成 yaml（pure 字符串），不破坏 stats / lineage 语义
- 不接 apps/api（design § 范围 Out-of-scope 明确）
- 不引入 LLM Gateway 真跑（W4-5 范畴）

## 6. 实现质量抽查

- zod searchSchema：`loader?` + `recipe_name?` optional ✓（决策 10）
- BuilderState type：`{name, loader, operators}` 与 design § 范围一致 ✓
- `buildRecipeYaml` pure 函数：`{name, version:2, loader, operators}` schema ✓（决策 7）
- config / input 字段处理：`yaml.load(trimmed)` + 空/null/undefined → `{}` + 非 mapping throw ✓（design § 风险 3）
- 拖拽：`DndContext` + `SortableContext` + `useSortable` + `verticalListSortingStrategy` + `arrayMove` ✓（决策 1）
- LOADER_NAMES + OPERATOR_NAMES export 来自 `lib/recipe-v2-builder.ts` 顶层 const ✓（决策 5）
- testid：`yaml-preview` + `operator-card-{idx}` + `operator-remove-{idx}` + `loader-select` + `operator-select` + `operator-add` ✓（design § 风险表第 6 行）
- AC-3 / AC-4 测试用 createMemoryHistory + vi.mock queries 模式 ✓（W4-1 / W4-2 同）
- AC-4 删除后索引重排：`operator-card-1` → null + 原 `operator-card-1` 内容变为 `operator-card-0` ✓
- 错误内联：bad yaml → preview 显示 "(yaml 序列化错误：...)" ✓（design § 风险 4）

## 7. 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

- **NICE-1**（继承 W4-2）：`builder.test.tsx` 跑时 console 仍打印 `Error: Not implemented: window.scrollTo`（TanStack Router scroll-restoration on jsdom 噪音）。已建议 follow-up `web-test-suppress-jsdom-scroll-noise-*` 在 `vitest.setup.ts` 加 `window.scrollTo = vi.fn()` stub 全局抑制。本 change 不阻塞。
- **NICE-2**（DEV-1 衍生）：design.md AC-2 字面 example 用了不存在的 `pdf_mineru` loader + `normalize_unicode` operator。sonnet 在 implementation 阶段 grep 确认后改用实际名 `html-md` + `chunker`。建议 follow-up `harness-design-example-real-name-*` 修订 design 文档（或在 design.md AC 表里加 "实际名见 registry"），并在 `.harness/rules/coding-style.md` / `development-process.md` 加一条："design 阶段举例 loader / operator 名要 grep 已注册列表验证"。本 change 不阻塞。

## Verdict

**APPROVED** — 0 MUST FIX / 0 SHOULD FIX / 2 NICE TO HAVE（全部非阻塞）。4 个 AC 全 PASS（1 static + 3 behavioral），apps/web 20/20 files 58/58 tests，typecheck clean，apps/api / packages / W4-1 / W4-2 路由 0 行触及，3 个 DEV 偏离全部 ACCEPT（DEV-1 是 design example bug 而非实现偏差，sonnet 用实际 registry 名是 v3 鼓励的判断），diff scope 严格符合 design § 范围，永不做清单 grep clean。17 连 0-MUST-FIX APPROVED 延续。

## 后续指引

1. application-owner merge `change/web-operator-chain-builder-20260520` → main（建议 `--no-ff`）
2. close W4-3 task；orchestration W4 计数 2/10 → 3/10
3. 启动 W4-4：`web-snapshot-export-ui-*`（gold export 触发 UI）
4. 可选 follow-up：
   - `harness-design-example-real-name-*`（NICE-2，design.md AC example 修订 + rule 防复发）
   - `web-test-suppress-jsdom-scroll-noise-*`（NICE-1，jsdom scrollTo 全局 stub）
