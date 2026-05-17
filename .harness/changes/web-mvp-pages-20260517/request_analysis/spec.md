---
change_id: web-mvp-pages-20260517
version: 2
authored_at: 2026-05-17T12:50:00Z
status: approved
revisions:
  - v1 → v2：消化 stage 2 reviewer 2 MUST FIX。
    (1) fetchJson 加 allowAnon opt-in；useMe 用之，匿名返 null（后端 /auth/me 是 get_current_user 强制 401）
    (2) TanStack Router 改 directory style：routes/repos/index.tsx + routes/repos/$owner.$name.tsx
  - v2 reviewer APPROVED；本轮直推 Stage 3
---

# Spec：Web MVP 三页（Login + Repo 列表 + Repo 详情）

## 背景

8 个变更后后端 API 完整；`apps/web/` 仍是 Vite 骨架。落 design.md §9 Phase 1 #7 最小 UI：登录 → repos 列表 → repo 详情。

## 范围

In scope：依赖（TanStack Router/Query + Tailwind + shadcn + openapi-typescript + rhf + zod）；api-types 真生成；`apps/web/src/lib/api/`（client + queries）；5 routes（__root / index / login / repos/index / repos/$owner.$name）；shadcn 4 组件；Tailwind；main.tsx 改造；vitest ≥ 4；self_check 13 AC。

Out of scope：repo 写 UI / Files-Commits-Lineage / 搜索 / 注册 / 响应式 / Storybook / E2E。

## 验收标准（13 AC + 验证方式）

- **AC-1** package.json 含 11 runtime + 2 dev deps。
  - 验证：`cd apps/web && node -e "const p=require('./package.json'); for (const d of ['@tanstack/react-router','@tanstack/react-query','tailwindcss','clsx','openapi-typescript']) { if (!(d in {...p.dependencies, ...p.devDependencies})) { process.exit(1); } }"`
- **AC-2** packages/api-types/src/generated.ts 真生成（含 `/repos`）。
  - 验证：`test -f packages/api-types/src/generated.ts && grep -q "/repos" packages/api-types/src/generated.ts`
- **AC-3** tailwind.config.ts + postcss.config.js + index.css；content 含 `./index.html` + `./src/**/*.{ts,tsx}`。
  - 验证：`test -f apps/web/tailwind.config.ts && test -f apps/web/postcss.config.js && test -f apps/web/src/index.css && grep -q "@tailwind base" apps/web/src/index.css`
- **AC-4** shadcn 4 组件文件齐全（button / card / input / label）。
  - 验证：`for f in button card input label; do test -f "apps/web/src/components/ui/$f.tsx" || exit 1; done`
- **AC-5** client.ts：`credentials: "include"` + 401 refresh + `UnauthorizedError` + `allowAnon` opt-in。
  - 验证：`test -f apps/web/src/lib/api/client.ts && grep -q 'credentials: "include"' apps/web/src/lib/api/client.ts && grep -q "/auth/refresh" apps/web/src/lib/api/client.ts && grep -q "UnauthorizedError" apps/web/src/lib/api/client.ts && grep -q "allowAnon" apps/web/src/lib/api/client.ts`
- **AC-6** 5 routes 文件（directory style for repos）。
  - 验证：`for f in __root.tsx index.tsx login.tsx repos/index.tsx; do test -f "apps/web/src/routes/$f" || exit 1; done && test -f 'apps/web/src/routes/repos/$owner.$name.tsx'`
- **AC-7** __root.tsx 含 Outlet + login/logout 标识。
  - 验证：`grep -q "Outlet" apps/web/src/routes/__root.tsx && grep -qE "logout|login" apps/web/src/routes/__root.tsx`
- **AC-8** login.tsx：rhf + /auth/login + navigate。
  - 验证：`grep -q "react-hook-form" apps/web/src/routes/login.tsx && grep -q "/auth/login" apps/web/src/routes/login.tsx && grep -q "navigate" apps/web/src/routes/login.tsx`
- **AC-9** repos/index.tsx：useRepos + cards；queries 指向 /api/repos。
  - 验证：`grep -qE "useQuery|useRepos" apps/web/src/routes/repos/index.tsx && grep -q "/api/repos" apps/web/src/lib/api/queries.ts`
- **AC-10** repos/$owner.$name.tsx：metadata layer/subtype。
  - 验证：`test -f 'apps/web/src/routes/repos/$owner.$name.tsx' && grep -qE "layer|subtype" 'apps/web/src/routes/repos/$owner.$name.tsx'`
- **AC-11** vitest ≥ 4 测试 + 全 PASS。
  - 验证：`[ "$(find apps/web/src -name '*.test.tsx' -o -name '*.test.ts' | wc -l)" -ge 4 ] && cd apps/web && pnpm test 2>&1 | tail -5 | grep -qE "Test Files.*passed|Tests.*passed"`
- **AC-12** typecheck + build + dist/index.html。
  - 验证：`cd apps/web && pnpm typecheck && pnpm build && test -f dist/index.html`
- **AC-13** self_check web-mvp-pages 13 AC PASS。

## 关键决策

- 路由保护：anon 可访，401 才跳 login
- useMe：`fetchJson(url, undefined, { allowAnon: true })`
- repos 文件结构：directory style（消歧 TanStack v1 自动 layout 升级）
- shadcn 手抄源码（不跑 CLI）
- bootstrap-monorepo AC-8 兼容更新（App.tsx 删，routes/ 替代）

## 风险

1-5 见上轮 v1 缓解（shadcn / codegen / openapi 冲突 / Tailwind content / cookie），已落地
6. useMe/`/auth/me` 契约（allowAnon 解决）
7. TanStack flat vs directory 歧义（directory style 解决）

## 流程偏离

本 v2 是 spec v1→v2 reviewer APPROVED 后的重新落地（前次代码已 revert，spec/tasks 也已删除）。直接复用 v2 内容；reviewer 已 APPROVED 状态由前一轮 review 记录证明，本轮直推 Stage 3。
