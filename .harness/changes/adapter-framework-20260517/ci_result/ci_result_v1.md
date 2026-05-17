---
change_id: adapter-framework-20260517
version: 1
run_id: local-self_check-2026-05-17T12:10:00Z
run_url: n/a（session 直推 main 等价；本地 self_check 作为 CI 等价 gate）
status: passed
---

# CI Result v1

## 本地等价 CI 结果

```text
=== ruff check ===
All checks passed!

=== mypy ===
Success: no issues found in 57 source files

=== pytest（PG 5433 + MinIO 9100 dataplat-secret）===
apps/api/tests: 64 passed in ~24s
  - 13 新 test_ingest.py（含 m parent 链回归）
  - 18 既有 test_commits.py 回归（commit-api-mvp 无破坏）
  - 14 既有 test_repos.py 回归（repo-api-mvp 无破坏）
  - 11 既有 test_auth.py 回归（auth-scaffold 无破坏）
  - 5 MinIO + 2 ORM + 1 health
packages/core/tests: 33 passed（IngestResult.files 加字段无回归）

=== bash scripts/_self_check.sh adapter-framework ===
PASS=13 FAIL=0 SKIP=0

=== bash scripts/_self_check.sh （全仓）===
PASS=108 FAIL=0 SKIP=0
  - bootstrap-monorepo 17
  - core-domain-model 17
  - cas-storage 17
  - auth-scaffold 17
  - repo-api-mvp 13
  - commit-api-mvp 13
  - adapter-framework 13
  - 自递归 1

=== make codegen ===
openapi.json 同步：/repos 命名空间 9 paths（3 repo CRUD + 5 commit-api + 1 ingest）
```

## CI 等价门禁判定

| 等价 CI job | 结果 |
|---|---|
| python-lint-type | PASS |
| python-test | PASS（64 + 33 = 97 passed） |
| codegen-check | PASS |
| adapter-framework self_check | PASS（13/13） |
| 全仓 self_check | PASS（108/108） |

## 已知限制

- 未跑 GitHub Actions；session 直推 main，CI 验证靠本地 self_check 等价

## 下一步

stage 9（skipped 无部署面）→ stage 10 close。
