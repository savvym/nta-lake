---
change_id: web-ux-nav-repo-form-20260521
phase: verify
status: APPROVED
verdict: APPROVED
authored_at: 2026-05-21T05:25:39Z
author: verify-reviewer-agent
model_used: opus
verified_against_design: design.md (commit 1eb828c)
verified_impl_commit: fea806a
---

# Verify Review：Web UX 修复——顶部导航 + 新建 repo schema 字段

## 结论

**APPROVED**。4/4 AC PASS（静态 grep 2 条、behavioral vitest 4/4、全量 web 测试 64/64 + tsc 0 errors）；diff 严格落在 design 声明范围内（仅 4 个 web 文件 + 5 个 harness 文档）；不违反 D-1 永不做清单；代码质量审查无 MUST / SHOULD / NICE 级别问题。可直接 merge。

## AC 验证（每条粘命令 + 实际输出）

| AC | kind | 命令 | 输出 | 状态 |
|---|---|---|---|---|
| AC-1 | static | `grep -cE 'to="(/repos\|/repos/new\|/recipes/builder)"' apps/web/src/routes/__root.tsx` | `3` | PASS (>=3) |
| AC-2 | static | `grep -q 'SCHEMA_IDS_BY_LAYER' apps/web/src/routes/repos.new.tsx && grep -q 'schema_id' apps/web/src/lib/api/queries.ts && grep -q 'row_format' apps/web/src/lib/api/queries.ts && echo "AC-2 OK"` | `AC-2 OK` (exit 0) | PASS |
| AC-3 | behavioral | `cd apps/web && pnpm exec vitest run src/routes/repos.new.test.tsx` | `Test Files 1 passed (1) / Tests 4 passed (4)` 含 `renders schema_id+row_format when layer=silver` + `submits schema_id+row_format when creating silver repo` | PASS |
| AC-4 | static (lint + 回归) | `cd apps/web && pnpm exec tsc --noEmit; echo EXIT=$?` 然后 `pnpm exec vitest run` | `EXIT=0`；`Test Files 22 passed (22) / Tests 64 passed (64)` | PASS |

### AC-3 详细输出节选

```text
$ cd apps/web && pnpm exec vitest run src/routes/repos.new.test.tsx
 ✓ src/routes/repos.new.test.tsx (4 tests) 286ms

 Test Files  1 passed (1)
      Tests  4 passed (4)
   Start at  13:24:47
   Duration  2.33s
```

`window.scrollTo` 的 jsdom stderr 警告来自 TanStack Router scroll-restoration（提交后 router.navigate 触发），与本 change 无关，所有 4 测试仍 PASS。

### AC-4 详细输出节选

```text
$ pnpm exec tsc --noEmit
EXIT=0

$ pnpm exec vitest run
 Test Files  22 passed (22)
      Tests  64 passed (64)
   Start at  13:25:13
   Duration  3.40s
```

含原有 60 + 新增 2 + 既有 repos.new 2 = 64 用例全部 PASS，相对 sonnet 报告的"原有 62 + 新 2 = 64"匹配。

## 代码质量审查

### `apps/web/src/routes/__root.tsx`

- **nav 顺序与 design 决策 §5 严格一致**：`Repos`（L33-38）→ `New Repo`（admin 门控 L39-46）→ `Jobs`（admin L49-55）→ `Observability`（admin L56-61）→ `Recipes Builder`（L64-70）→ username → logout。
- **admin 门控**：L39 `{me.role === "admin" && (<Link to="/repos/new" ...)}` 与 design 决策 §6 一致；New Repo 仅 admin 可见，普通用户不会看到然后吃 403。
- **`/recipes/builder` 用 `search={{}}`**：与现有 Jobs Link 的显式 search prop 模式一致（TanStack Router validateSearch 全 optional 字段），impl 报告已声明。
- 样式 `text-sm text-gray-700 hover:underline` 沿用现有规范。
- 无新增 `any` / `as any`。
- 小观察：现有 nav 用了两个独立的 `{me.role === "admin" && ...}` 表达式（L39-46 单独一个 New Repo；L47-63 包了 Jobs+Observability 的 fragment）。可以合并成一个 fragment 但不强求——保持当前形态更易后续单独调整 New Repo 入口可见性。**NICE TO HAVE 都算不上，仅作为观察。**

### `apps/web/src/routes/repos.new.tsx`

