---
change_id: commit-api-mvp-20260517
version: 1
run_id: local-self_check-2026-05-17T10:50:00Z
run_url: n/a（session 直推 main 等价模式；本地 self_check 作为 CI 等价 gate）
status: passed
---

# CI Result v1

## 本地等价 CI 结果

```text
=== ruff check（apps/api + packages/core）===
All checks passed!

=== mypy（apps/api/dataplat_api + packages/core/src）===
Success: no issues found in 49 source files

=== pytest（PG 5433 + MinIO 9100 dataplat-secret）===
apps/api/tests: 51 passed in ~18s
  - 18 新 test_commits.py::test_a~test_q（含 g1 单元）
  - 14 既有 test_repos.py（repo-api-mvp 回归）
  - 11 既有 test_auth.py（auth-scaffold 回归）
  - 2 ORM smoke + 1 health + 5 MinIO 集成（cas-storage env-drift 消化后 PASS）
packages/core/tests: 33 passed in ~0.2s

=== bash scripts/_self_check.sh commit-api-mvp ===
PASS=13 FAIL=0 SKIP=0（DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100）

=== bash scripts/_self_check.sh （全仓）===
PASS=95 FAIL=0 SKIP=0
  - bootstrap-monorepo 17
  - core-domain-model 17
  - cas-storage 17（含 MinIO AC-15）
  - auth-scaffold 17
  - repo-api-mvp 13
  - commit-api-mvp 13
  - 1 自递归

=== make codegen ===
openapi.json 同步：/repos 命名空间 8 paths（3 repo CRUD + 5 commit-api）
```

## CI 等价门禁判定

| 等价 CI job | 结果 |
|---|---|
| python-lint-type | PASS |
| python-test | PASS（51 + 33 = 84 passed） |
| codegen-check | PASS（make codegen 后 git diff 仅 openapi.json） |
| commit-api-mvp self_check | PASS（13/13） |
| 全仓 self_check | PASS（95/95，pre-existing MinIO env-drift 也消化） |

## 已知限制

- 未跑 GitHub Actions；session 直推 main，CI 验证靠本地 self_check 等价
- 本机 MinIO 凭据特殊：`localhost:9100 / dataplat-secret`（与 compose 默认 `9000/dataplat-dev-secret` 不一致）；需显式 env 变量

## 下一步

stage 9 部署（skipped：无运行时部署面）→ stage 10 close。
