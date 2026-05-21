---
change_id: integration-test-framework-20260520
phase: design
status: approved
authored_at: 2026-05-21T11:55:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：integration test framework (W4-6，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

加一条 `bash scripts/integration_test.sh` 端到端命令：起 docker-compose（PG/MinIO/Redis）→ alembic upgrade → 设 env → 跑全量 env-gated pytest → 退码 0 即整链路通。

## 背景

当前 apps/api 测试体系分两层：
- **unit / pure**：纯 Python，`uv run pytest -q` 直接通；约 51 passed（W4-5 后）
- **env-gated integration**：`pytestmark = pytest.mark.skipif(...)`，缺 `DATAPLAT_DATABASE_URL` / `DATAPLAT_MINIO_ENDPOINT` / `DATAPLAT_REDIS_URL` 就 SKIP；当前 main 上有 ~128 skipped 测试

`docker/docker-compose.dev.yml` 已经提供 PG/MinIO/Redis，但**没有一条命令把"起容器 → 设 env → 跑测试"串起来**。结果是：

1. user / CI 不知道整链路是否真通（W4-1/W4-4 的 `test_snapshot_export.py` 长期 SKIP）
2. 回归 risk 累积：merge 时只看 unit 通过，集成路径 silent broken
3. roadmap 的"W4 checkpoint 用户在 UI 上完整流程"前置需要一条机器化端到端验证

W4-6 落这个 orchestrator script。roadmap 描述还提到 playwright e2e，但 playwright 是独立体量（要装 Chromium / 写 web 端 spec / 起 apps/web devserver / 跨语言 fixture）→ **本 change 不做 playwright**，留 follow-up `integration-playwright-e2e-*`；本 change 聚焦 backend integration（pytest env-gated 真跑）。

价值定位：把 `test_snapshot_export.py` / `test_pipeline_e2e.py` / `test_llm_qa_gen.py` 等 ~10 个 env-gated 测试一键 PASS。

## 范围

In scope：

- `scripts/integration_test.sh`（新，~120 行 bash）：
  - 子命令：`up` / `down` / `run` / `all`（默认 `all` = up → run → down）；`up-keep` = up 不 down（dev 复用）
  - `up`：
    - `docker compose -f docker/docker-compose.dev.yml up -d postgres minio minio-init redis`
    - 轮询 healthcheck（每 2s 一次；max 60s 超时报错退出）
    - 等 minio-init 完成（exit code 0）
    - 跑 `cd apps/api && DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5432/dataplat uv run alembic upgrade head`
  - `run`：
    - 设 env：`DATAPLAT_DATABASE_URL` / `DATAPLAT_MINIO_ENDPOINT=http://localhost:9000` / `DATAPLAT_MINIO_ACCESS_KEY=dataplat` / `DATAPLAT_MINIO_SECRET_KEY=dataplat-dev-secret` / `DATAPLAT_REDIS_URL=redis://localhost:6379/0`
    - 跑 `cd apps/api && uv run pytest -q`；再 `cd packages/core && uv run pytest -q`
    - 输出每段前缀 `[integration]`；非 0 退码时 dump pytest 最后 100 行
  - `down`：
    - `docker compose -f docker/docker-compose.dev.yml down -v`（v 清 volume；隔离测试间状态）
  - 顶部 `set -euo pipefail` + `usage()` 函数 + `case` 分发；无参数 / `--help` 打印 usage
  - 退码语义：usage 错 64；up 失败 2；run 失败 1；down 失败 3
- `scripts/lib/integration_helpers.sh`（新，~40 行）：
  - `wait_for_healthy(service_name, timeout_s)`：循环 `docker compose ... ps --format json` jq query `.Health == "healthy"`（fallback：service running 即可）
  - 共享 env / log 函数
- `apps/api/tests/test_integration_smoke.py`（新，~30 行）：
  - 1 个 env-gated behavioral test：`skipif(not DATAPLAT_DATABASE_URL)`；httpx ASGI client → GET `/health` → 200 + body 含 `status: ok`
  - 目的：**保证 integration_test.sh 真执行了一条 env-gated 测试**（防止 script up 之后 pytest 命令空跑或路径错）
- `scripts/integration_test.sh` 最后一步打印 `INTEGRATION_OK` 或 `INTEGRATION_FAIL <exit_code>` sentinel（grep 友好）
- 顶部 inline 注释列 usage + 退码（避免单独写 README）

Out of scope：

- **不**做 playwright UI e2e：体量大、跨语言、devserver 启动依赖；留 follow-up `integration-playwright-e2e-*`
- **不**做 sample.pdf / sample.docx / sample.pptx binary fixture commit：现有 unit/integration tests 都自带 inline fixture（test_pdf_mineru 用 `b"%PDF-1.4"` 桩；test_loader_docx 用 `_build_sample_docx()` 内存构造）；引入 binary 污染 git 历史；留 follow-up `integration-binary-fixtures-*`
- **不**做 CI workflow（.github/workflows/integration.yml）：当前 repo 无 CI；CI 引入是独立改动；留 follow-up `ci-bootstrap-*`
- **不**做 apps/web devserver 启动
- **不**做 docker-compose.integration.yml 分离（dev 与 integration 共用 yml + 脚本选择性 service）
- **不**做 alembic downgrade / restore 测试（W4-10 范围）
- **不**做 pytest 自定义 `-m integration` marker（现有 skipif env 模式够；多一层增 mental load）
- **不**做 manifest.yaml / dataset-card.yaml（D-1）
- **不**改 packages/core / W1..W4-5 任何 merged 产物

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | scripts/integration_test.sh 可执行 + 含 4 子命令函数 | `test -x scripts/integration_test.sh && grep -qE '^cmd_up\(\)' scripts/integration_test.sh && grep -qE '^cmd_run\(\)' scripts/integration_test.sh && grep -qE '^cmd_down\(\)' scripts/integration_test.sh && grep -qE '^cmd_all\(\)' scripts/integration_test.sh` | 0 退出码 |
| AC-2 | static | usage 含 4 个子命令 | `bash scripts/integration_test.sh --help 2>&1 \| grep -qE 'up.*down.*run.*all\|all.*up.*down'` | 命中 |
| AC-3 | behavioral | apps/api 集成 smoke：env 就位时 GET /health → 200 | `cd apps/api && uv run pytest tests/test_integration_smoke.py -x -q` | 1 passed (env 就位) / skipped (env 缺) |
| AC-4 | behavioral | bash 语法 lint | `bash -n scripts/integration_test.sh && bash -n scripts/lib/integration_helpers.sh` | 0 退出码 |

> 注：AC-3 在 docker 缺位的环境 SKIP；reviewer / user 跑 `bash scripts/integration_test.sh all` 走完整链路看 INTEGRATION_OK sentinel。验证报告中需明示哪种状态。

## 决策

1. **scope 缩到 backend integration only**：不做 playwright；roadmap 文字提到但代价过高。整链路 PASS = "测试矩阵从 ~128 skipped 全转 PASS"。
2. **复用 dev compose 不分离 integration compose**：services 完全相同；mailpit 启动 ~1s 可接受；省一份 yml 维护成本。
3. **不引入新 binary fixture 文件**：tests 现有 inline fixture 已覆盖；新 fixture 进 git 增 repo 体积。
4. **smoke test 落 apps/api/tests/**：复用现有 conftest + pytest 配置；不开新顶层 `tests/integration/` 目录避免 pytest discovery 跨目录 + pyproject.toml 改动。
5. **healthcheck 轮询 max 60s**：PG / MinIO 在 dev 机器约 2-5s 起；Redis 1-2s；60s 给 cold pull 镜像留余量。
6. **sentinel `INTEGRATION_OK` / `INTEGRATION_FAIL <exit_code>`**：scripts 友好；CI / user 可 grep 一行知结果，不必 parse pytest 完整输出。
7. **`down -v` 默认 clean volume**：保证 idempotent 跨 run；user 不想清可改用 `up-keep` 子命令保留 PG data。
8. **alembic upgrade 进 up 子命令而非 run**：DDL 是 "环境一次性准备"，与 service 起类同；`run` 只跑测试不动 schema。
9. **退码语义**：usage 错 64（sysexits.h EX_USAGE）；up 失败 2；run 失败 1；down 失败 3。
10. **不接 GitHub Actions / GitLab CI**：当前 repo 无 CI；CI 引入要选 hosted runner / matrix / cache 策略，独立改动量。本 change 只确保 script 在本机可跑。
11. **smoke test 内容选 GET /health 而非更复杂 e2e**：smoke 只验证"集成测试机制本身工作"，不验证业务正确性（业务由各专用集成测试覆盖）。
12. **`cmd_*` 函数命名前缀**：避免与 bash builtin（up / down）冲突 + 便于 AC-1 grep。

## 风险

| 风险 | 缓解 |
|---|---|
| docker compose v1 vs v2 syntax 差异（`docker-compose` vs `docker compose`） | 主脚本统一 `docker compose`（v2 plugin form）；v1 user 会得到清晰错误 |
| healthcheck 在 macOS / Linux Docker Desktop 时序不同 | 轮询 max 60s 留余量；超时报错附 `docker compose ps` 输出帮 user 定位 |
| 网络端口 5432 / 9000 / 6379 占用 | up 前先 `docker compose down --remove-orphans`；端口冲突时 docker 自身报错 + 提示 user 释放 |
| user 已有正在运行的 dev compose | up 是 idempotent；不影响 |
| alembic upgrade 在已存在 schema 上 noop | 是 idempotent 行为；多次运行无负作用 |
| sentinel 字符串和 pytest 输出冲突 | sentinel 单独一行；用 `\bINTEGRATION_OK\b` 不会被 pytest "OK" 子串误命中 |
| smoke test 集合不属于既有矩阵 | 加 1 个 PASS（env 就位）/ SKIP（env 缺）；与 main 同模式 |
| `docker/docker-compose.dev.yml` 服务名变更 | 脚本 service name hard-coded；如 yml 改名需同步；增加风险提示 |
| jq 在某些 minimal docker 环境不可用 | wait_for_healthy fallback 检查 `Up (healthy)` 子串（grep + docker ps 文本），不强依赖 jq |
| AC-4 lint 不能catch 运行时错误 | bash -n 仅语法；运行时由 AC-3 + 用户跑 `all` 子命令验 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `docker/docker-compose.dev.yml`（service 名 + 端口；脚本依赖；不动 yml）
  - `apps/api/alembic.ini` / `apps/api/alembic/env.py`（upgrade head 走现有配置）
  - `apps/api/tests/conftest.py`（smoke test 继承 jwt secret env）
  - `apps/api/dataplat_api/main.py`（GET /health 路由）
- 应当不动：
  - `packages/core/*`（本 change 是 apps/api 集成层 + 脚本）
  - W1..W4-5 已 merge 产物
  - `apps/api/alembic/versions/*`（无新 migration）
- 引用的其他 change：W4-1..W4-5（env-gated 测试都受益）；W3-1..W3-7（loader / adapter 集成测试也受益）

## 关联 follow-up

- `integration-playwright-e2e-*`：apps/web devserver + playwright 跑 UI 流程（pdf 上传 → silver row preview → chain builder → export）
- `integration-binary-fixtures-*`：sample.pdf / sample.docx 等 git LFS 管理
- `ci-bootstrap-*`：GitHub Actions / GitLab CI workflow 接 integration_test.sh
- `integration-pytest-marker-*`：引入 `@pytest.mark.integration` marker + `-m integration` selector
- `integration-parallel-shard-*`：测试 sharding（pytest-xdist + 多 PG/MinIO instance）
- `integration-test-fast-mode-*`：跳过 down，复用容器跑 K 次（dev 提速）
