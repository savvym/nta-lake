---
change_id: processor-framework-20260517
version: 1
run_id: local-equivalent-via-self_check
run_url: scripts/_self_check.sh
branch: main
commit_sha: (will-be-filled-at-commit)
triggered_at: 2026-05-17T19:00:00Z
finished_at: 2026-05-17T19:01:00Z
status: SUCCESS
---

# CI Result v1

> **本地等价跑**：MVP 阶段尚未接 GitHub Actions（追踪在 `ci-pipeline-setup-*` follow-up）。本变更用全仓 `_self_check.sh` + `pytest` + `ruff/mypy` 作为 CI 等价证据。

## 结构化字段

```yaml
total_ac: 173
passed_ac: 173
failed_ac: 0
skipped_ac: 0
processor_framework_pytest_count: 8
processor_framework_pytest_passed: 8
processor_framework_pytest_duration_sec: 5.43
ruff_errors: 0
mypy_errors: 0
mypy_source_files: 76
duration_seconds: ~110
coverage_percent: n/a
```

> 阶段 8 门禁判定：
> ```
> status == SUCCESS           ✓
> total_ac > 0                ✓ (173)
> passed_ac == total_ac       ✓
> ```

## Job 概览

| Job | 状态 | 用时 | 备注 |
|---|---|---|---|
| processor-framework AC (13) | success | 8s | PASS=13 / FAIL=0 / SKIP=0 |
| full self_check (12 blocks · 173 AC) | success | ~100s | PASS=173 / FAIL=0 / SKIP=0 |
| pytest test_processor.py | success | 5.43s | 8 PASS / 0 FAIL |
| ruff check apps/api packages/core worker/src | success | <2s | 0 errors（修了 1 处 import 排序后再跑） |
| mypy apps/api/dataplat_api packages/core/src worker/src | success | ~10s | 0 errors / 76 source files |

## 关键命令

```bash
# AC 13 条
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_REDIS_PORT=6379 \
bash scripts/_self_check.sh processor-framework
# → PASS: 13 / FAIL: 0 / SKIP: 0

# 全仓 173 条
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_REDIS_PORT=6379 \
bash scripts/_self_check.sh
# → PASS: 173 / FAIL: 0 / SKIP: 0

# pytest
cd apps/api && uv run pytest -q tests/test_processor.py
# → 8 passed in 5.43s
```

## 失败详情

无。

## Verdict

PASS。

## 处理动作

PASS → 进入阶段 9 部署验证。
