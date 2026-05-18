---
change_id: sdk-cli-mvp-20260518
version: 1
run_id: local-equivalent-via-self_check
run_url: scripts/_self_check.sh
branch: main
commit_sha: (will-be-filled-at-commit)
triggered_at: 2026-05-18T11:55:00Z
finished_at: 2026-05-18T11:58:00Z
status: SUCCESS
---

# CI Result v1

> 本地等价跑。MVP 尚未接 GitHub Actions（跟踪 `ci-pipeline-setup-*`）。

## 结构化字段

```yaml
total_ac: 225
passed_ac: 225
failed_ac: 0
skipped_ac: 0
sdk_cli_pytest_count: 12
sdk_cli_pytest_passed: 12
sdk_cli_pytest_duration_sec: 0.38
regression_pytest_count: 26  # llm_qa_gen + processor + firecrawl + llm
regression_pytest_passed: 26
ruff_errors: 0
mypy_errors: 0
mypy_source_files: 91  # 88 + 3 sdk-py 新文件
duration_seconds: ~180
```

> 阶段 8 门禁：status SUCCESS / total_ac > 0 / passed == total，全过。

## Job 概览

| Job | 状态 | 用时 | 备注 |
|---|---|---|---|
| sdk-cli-mvp AC (13) | success | ~5s | PASS=13 / FAIL=0 / SKIP=0（**全块不依赖 PG/MinIO/Redis**） |
| full self_check (16 blocks · 225 AC) | success | ~180s | PASS=225 |
| pytest packages/sdk-py/tests | success | 0.38s | 12 PASS |
| pytest 跨变更回归 | success | 12.24s | 26 PASS（无回归） |
| ruff check 全仓 | success | <2s | 0 errors |
| mypy 全仓 | success | ~12s | 0 errors / 91 source files |

## 关键命令

```bash
# 本块 13 AC（**不依赖 PG/MinIO/Redis**）
bash scripts/_self_check.sh sdk-cli-mvp

# 全仓 225 条
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_REDIS_PORT=6379 \
bash scripts/_self_check.sh

# pytest（也无需依赖）
cd packages/sdk-py && uv run pytest -q tests/
```

## Verdict

PASS。