- **常量定义清晰**：L24-30 `SCHEMA_IDS_BY_LAYER` + `ROW_FORMATS`，含注释指向 `_builtin.py` 权威源 + follow-up 拉取 API 路径，符合 design 风险栏第 2 条缓解。
- **zod schema 扩展正确**：L39-40 `schema_id?: string` + `row_format?: enum(parquet, jsonl)`，optional 与 design 一致。
- **layer 切换 reset 逻辑（L71-83）**：silver → `silver-text-v1`+`parquet`；gold → `gold-sft-v1`+`parquet`；bronze (else 分支) → `setValue(..., undefined)`，与 design 决策 §2/§3 严格一致。useEffect 依赖 `[selectedLayer, setValue]` 正确。
- **bronze 不传 schema_id/row_format**：L100-101 `parsed.data.schema_id || undefined`；bronze 时 useEffect 把 form 值 set 成 undefined，`undefined || undefined = undefined`，CreateRepoRequest 字段 optional，序列化时不会发到后端 → 不触 422。✓ 符合 design 关键约束。
- **silver|gold 渲染 select（L193-224）**：用 `getByLabelText` 友好的 `htmlFor`/`id` 配对；选项来自 `SCHEMA_IDS_BY_LAYER[selectedLayer]`，**`?? []` fallback 兜底**避免 undefined 访问。
- 视觉：schema 字段在 visibility 行下方、description 之前，符合 design 决策 §7 "主表单视觉变化最小"。
- 无 `any`，无 hack。

### `apps/web/src/lib/api/queries.ts`

- `CreateRepoRequest` 接口加 `schema_id?: string | null` + `row_format?: 'parquet' | 'jsonl' | null`（L86-87），全 optional 不破坏既有 caller，符合 design 风险栏第 5 条。
- type 与后端 `apps/api/dataplat_api/schemas/repo.py` 的 payload 字段对齐（design § 交叉引用清单已确认后端已就绪）。

### `apps/web/src/routes/repos.new.test.tsx`

- **真实行为测试**，不是空 mock 过：
  - Test "renders schema_id+row_format when layer=silver" 用 `fireEvent.change(layer, "silver")` 触发 useEffect → 断言 `getByLabelText("schema_id")` 出现 + 默认值 `silver-text-v1`/`parquet`。覆盖 reset on layer change 行为。
  - Test "submits schema_id+row_format when creating silver repo" 填 owner/name/layer → 点 `^创建$` → 断言 `mockMutateAsync` 被以 `objectContaining({schema_id, row_format})` 调用。覆盖 onSubmit payload。
- `mockMutateAsync` 提到模块顶层正确（避免每次 mount 创建新 vi.fn() 难追踪调用）。
- `^创建$` 的精确 regex 避开和"创建中…" 撞——细节考虑到位。
- 没有引入 strict any。

## 范围 / D-1 合规审查

### 范围内文件（`git diff main...HEAD --name-only`）

```
.harness/changes/web-ux-nav-repo-form-20260521/design.md          (Phase 1)
.harness/changes/web-ux-nav-repo-form-20260521/design_review.md   (Phase 1 模板)
.harness/changes/web-ux-nav-repo-form-20260521/implementation.md  (Phase 2)
.harness/changes/web-ux-nav-repo-form-20260521/summary.md         (流程 SoT)
.harness/changes/web-ux-nav-repo-form-20260521/verify_review.md   (Phase 3 本文件)
apps/web/src/lib/api/queries.ts                                   (in scope)
apps/web/src/routes/__root.tsx                                    (in scope)
apps/web/src/routes/repos.new.test.tsx                            (in scope)
apps/web/src/routes/repos.new.tsx                                 (in scope)
```

- **零后端改动**：`apps/api/**` 未触。✓
- **零 generated.ts 改动**：`packages/api-types/src/generated.ts` 未触。✓
- **零 Recipes Builder 内部逻辑改动**（Change B 边界保持清晰）。✓
- **零 routers / services / schemas 改动**。✓
- 与 design § 范围声明严格匹配。

### D-1 永不做清单合规

- 不引入 branch / merge / cherry-pick / rollback / row-diff / Asset / manifest 强制 / bronze 强 schema / silver 文件树。✓
- 本 change 仅前端表单 + nav，无 storage / DB schema 变动。✓
- Phase 1 reviewer 必查项全部通过。

## 发现的问题（按严重度）

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

无。（合并两个 admin 门控 fragment 的小重构不计入；当前形态对后续单独迭代 New Repo 入口更友好。）

## 建议下一步

直接 merge 到 main + close change：

1. Application Owner 把 summary.md 阶段进度表 Phase 3 行更新为 `approved` / `APPROVED` / 本文件 commit sha。
2. 合并 `change/web-ux-nav-repo-form-20260521` → `main`。
3. 在用户访问的 web UI 上 manual smoke test（建议）：
   - 登录 admin → 顶 nav 见 Repos / New Repo / Jobs / Observability / Recipes Builder
   - 普通用户登录 → 仅见 Repos + Recipes Builder（无 New Repo / Jobs / Observability）
   - `/repos/new` 切 layer=silver → schema_id 显示并默认 `silver-text-v1`，row_format 默认 `parquet`；切回 bronze 字段消失；提交 silver 成功不再吃 422
4. 用户原话两条 UX 缺陷视为闭环；如还有未覆盖入口（如 repo 详情页跳 pdf-mineru / snapshots / recipes builder 的上下文按钮），落到已规划的 follow-up `web-repo-detail-contextual-links-*`。
5. 关注的 follow-up（来自 design § 关联 follow-up）按既定优先级派发：`web-schemas-api-*`（schema ≥ 5 时启动）、`web-schema-id-tooltip-*`、`web-nav-mobile-*`。
