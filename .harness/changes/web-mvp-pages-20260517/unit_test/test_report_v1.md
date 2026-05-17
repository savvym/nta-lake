---
change_id: web-mvp-pages-20260517
version: 1
authored_at: 2026-05-17T13:35:00Z
status: waiting_review
---

# Test Report v1

## 验收 ↔ 测试映射

| AC | 测试 |
|---|---|
| AC-1 | self_check AC-1（package.json deps） |
| AC-2 | self_check AC-2（generated.ts /repos grep） |
| AC-3 | self_check AC-3（tailwind/postcss/index.css） |
| AC-4 | self_check AC-4（4 shadcn 组件） |
| AC-5 | self_check AC-5 + `client.test.tsx` (c1) 默认 refresh 重试 + (c2) allowAnon → null |
| AC-6 | self_check AC-6（5 routes 文件） |
| AC-7 | self_check AC-7 + `App.test.tsx` 验 dataplat brand + login 链 |
| AC-8 | self_check AC-8 + `login.test.tsx` 表单 render + zod 校验 |
| AC-9 | self_check AC-9 + `repos.test.tsx` mock 2 repo 卡片字段 |
| AC-10 | self_check AC-10 grep metadata 字段 |
| AC-11 | self_check AC-11（pnpm test 4 file 7 test PASS） |
| AC-12 | self_check AC-12（typecheck + build + dist） |
| AC-13 | self_check AC-13 |

## 测试文件清单

| 文件 | 用例数 |
|---|---|
| `App.test.tsx` | 2（root layout + redirect） |
| `routes/login.test.tsx` | 2（render + required 校验） |
| `lib/api/client.test.tsx` | 2（c1 + c2） |
| `routes/repos.test.tsx` | 1（cards 字段） |
| `_self_check.sh` web-mvp-pages | 13 |

**总：7 + 13 = 20 断言**

## Mock 范围

- vi.mock `lib/api/queries` 在路由测试中（mock TanStack Query hooks 返 fixture）
- `vi.fn()` mock global.fetch 在 client.test 中
- 不连后端（后端集成已在 apps/api/tests 充分覆盖）

## 本地运行结果

```text
pnpm test → 4 files / 7 tests passed in 1.49s
pnpm typecheck → 0 error
pnpm build → dist/index.html + dist/assets/* 生成
self_check web-mvp-pages → PASS=13 FAIL=0
self_check 全仓 → PASS=121 FAIL=0
```

## 与前次落地差异

前轮 stage 6 reviewer APPROVED 0 MUST FIX；本轮测试代码等价；不重启 reviewer。
