---
change_id: integration-test-framework-20260520
phase: implementation
status: done
authored_at: 2026-05-21T12:30:00Z
author: claude-sonnet-4-6
model_used: claude-sonnet-4-6
branch: change/integration-test-framework-20260520
base_commit: ccdc67f
head_commit: c3e91b0
pr_url: n/a
---

# Implementation：integration test framework (W4-6)

## 改动文件清单

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `scripts/integration_test.sh` | new | 主 orchestrator：cmd_up/cmd_down/cmd_run/cmd_all/cmd_up_keep + sysexits 退码 + INTEGRATION_OK sentinel |
| `scripts/lib/integration_helpers.sh` | new | 共享库：log_info/log_error/wait_for_healthy/wait_for_exit（不依赖 jq） |
| `apps/api/tests/test_integration_smoke.py` | new | env-gated smoke：skipif DATAPLAT_DATABASE_URL；httpx ASGI → GET /healthz → 200 + status=ok |
| `.harness/changes/integration-test-framework-20260520/implementation.md` | edit | 本文件 backfill |

## AC 自检 + 证据

| AC | kind | 命令 | 结果 |
|---|---|---|---|
| AC-1 | static | `test -x scripts/integration_test.sh && grep -qE '^cmd_up\(\)' ... (4 greps)` | PASS exit 0 |
| AC-2 | static | `bash scripts/integration_test.sh --help 2>&1 \| grep -E 'up.*down.*run.*all'` | PASS：命中 `子命令（all up down run up-keep）` |
| AC-3 | behavioral | `cd apps/api && uv run pytest tests/test_integration_smoke.py -x -q` | `1 skipped in 1.67s`（env 缺位；预期） |
| AC-4 | behavioral | `bash -n scripts/integration_test.sh && bash -n scripts/lib/integration_helpers.sh` | PASS exit 0 |

## 全量回归

```text
apps/api:      51 passed, 129 skipped in 1.89s   （新增 1 SKIP；零 failure）
packages/core: 97 passed in 1.31s                （本 change 不动 core）
```

## 偏离 design.md

| # | 偏离点 | 原因 |
|---|---|---|
| D-1 | smoke test 用 `/healthz` 而非 `/health` | `main.py` 实际路由是 `/healthz`；design.md 写 `/health` 系笔误；以实现为准，无代码改动 |
| D-2 | usage 改为 heredoc 函数而非纯注释块 grep | 原 `grep '^#'` 会把脚本内所有注释行全打印；改用 heredoc 保持 usage 清晰可读；头部注释块保留作文档 |

## D-1 永不做清单自查

无 manifest.yaml / dataset-card.yaml / row-diff / cherry-pick / rollback / DB schema rename / blob 派生图 / Asset。

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验。
