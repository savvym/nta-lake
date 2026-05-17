---
change_id: web-mvp-pages-20260517
version: 2
authored_at: 2026-05-17T12:50:00Z
---

# Tasks

## T-1 依赖 + Tailwind 配置

- `pnpm add` runtime（@tanstack/react-router / react-query / rhf / zod / tailwindcss(v3) / postcss / autoprefixer / clsx / tailwind-merge / cva / lucide-react）
- `pnpm add -D` dev（@tanstack/router-vite-plugin / openapi-typescript）
- tailwind.config.ts content 含 `./index.html` + `./src/**/*.{ts,tsx}`
- postcss.config.js + src/index.css
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-1, AC-3

## T-2 api-types 真生成

- packages/api-types/package.json: `generate` 改为 `openapi-typescript openapi.json -o src/generated.ts`
- 跑 `pnpm --filter @dataplat/api-types generate`
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-2

## T-3 shadcn 4 组件 + utils.cn

- apps/web/src/lib/utils.ts（cn = twMerge + clsx）
- 拷 button / card / input / label 源码
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-4

## T-4 client + queries

- client.ts：fetchJson + UnauthorizedError + ApiError + FetchOptions(allowAnon) + 401 refresh
- queries.ts：useMe（allowAnon: true）+ useRepos + useRepo
- depends_on: T-1, T-2 / estimated_stage: stage-3 / AC: AC-5

## T-5 router setup + __root + index + login

- vite.config.ts 加 TanStackRouterVite plugin + routeFileIgnorePattern 排测试
- routes/__root.tsx（layout + nav）
- routes/index.tsx（redirect /repos）
- routes/login.tsx（rhf + POST /auth/login）
- depends_on: T-1, T-3, T-4 / estimated_stage: stage-3 / AC: AC-6/7/8

## T-6 repos directory routes

- routes/repos/index.tsx（list）
- routes/repos/$owner.$name.tsx（detail）
- depends_on: T-3, T-4, T-5 / estimated_stage: stage-3 / AC: AC-9, AC-10

## T-7 main.tsx 改造

- 删 App.tsx；改 main.tsx 用 QueryClient + RouterProvider + routeTree.gen.ts
- build script 改 `vite build && tsc --noEmit`（routeTree 由 vite plugin 生成，必须先跑 vite）
- depends_on: T-5, T-6 / estimated_stage: stage-3 / AC: AC-6

## T-8 测试 ≥ 4

- App.test.tsx 改 router smoke（mock useMe/useRepos）
- routes/login.test.tsx（rhf required → "必填"）
- lib/api/client.test.tsx（c1 默认 refresh 重试 + c2 allowAnon → null）
- routes/repos.test.tsx（mock useRepos → 卡片字段）
- depends_on: T-5, T-6, T-7 / estimated_stage: stage-3 / AC: AC-11

## T-9 build + typecheck

- `pnpm typecheck` 0 error + `pnpm build` → dist/index.html
- depends_on: T-7, T-8 / estimated_stage: stage-3 / AC: AC-12

## T-10 self_check + bootstrap-monorepo AC-8 兼容更新

- scripts/_self_check.sh 追加 `run_web_mvp_pages` 13 AC + filter
- 修 bootstrap-monorepo AC-8：`App.tsx OR routes/` 二选一
- depends_on: T-1~T-9 / estimated_stage: stage-3 / AC: AC-13

## process_tasks（T-11~T-16）

- T-11 stage-2 spec/tasks review（已完成；v1 → v2 APPROVED；本轮复用）/ stage-2
- T-12 stage-4 coding review（独立 reviewer）/ stage-4
- T-13 stage-5/6 test_report + review / stage-6
- T-14 stage-7 CI 验证（self_check 全仓）/ stage-7
- T-15 stage-9 deploy verify（skipped 静态资源）/ stage-9
- T-16 stage-10 close + 更新 session_handoff / stage-10
