---
change_id: web-ux-nav-repo-form-20260521
phase: implementation
status: done
authored_at: 2026-05-21T05:21:53Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/web-ux-nav-repo-form-20260521
base_commit: 1eb828c
head_commit: fea806a
pr_url: n/a (gh PAT 缺 pr:write)
---

# Implementation

> Phase 2 sonnet 端到端产物。一次 sonnet 调用内完成：编码 + 单元测试 + 端到端验证 + commit。

## 改动文件清单

执行 `git diff --name-only main...HEAD`：

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `apps/web/src/routes/__root.tsx` | edit | 登录态 nav 追加 Repos / New Repo (admin) / Recipes Builder 三链接 | T-1 |
| `apps/web/src/routes/repos.new.tsx` | edit | 加 SCHEMA_IDS_BY_LAYER/ROW_FORMATS 常量；zod schema 扩 schema_id+row_format；useEffect layer 切换默认值；渲染两个 select；onSubmit 传新字段 | T-1 |
| `apps/web/src/lib/api/queries.ts` | edit | CreateRepoRequest 接口加 schema_id?+row_format? 两个 optional 字段 | T-1 |
| `apps/web/src/routes/repos.new.test.tsx` | edit | 提取 mockMutateAsync；新增 Test A（schema 字段渲染）与 Test B（submit payload 含新字段）| T-1 |
| `.harness/changes/web-ux-nav-repo-form-20260521/implementation.md` | new | 本文件 | - |

## 任务完成情况

| Task | 状态 | commit | 备注 |
|---|---|---|---|
| T-1 (nav links + repos/new schema fields) | done | <见 head_commit> | - |

## 测试通过证据

### 单元测试（AC-3）

```text
$ cd apps/web && pnpm exec vitest run src/routes/repos.new.test.tsx

 ✓ src/routes/repos.new.test.tsx (4 tests) 282ms

 Test Files  1 passed (1)
      Tests  4 passed (4)
   Start at  13:21:17
   Duration  2.29s
```

### 全量回归（AC-4）

```text
$ cd apps/web && pnpm exec tsc --noEmit
(0 errors)

$ cd apps/web && pnpm exec vitest run

 Test Files  22 passed (22)
      Tests  64 passed (64)
   Start at  13:21:37
   Duration  3.71s
```

### 自检 AC

**AC-1** static grep:
```text
$ grep -cE 'to="(/repos|/repos/new|/recipes/builder)"' apps/web/src/routes/__root.tsx
3
```
结果 >= 3: PASS

**AC-2** static grep:
```text
$ grep -q 'SCHEMA_IDS_BY_LAYER' apps/web/src/routes/repos.new.tsx && \
  grep -q 'schema_id' apps/web/src/lib/api/queries.ts && \
  grep -q 'row_format' apps/web/src/lib/api/queries.ts && echo "AC-2 OK"
AC-2 OK
```
退出码 0: PASS

**AC-3** behavioral（vitest repos.new.test.tsx）: PASS（见上，4 tests，含 2 新增）

**AC-4** tsc + vitest run: PASS（0 typecheck errors, 64/64 tests pass）

## 偏离 design.md（如有）

无偏离。所有改动严格按 design.md 规格执行：
- nav 顺序：Repos → New Repo(admin) → Jobs(admin) → Observability(admin) → Recipes Builder → username → logout
- `/recipes/builder` Link 使用 `search={{}}` 因 validateSearch 全字段 optional
- layer change 用 `useEffect` watching `selectedLayer` + `setValue`，与 design 决策一致
- schema 字段插入在 visibility 行下方（layer/subtype/visibility 三列行之后），description 之前

## 跨 change / 上游回归

- 全 web vitest: 64/64 PASS（22 files）
- TypeScript noEmit: 0 errors
- self_check AC block: PASS 4/4, FAIL 0

## PR 描述（用于 gh pr create body）

```markdown
## Summary
- `__root.tsx`: 登录态 nav 加 Repos / New Repo(admin only) / Recipes Builder 三入口，消灭"只能手输 URL"的 UX 痛点
- `repos.new.tsx`: layer=silver|gold 时显示 schema_id+row_format 下拉（默认值自动填入），layer 切回 bronze 自动清空，彻底解决 "layer=silver 必须传 schema_id" 的 422 报错
- `queries.ts`: CreateRepoRequest 接口向后兼容扩展（optional 字段）

## Test plan
- [x] AC-1: __root.tsx grep >= 3 link 入口
- [x] AC-2: repos.new.tsx SCHEMA_IDS_BY_LAYER 常量 + queries.ts schema_id/row_format 字段存在
- [x] AC-3: vitest repos.new.test.tsx 4/4 PASS（含 Test A schema 渲染 + Test B submit payload）
- [x] AC-4: tsc --noEmit 0 errors + vitest run 64/64 PASS

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 PR。
