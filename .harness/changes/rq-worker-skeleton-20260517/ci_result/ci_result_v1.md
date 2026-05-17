---
change_id: rq-worker-skeleton-20260517
version: 1
run_id: local-self_check-2026-05-17T15:00:00Z
run_url: n/a（session 直推 main 等价）
status: passed
---

# CI Result v1

```text
ruff: All checks passed!
mypy: Success: no issues found in 67 source files
pytest apps/api/tests: 74 passed in ~30s
  - 10 新 test_jobs.py
  - 13 既有 test_ingest.py 回归
  - 18 既有 test_commits.py 回归
  - 14 既有 test_repos.py 回归
  - 11 既有 test_auth.py 回归
  - 2 ORM smoke + 1 health + 5 MinIO
self_check rq-worker-skeleton: PASS=13 FAIL=0
self_check 全仓: PASS=134 FAIL=0（10 个 block；auth-scaffold AC-2 兼容 0003 head 更新）
make codegen: openapi.json 同步含 /jobs 2 paths
```

## 10 个 block 分布

- bootstrap-monorepo 17 / core-domain-model 17 / cas-storage 17 / auth-scaffold 17
- repo-api-mvp 13 / commit-api-mvp 13 / adapter-framework 13 / web-mvp-pages 13
- rq-worker-skeleton 13 / 自递归 1
- 总 = 134
