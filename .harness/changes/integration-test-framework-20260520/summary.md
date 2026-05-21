---
change_id: integration-test-framework-20260520
title: integration test framework — bash orchestrator (up / run / down / all) + env-gated smoke test
owner: application-owner-agent
started_at: 2026-05-21T11:55:00Z
phase: done
status: done
last_updated: 2026-05-21T13:00:00Z
related_changes: [web-pdf-mineru-ui-v2-20260520, web-chain-builder-ui-20260520, web-snapshot-export-ui-20260520, recipe-job-runner-20260520, cost-budget-system-20260520]
---

# Summary

## 一句话目标

加一条 `bash scripts/integration_test.sh` 端到端命令，把 "起 docker-compose（PG/MinIO/Redis） → alembic upgrade → 设 env → 跑全量 env-gated pytest → 关容器" 串成机器化命令，让 ~129 个 env-gated 测试有可重复跑通的路径。

## 范围摘要

- **In scope**：
  - `scripts/integration_test.sh`：5 子命令（all / up / up-keep / run / down）+ sysexits 退码 + `INTEGRATION_OK` / `INTEGRATION_FAIL <code>` sentinel
  - `scripts/lib/integration_helpers.sh`：log_info / log_error / wait_for_healthy（`(healthy)` 子串 grep，不依赖 jq）/ wait_for_exit（minio-init）
  - `apps/api/tests/test_integration_smoke.py`：env-gated httpx ASGI → `GET /healthz` → 200 + `status=ok`；env 缺时 SKIP
- **Out of scope**：playwright UI e2e / binary fixtures / CI workflow / docker-compose.integration.yml 分离 / pytest `-m integration` marker / alembic downgrade-restore

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus | approved | APPROVED（self-attest，v3 mini-design） | `ccdc67f` | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | `c3e91b0` (feat) + `e83a4ef` (docs backfill) | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | approved | APPROVED | `297f088` | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 | scope 收缩到 backend integration only，不做 playwright | playwright 体量大（Chromium 装 / web spec / devserver 启动），独立改动 | design § 决策 1 |
| 2026-05-21 | 不引入新 binary fixture，沿用 inline | 现有 tests 都自带 `b"%PDF-1.4"` / `_build_sample_docx()` 内存构造；新 fixture 增 repo 体积 | design § 决策 3 |
| 2026-05-21 | smoke test 进 `apps/api/tests/`，不开顶层 `tests/integration/` | 复用 conftest + pytest 配置，避免改 pyproject.toml | design § 决策 4 |
| 2026-05-21 | helpers 用 `(healthy)` 子串 grep 而非 jq | 兼容 minimal 环境 | design § 风险表 |
| 2026-05-21 | `down -v` 默认清 volume；`up-keep` 提供 dev 复用 | idempotent 跨 run | design § 决策 7 |

## 当前阻塞

无。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up | apps/web devserver + playwright 跑 UI 流程（pdf 上传 → silver preview → chain → export） | `integration-playwright-e2e-*` |
| follow-up | sample.pdf / sample.docx / sample.pptx git LFS 管理 | `integration-binary-fixtures-*` |
| follow-up | GitHub Actions / GitLab CI workflow 接 integration_test.sh；考虑 `--full-trace` 切换 | `ci-bootstrap-*` |
| follow-up | 引入 `@pytest.mark.integration` marker + `-m integration` selector | `integration-pytest-marker-*` |
| follow-up | 测试 sharding（pytest-xdist + 多 PG/MinIO instance） | `integration-parallel-shard-*` |
| follow-up | 跳过 down，复用容器跑 K 次（dev 提速） | `integration-test-fast-mode-*` |

## 交付

- Branch：`change/integration-test-framework-20260520`
- Base：`827155a`（main HEAD at W4-5 docs commit）
- Head：`297f088`（verify_review）；feat `c3e91b0` + docs backfill `e83a4ef`
- Merge commit：`f8068fa`（main，no-ff）
- 用户确认：批量授权（"我只最后验收整个系统，也不用给我过目了"，2026-05-20）
- 关闭时间：2026-05-21T13:00:00Z

## 复盘

- **顺利**：4/4 AC 一次性 PASS；2 个 DEV 偏离都是自洽的（design 笔误纠正 + 实现 quality 提升），无返工。与 W4-1 / W4-4 env-gated SKIP 模式对齐。脚本质量达到 dataplat bash 规范（`set -euo pipefail` / usage / sysexits / sentinel）。范围干净：packages/core + W1..W4-5 merged 产物 0 改动。
- **踩坑**：design 写 `/health` 而 main.py 实际是 `/healthz`；sonnet 在 impl 阶段对照代码纠正。提示 application-owner 写 mini-design 引用既有路由应 `grep` 而非凭记忆。本次 sonnet 主动声明 DEV-1 + 给出充分理由，无需更新 .harness/ rules。
