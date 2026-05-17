---
change_id: llm-gateway-mvp-20260517
version: 1
run_id: local-equivalent-via-self_check
run_url: scripts/_self_check.sh
branch: main
commit_sha: (will-be-filled-at-commit)
triggered_at: 2026-05-17T20:50:00Z
finished_at: 2026-05-17T20:53:00Z
status: SUCCESS
---

# CI Result v1

> **本地等价跑**：MVP 阶段尚未接 GitHub Actions（跟踪在 `ci-pipeline-setup-*` follow-up）。本变更用全仓 `_self_check.sh` + `pytest` + `ruff/mypy` 作为 CI 等价证据。

## 结构化字段

```yaml
total_ac: 186
passed_ac: 186
failed_ac: 0
skipped_ac: 0
llm_gateway_pytest_count: 6
llm_gateway_pytest_passed: 6
llm_gateway_pytest_duration_sec: 2.15
combined_pytest_count: 14  # test_llm + test_processor 无回归
ruff_errors: 0
mypy_errors: 0
mypy_source_files: 85
duration_seconds: ~180
```

> 阶段 8 门禁判定：
> ```
> status == SUCCESS           ✓
> total_ac > 0                ✓ (186 = 12 blocks × 13 AC + 旧 17×3 + 13×9)
> passed_ac == total_ac       ✓
> ```

## Job 概览

| Job | 状态 | 用时 | 备注 |
|---|---|---|---|
| llm-gateway-mvp AC (13) | success | 10s | PASS=13 / FAIL=0 / SKIP=0 |
| full self_check (12 blocks · 186 AC) | success | ~180s | PASS=186 / FAIL=0 / SKIP=0 |
| pytest test_llm.py | success | 2.15s | 6 PASS / 0 FAIL |
| pytest test_llm + test_processor | success | 6.64s | 14 PASS（含 8 旧 processor 测试无回归） |
| ruff check apps/api packages/core worker/src | success | <2s | 0 errors（修了 1 处 import 排序后再跑） |
| mypy apps/api/dataplat_api packages/core/src worker/src | success | ~10s | 0 errors / 85 source files |

## 关键命令

```bash
# 本块 13 AC
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_REDIS_PORT=6379 \
bash scripts/_self_check.sh llm-gateway-mvp
# → PASS: 13 / FAIL: 0 / SKIP: 0

# 全仓 186 条
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
DATAPLAT_REDIS_PORT=6379 \
bash scripts/_self_check.sh
# → PASS: 186 / FAIL: 0 / SKIP: 0

# pytest
cd apps/api && uv run pytest -q tests/test_llm.py
# → 6 passed in 2.15s
```

## 失败详情

无。

## Verdict

PASS。

## 处理动作

PASS → 进入阶段 9 部署验证。
