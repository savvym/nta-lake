---
change_id: adapter-firecrawl-20260517
version: 1
run_id: local-equivalent-via-self_check
run_url: scripts/_self_check.sh
branch: main
commit_sha: (will-be-filled-at-commit)
triggered_at: 2026-05-18T09:15:00Z
finished_at: 2026-05-18T09:18:00Z
status: SUCCESS
---

# CI Result v1

> **本地等价跑**：MVP 阶段尚未接 GitHub Actions（跟踪在 `ci-pipeline-setup-*` follow-up）。本变更用全仓 `_self_check.sh` + `pytest` + `ruff/mypy` 作为 CI 等价证据。

## 结构化字段

```yaml
total_ac: 199
passed_ac: 199
failed_ac: 0
skipped_ac: 0
adapter_firecrawl_pytest_count: 6
adapter_firecrawl_pytest_passed: 6
adapter_firecrawl_pytest_duration_sec: 3.21
regression_pytest_count: 33  # firecrawl + ingest + llm + processor
regression_pytest_passed: 33
ruff_errors: 0
mypy_errors: 0
mypy_source_files: 87
duration_seconds: ~180
```

> 阶段 8 门禁判定：
> ```
> status == SUCCESS           ✓
> total_ac > 0                ✓ (199 = 14 blocks)
> passed_ac == total_ac       ✓
> ```

## Job 概览

| Job | 状态 | 用时 | 备注 |
|---|---|---|---|
| adapter-firecrawl AC (13) | success | ~10s | PASS=13 / FAIL=0 / SKIP=0 |
| full self_check (14 blocks · 199 AC) | success | ~180s | PASS=199 / FAIL=0 / SKIP=0 |
| pytest test_firecrawl.py | success | 3.21s | 6 PASS / 0 FAIL |
| pytest test_firecrawl + test_ingest + test_llm + test_processor | success | 14.68s | 33 PASS（含 13 ingest 旧测试 + 8 processor + 6 llm 无回归） |
| ruff check apps/api packages/core worker/src | success | <2s | 0 errors（自动 fix 1 处 UP037） |
| mypy apps/api/dataplat_api packages/core/src worker/src | success | ~10s | 0 errors / 87 source files |

## 关键命令

```bash
# 本块 13 AC
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_REDIS_PORT=6379 \
bash scripts/_self_check.sh adapter-firecrawl
# → PASS: 13 / FAIL: 0 / SKIP: 0

# 全仓 199 条
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_REDIS_PORT=6379 \
bash scripts/_self_check.sh
# → PASS: 199 / FAIL: 0 / SKIP: 0

# pytest
cd apps/api && uv run pytest -q tests/test_firecrawl.py
# → 6 passed in 3.21s
```

## 失败详情

无。

## Verdict

PASS。

## 处理动作

PASS → 进入阶段 9 部署验证。
