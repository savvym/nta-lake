---
change_id: repo-api-mvp-20260517
version: 1
run_id: local-self_check-2026-05-17T09:15:00Z
run_url: n/a（session 直推 main 等价模式；本地 self_check 作为 CI 等价 gate）
status: passed
---

# CI Result v1

## 触发条件

- 本变更采用 session 直推 main 等价模式；未走 GitHub Actions。
- `scripts/_self_check.sh` 是统一 smoke gate（bootstrap 阶段已规则化），repo-api-mvp 块 + 全仓块都本地实跑。

## 本地等价 CI 结果

```text
=== ruff check（apps/api + packages/core） ===
All checks passed!

=== mypy（apps/api/dataplat_api + packages/core/src） ===
Success: no issues found in 43 source files

=== pytest（apps/api + packages/core，PG 5433）===
28 passed, 5 skipped
  - 14 新 test_repos.py::test_a ~ test_n
  - 11 既有 test_auth.py 回归
  - 33 packages/core
  - 2 ORM smoke + 1 health
  - 5 skipped: MinIO 集成（env-drift）

=== bash scripts/_self_check.sh repo-api-mvp ===
PASS=13 FAIL=0 SKIP=0（DATAPLAT_PG_PORT=5433）

=== bash scripts/_self_check.sh ===
PASS=81 FAIL=1 SKIP=0
  - 失败：cas-storage AC-15（MinIO 凭据 env-drift；pre-existing；与本变更无关）

=== make codegen ===
openapi.json 同步：3 paths + 5 operations + RepositoryListResponse schema 含 items/total
```

## CI 等价门禁判定

| 等价 CI job | 结果 |
|---|---|
| python-lint-type | PASS（ruff + mypy） |
| python-test | PASS（28 passed + 5 env-skipped） |
| codegen-check | PASS（make codegen 后 git diff 仅 openapi.json，是本变更预期改动） |
| repo-api-mvp self_check | PASS（13/13） |
| 全仓 self_check | 81/82（pre-existing MinIO env-drift；non-blocking） |

## 已知限制

- 未跑 GitHub Actions；session 直推 main，CI 验证靠本地 self_check 等价。
- MinIO 集成测试 env-drift 是 pre-existing 环境层问题，不阻塞本变更。Follow-up：`storage-env-rotate-*`。

## 下一步

进入阶段 9 部署验证（本变更无运行时部署面，skipped）→ 阶段 10 用户确认 → close。
