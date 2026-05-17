---
change_id: web-mvp-pages-20260517
version: 1
run_id: local-self_check-2026-05-17T13:40:00Z
run_url: n/a（session 直推 main 等价模式）
status: passed
---

# CI Result v1

```text
ruff/mypy/pytest（既有）→ 不退化
pnpm typecheck → 0 error
pnpm build → dist/index.html
pnpm test → 4 files / 7 tests passed
self_check web-mvp-pages → PASS=13 FAIL=0
self_check 全仓 → PASS=121 FAIL=0（9 个 block）
make codegen → openapi.json 同步（无新 backend 改动）
```

## 全仓 self_check 9 block 分布

- bootstrap-monorepo 17（AC-8 已兼容更新 App.tsx → routes/）
- core-domain-model 17
- cas-storage 17
- auth-scaffold 17
- repo-api-mvp 13
- commit-api-mvp 13
- adapter-framework 13
- web-mvp-pages 13
- 自递归 1

= 121 total
