---
change_id: llm-qa-gen-20260518
version: 1
run_id: local-equivalent-via-self_check
run_url: scripts/_self_check.sh
branch: main
commit_sha: (will-be-filled-at-commit)
triggered_at: 2026-05-18T10:30:00Z
finished_at: 2026-05-18T10:33:00Z
status: SUCCESS
---

# CI Result v1

> **本地等价跑**：MVP 阶段尚未接 GitHub Actions（跟踪在 `ci-pipeline-setup-*` follow-up）。本变更用全仓 `_self_check.sh` + `pytest` + `ruff/mypy` 作为 CI 等价证据。

## 结构化字段

```yaml
total_ac: 212
passed_ac: 212
failed_ac: 0
skipped_ac: 0
llm_qa_gen_pytest_count: 6
llm_qa_gen_pytest_passed: 6
llm_qa_gen_pytest_duration_sec: 2.74
regression_pytest_count: 26  # qa-gen + processor + firecrawl + llm
regression_pytest_passed: 26
ruff_errors: 0
mypy_errors: 0
mypy_source_files: 88
duration_seconds: ~180
```

> 阶段 8 门禁判定：
> ```
> status == SUCCESS           ✓
> total_ac > 0                ✓ (212 = 15 blocks)
> passed_ac == total_ac       ✓
> ```

## Job 概览

| Job | 状态 | 用时 | 备注 |
|---|---|---|---|
| llm-qa-gen AC (13) | success | ~10s | PASS=13 / FAIL=0 / SKIP=0 |
| full self_check (15 blocks · 212 AC) | success | ~180s | PASS=212 / FAIL=0 / SKIP=0 |
| pytest test_llm_qa_gen.py | success | 2.74s | 6 PASS / 0 FAIL |
| pytest 跨变更回归 (qa-gen + processor + firecrawl + llm) | success | 11.38s | 26 PASS |
| ruff check apps/api packages/core worker/src | success | <2s | 0 errors |
| mypy apps/api/dataplat_api packages/core/src worker/src | success | ~10s | 0 errors / 88 source files |

## 关键命令

```bash
# 本块 13 AC
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_REDIS_PORT=6379 \
bash scripts/_self_check.sh llm-qa-gen
# → PASS: 13 / FAIL: 0 / SKIP: 0

# 全仓 212 条
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_REDIS_PORT=6379 \
bash scripts/_self_check.sh
# → PASS: 212 / FAIL: 0 / SKIP: 0

# pytest
cd apps/api && uv run pytest -q tests/test_llm_qa_gen.py
# → 6 passed in 2.74s
```

## 失败详情

无。

## Verdict

PASS。

## 处理动作

PASS → 进入阶段 9 部署验证。
