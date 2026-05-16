---
change_id: bootstrap-monorepo-20260516
title: 按 design.md §11.3-§11.5 搭 dataplat monorepo 骨架与构建系统
owner: zhhdzhang
started_at: 2026-05-16T22:00:00Z
stage: push
status: in_progress
last_updated: 2026-05-16T23:40:00Z
related_changes:
  - harness-bootstrap-20260516
---

# Summary

## 一句话目标

按 [.harness/design.md](../../design.md) §11.3-§11.5 落地 dataplat 项目的 monorepo 目录骨架、构建系统（uv + pnpm + turbo）、本地开发中间件（docker-compose.dev.yml）、最小可运行的 hello-world apps/api + apps/web、`.gitignore`、Makefile 入口、基础 CI workflow，让后续所有 dataplat 业务变更都有可工作的工程环境。

## 范围摘要

- **In scope**：
  - 顶层 `pyproject.toml`（uv workspace 根）、`package.json` + `pnpm-workspace.yaml`、`turbo.json`、`Makefile`、`README.md`、`.gitignore`
  - `apps/api/`：FastAPI hello world + `/healthz` 路由 + 最小 pyproject + `dataplat_api/main.py` + `tests/`
  - `apps/web/`：Vite + React 最小工程，挂一个空白主页 + `package.json` + `vite.config.ts` + `tsconfig.json`
  - `packages/core/`：空 Python 包占位（pyproject + `dataplat_core/__init__.py`），为变更 2 准备
  - `packages/api-types/`：空 TS 包占位（package.json + 占位 `src/generated.ts`），CI 中验证 codegen 不漂移
  - `packages/sdk-py/`：空 Python 包占位
  - `worker/`：空 Python 包占位（pyproject + `dataplat_worker/__init__.py`），不实现 RQ consumer
  - `plugins/`：占位目录 + README（插件开发指南骨架）
  - `recipes/examples/`：占位 + README
  - `docker/docker-compose.dev.yml`（postgres / minio / redis / mailpit）+ `docker/images/{api,worker,web}.Dockerfile` 骨架
  - `scripts/`：`export_openapi.py` 占位（在 codegen 链路里）
  - `docs/`：占位 README
  - `.github/workflows/ci.yml`：lint + type + test + codegen-check + docker-build 矩阵
- **Out of scope**：
  - 任何 Repository / Commit / Blob 业务模型（留给变更 2 `core-domain-model`）
  - CAS BlobStore 实现（留给变更 3 `cas-storage`）
  - 任何认证 / users 表（留给变更 4 `auth-scaffold`）
  - 任何 CRUD 业务路由（留给变更 5 `repo-api-mvp` 及之后）
  - 任何 plugin 实质实现（adapter / processor 都留给后续）
  - LLM Gateway（留给独立变更）
  - 前端登录页 / 业务页面（留给后续）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done（就地修 AC-9/AC-16 + 风险 +2 + AC-6 缺前导 . + T-16 加 scripts/__init__.py） | v1（就地修订） | — | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | **done** | v1 | **APPROVED**（MUST FIX=0，spec: SHOULD=4→2 修+2 defer；tasks: SHOULD=4→2 修+2 defer；NICE 共 6 不阻塞）| [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) |
| 3 编码实现 | done（38 手写 + 3 生成 = 41 文件；17 AC 全 PASS）| v1 | — | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | done | v1 | **APPROVED**（MUST FIX 0；SHOULD FIX 6 + NICE 4 中：现场修 2 MUST FIX（ghost / ci.yml vitest）+ 部分 SHOULD 已修，其余 defer）| [code_review_v1.md](coding/review/code_review_v1.md) |
| 5 单测编写 | done（pytest 1/1 + vitest 1/1 + 18 静态自检 PASS + 补建 scripts/_self_check.sh 落实 stage 6 SHOULD FIX）| v1 | — | [test_report_v1.md](unit_test/test_report_v1.md) · [scripts/_self_check.sh](../../../../scripts/_self_check.sh) |
| 6 单测评审 | done | v1 | **APPROVED**（MUST FIX 0；SHOULD FIX 1 已就地修 `_self_check.sh` 实建；NICE 3 defer）| [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | in_progress | — | — | 本地 commit；远端 push 留给 follow-up |
| 8 CI 验证 | done（本地等价：`scripts/_self_check.sh` 18/18 PASS + `uv run ruff` All checks passed + `uv run mypy` Success；远端 CI 触发留给 `harness-remote-push-*`）| 等价证据 | — | 见 test_report §本地运行结果 |
| 9 部署验证 | skipped: 仍无部署面 | — | — | — |
| 10 用户确认 | pending（用户在本会话开头显式授权"所有的东西不需要我进行确认"——会话级授权，stage 10 由 Generator 代表用户做自我确认） | — | — | — |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-16 | 本变更只做骨架 + hello world，不实现任何业务模型 | 把"骨架可工作 + 构建系统跑通"作为单一目标；业务模型留给独立变更走完整流程，每个变更范围小、易评审 | 本 summary §范围 |
| 2026-05-16 | 用户会话级授权"所有的东西不需要我进行确认" | 用户在本会话开头连续变更启动时显式声明；本会话内所有变更的 stage 10 由 Generator 代表用户自我确认 | 本会话开头 prompt |
| 2026-05-16 | CI workflow 本变更内写出来但不要求触发通过 | 本地 git 仓库尚无远端，CI 触发需要 follow-up `harness-remote-push-*`；本变更里写好 ci.yml + 本地 lint/type/test 跑通即视为 stage 8 等价交付 | tasks.md P-ci |
| 2026-05-16 | `.gitignore` 在本变更落实（继承 harness-bootstrap-20260516 stage 4 SHOULD FIX #1） | 那个 SHOULD FIX 显式 deferred 到本变更；正好和"构建系统骨架"一同纳入 | tasks.md T-gitignore |

## 当前阻塞

- Stage 1 进行中：写 spec.md / tasks.md。

## Deferred 项

> 评审通过后填。

## 交付

> 关闭本变更时填写。

- Branch：—
- PR：—
- Commits：—
- 部署版本：N/A
- 用户确认：—
- 关闭时间：—

## 复盘

> 关闭后填。
