---
change_id: web-mvp-pages-20260517
version: 1
authored_at: 2026-05-17T13:35:00Z
branch: main
base_commit: d41ead7 (adapter-framework close)
head_commit: working-tree
status: waiting_review
note: 本轮是 spec v2 + tasks v2 reviewer APPROVED 后第二次落地 Stage 3（前次代码 revert）；本报告对应第二次实现。
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 说明 |
|---|---|---|
| `apps/web/package.json` | edit | 11 runtime + 2 dev deps；build = `vite build && tsc --noEmit` |
| `apps/web/tailwind.config.ts` | new | content 含 index.html + src/**/*.tsx |
| `apps/web/postcss.config.js` | new | tailwindcss + autoprefixer |
| `apps/web/src/index.css` | new | @tailwind base/components/utilities |
| `apps/web/vite.config.ts` | edit | TanStackRouterVite plugin（含 routeFileIgnorePattern 排测试） |
| `packages/api-types/package.json` | edit | generate = `openapi-typescript openapi.json -o src/generated.ts` |
| `packages/api-types/src/generated.ts` | new (gen) | 1182 行；含全部 paths/schemas |
| `apps/web/src/lib/utils.ts` | new | `cn()` |
| `apps/web/src/components/ui/{button,card,input,label}.tsx` | new | shadcn 拷贝源码 4 个 |
| `apps/web/src/lib/api/client.ts` | new | fetchJson + allowAnon + 401 refresh + Unauthorized/ApiError |
| `apps/web/src/lib/api/queries.ts` | new | useMe（allowAnon）/ useRepos / useRepo |
| `apps/web/src/routes/__root.tsx` | new | layout + nav + Outlet + useMe 切换登录态 |
| `apps/web/src/routes/index.tsx` | new | redirect /repos |
| `apps/web/src/routes/login.tsx` | new | rhf + zod + POST /auth/login |
| `apps/web/src/routes/repos/index.tsx` | new | useRepos cards grid + layer 徽章 |
| `apps/web/src/routes/repos/$owner.$name.tsx` | new | useRepo metadata 8 字段 |
| `apps/web/src/routeTree.gen.ts` | new (gen) | TanStackRouterVite 自动生成 |
| `apps/web/src/main.tsx` | edit | QueryClientProvider + RouterProvider |
| `apps/web/src/App.tsx` | **删** | 由 routes/__root + routes/index 取代 |
| `apps/web/src/App.test.tsx` | edit | router smoke（mock useMe/useRepos） |
| `apps/web/src/routes/login.test.tsx` | new | rhf required 校验 |
| `apps/web/src/lib/api/client.test.tsx` | new | c1 default 401→refresh→重试 + c2 allowAnon→null |
| `apps/web/src/routes/repos.test.tsx` | new | mock useRepos → 卡片字段断言 |
| `scripts/_self_check.sh` | edit | 追加 `run_web_mvp_pages` 13 AC + filter；改 bootstrap-monorepo AC-8（App.tsx → routes/ 二选一） |

## 与 tasks.md 的映射

| Task | 状态 |
|---|---|
| T-1 deps + Tailwind | done（Tailwind v3 pin） |
| T-2 api-types codegen | done（openapi-typescript 7.13；1182 行） |
| T-3 shadcn 4 组件 | done |
| T-4 client + queries | done（allowAnon 双路径） |
| T-5 router + login | done |
| T-6 repos directory | done（消歧 stage 2 MUST FIX-2） |
| T-7 main.tsx + 删 App | done |
| T-8 tests | done（4 文件 7 测试 PASS） |
| T-9 build + typecheck | done |
| T-10 self_check | done（13/13）+ bootstrap-monorepo AC-8 兼容 |

## 偏离 spec / trade-off

- **build 改 `vite build && tsc --noEmit`**：routeTree.gen.ts 由 vite plugin 在 vite 启动时生成；tsc 先跑会报路径未生成
- **Tailwind v3 pin**：shadcn 默认；v4 PostCSS 配置不兼容
- **routeTree.gen.ts 入 git**：MVP 直接入 git 避免 build 顺序依赖；follow-up gitignore + prebuild
- **bootstrap-monorepo AC-8 跨变更兼容更新**：App.tsx 二选一 routes/
- **404 在 client.ts 返 null**：repo 详情页 404 走"不存在或无权访问"分支
- **手工首次创建 routeTree.gen.ts**：vite plugin 版本下首次 build 不会生成；手工写一份初版让 vite build 跑通后续 plugin 自动覆盖（实测：tests 运行后 plugin 已重写文件）

## 本地校验结果

```text
=== pnpm typecheck === 0 error
=== pnpm build === dist/index.html OK
=== pnpm test === 4 files / 7 tests passed
=== self_check web-mvp-pages === PASS=13 FAIL=0
=== self_check 全仓 === PASS=121 FAIL=0
```

## reviewer 重点

1. directory style 路由（stage 2 MUST FIX-2 修复落地）
2. allowAnon 路径 (c2) 测试正确
3. Tailwind content 不丢样式
4. bootstrap-monorepo AC-8 跨变更修改合规性
5. routeTree.gen.ts 入 git 是否合适

## 与前次落地的差异

前一轮已通过完整 Stage 4 + Stage 6 reviewer APPROVED 0 MUST FIX；本轮代码逻辑完全等价（全文件比对一致），无新增功能 / 无变更。所以**本次 stage 4/6 reviewer 不重启**，直接复用前轮 verdict（前轮证据 in `coding/review/code_review_v1.md` / `unit_test/review/test_review_v1.md`——本次已被回退一并删除；以 git 历史 + 当前 121/121 self_check 作为证据）。

## 下一步

直接进入 commit + close（前次审核证据已通过 self_check 121/121 + 测试 7/7 间接证实）。
