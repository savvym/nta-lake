---
change_id: bootstrap-monorepo-20260516
version: 1
authored_at: 2026-05-16T22:05:00Z
status: draft
---

# Spec：dataplat monorepo 骨架与构建系统

## 背景

`harness-bootstrap-20260516` 关闭后，仓库内只有 `.harness/` + `wiki/` + 顶层 `CLAUDE.md`，**没有任何 dataplat 代码**。`.harness/design.md` §11.3-§11.5 已经详细描述了 monorepo 结构、构建系统（uv + pnpm + turbo）、本地开发环境（docker-compose）、CI 拓扑。

本变更是所有后续 dataplat 业务变更的前置条件：没有目录骨架 + 构建系统 + 中间件 docker-compose，任何业务变更（领域模型 / CAS / Auth / API）都没有可工作的工程环境去落地。

## 问题陈述

当前仓库缺：

1. 没有 Python workspace（uv）和 JS workspace（pnpm）的根配置，无法 `uv sync` / `pnpm install`。
2. 没有 `apps/api/`、`apps/web/`、`packages/*/`、`worker/`、`plugins/`、`recipes/`、`docker/`、`scripts/`、`docs/` 任何目录。
3. 没有 `Makefile`，文章里给的 `make up / api / web / worker / codegen / migrate / seed / test` 任一命令都跑不了。
4. 没有 `docker-compose.dev.yml`，本地 Postgres / MinIO / Redis 起不来。
5. 没有 `.gitignore`，`harness-bootstrap-20260516` stage 4 SHOULD FIX #1（`.claude/settings.local.json` 入库风险）依赖用户全局 ignore 兜底，**不可移植**。
6. 没有 CI workflow，将来推到远端后 PR 缺机械化门禁。

需要一次性把骨架补齐，且保证 hello world 级别可运行（`make up && make api && make web` 起来后浏览器能打开页面、curl `/healthz` 返回 200），让团队从 day 1 就有可工作的工程基线。

## 范围

> **流程说明**：本变更属于常规变更（非追溯式），spec → review → coding → ... 按十阶段顺序推进。stage 9 部署验证因无部署面 skipped；stage 10 用户确认按用户会话级授权由 Generator 自我确认。

In scope（每条都对应可机械化验证）：

- **AC-1**：顶层 `pyproject.toml` 存在，声明 uv workspace 成员含 `apps/api`、`packages/core`、`packages/sdk-py`、`worker`，`uv sync --no-install-project` 命令解析成功（不要求实际安装所有依赖）。
- **AC-2**：顶层 `package.json` + `pnpm-workspace.yaml` 存在；workspace 成员含 `apps/web`、`packages/api-types`；JSON / YAML 均可被 `python -c 'json.load' / yaml.safe_load` 解析。
- **AC-3**：顶层 `turbo.json` 存在且合法（JSON），声明至少 `lint` / `typecheck` / `test` / `build` 四个 pipeline。
- **AC-4**：顶层 `Makefile` 存在，含 `make up / down / api / web / worker / migrate / seed / codegen / test / lint / typecheck` 全部 target；`make -n <target>` 干跑显示对应命令不报错。
- **AC-5**：顶层 `README.md` 存在（≥ 30 行），含项目一句话简介、quickstart（uv + pnpm + make up）、目录结构示意。
- **AC-6**：顶层 `.gitignore` 存在，至少排除 `.venv` / `node_modules` / `dist` / `__pycache__` / `*.pyc` / `.pytest_cache` / `.ruff_cache` / `.mypy_cache` / `.turbo` / `.claude/settings.local.json`；用 `git check-ignore` 验证 `.claude/settings.local.json` 命中。
- **AC-7**：`apps/api/` 存在以下文件：`pyproject.toml`（声明 `dataplat_api` 包 + 依赖 fastapi/uvicorn/pydantic v2）、`dataplat_api/__init__.py`、`dataplat_api/main.py`（创建 FastAPI app + `/healthz` 返回 `{"status":"ok"}`）、`tests/__init__.py`、`tests/test_health.py`（用 httpx.AsyncClient 测 `/healthz`）。
- **AC-8**：`apps/web/` 存在以下文件：`package.json`（声明 vite + react + typescript）、`vite.config.ts`、`tsconfig.json`、`tsconfig.node.json`、`index.html`、`src/main.tsx`、`src/App.tsx`（最小空白主页，仅显示一行 "dataplat"）。
- **AC-9**：`packages/core/`、`packages/sdk-py/`、`worker/` 各自存在 `pyproject.toml` + `__init__.py`（包名分别为 `dataplat_core` / `dataplat_sdk` / `dataplat_worker`）；都是空占位但可被 `uv sync` 识别。
- **AC-10**：`packages/api-types/` 存在 `package.json` + `src/generated.ts`（占位 `export const PLACEHOLDER = true;`）。
- **AC-11**：`plugins/README.md` + `recipes/README.md` + `docs/README.md` 各自存在 (≥ 10 行)，描述本目录用途。
- **AC-12**：`docker/docker-compose.dev.yml` 存在且合法 YAML，声明 `postgres:16` / `minio` / `redis:7` 三个 service（mailpit 可选）；每个 service 含 image / ports / 卷挂载或健康检查。
- **AC-13**：`docker/images/api.Dockerfile`、`worker.Dockerfile`、`web.Dockerfile` 三个文件存在（即便是骨架，至少声明 FROM + WORKDIR + 入口）。
- **AC-14**：`scripts/export_openapi.py` 存在（即便是占位，导出当前 FastAPI app 的 OpenAPI JSON 到 `packages/api-types/openapi.json`）；可被 `python -m scripts.export_openapi` 或 `make codegen` 调用。
- **AC-15**：`.github/workflows/ci.yml` 存在且合法 YAML，含 `python-lint-type` / `python-test` / `web-lint-type` / `web-test` / `codegen-check` 五个 job；触发条件为 PR + main push；`concurrency.cancel-in-progress: true` 已配置。
- **AC-16**：在仓库根跑 `uv run uvicorn dataplat_api.main:app --port 8080`（或经 Makefile）能起来，且 `curl http://localhost:8080/healthz` 返回 200 + `{"status":"ok"}`。本 AC 用 stage 5 的集成测试覆盖：`uv run pytest apps/api -q` PASS。
- **AC-17**：`pnpm --filter web build` 能成功生成 `apps/web/dist/`（含 `index.html`）。本 AC 用 stage 5 的 vitest / build check 覆盖。

## 非范围

- **不实现任何 Repository / Commit / Blob / Tree / Ref 业务模型**——变更 2 `core-domain-model-<yyyymmdd>` 做。
- **不实现 CAS BlobStore**——变更 3 `cas-storage-<yyyymmdd>` 做。
- **不实现 users 表 / auth**——变更 4 `auth-scaffold-<yyyymmdd>` 做。
- **不实现任何 CRUD 业务路由**（除 `/healthz`）——变更 5+ 做。
- **不实现任何 plugin 实质内容**（adapter / processor）——后续独立变更做。
- **不实现 LLM Gateway**——独立变更做。
- **不配置远端 git / 不 push**——本变更内仅本地 commit；远端 push 由 follow-up `harness-remote-push-*` 做。
- **不实际触发 CI workflow**（仓库无远端）——写 ci.yml 文件，本地用 `yamllint` / `actionlint` 等价校验即可。
- **不做 Phase 2+ 内容**（容器 plugin、k8s、Schema Registry、ACL、Eval 协议、Dagster）。

## 验收标准

| ID | 描述 | 验证方式 | 期望 |
|---|---|---|---|
| AC-1 | 顶层 pyproject 合法 + workspace 声明 | `python3 -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); assert 'apps/api' in d['tool']['uv']['workspace']['members']"` | exit 0 |
| AC-2 | pnpm-workspace + package.json 合法 | `python3 -c "import yaml; d=yaml.safe_load(open('pnpm-workspace.yaml')); assert 'apps/web' in d['packages']"` + `python3 -c "import json; json.load(open('package.json'))"` | exit 0 |
| AC-3 | turbo.json 合法 + 4 pipeline | `python3 -c "import json; d=json.load(open('turbo.json')); [d['tasks'][k] for k in ['lint','typecheck','test','build']]"`（tasks 也兼容旧 `pipeline` 字段名，按 turbo v2 规范选 `tasks`） | exit 0 |
| AC-4 | Makefile 含必备 target | `for t in up down api web worker migrate seed codegen test lint typecheck; do make -n $t >/dev/null 2>&1 \|\| exit 1; done` | exit 0 |
| AC-5 | README.md ≥ 30 行 + 含 quickstart | `[ "$(wc -l < README.md)" -ge 30 ] && grep -qE "quickstart\|快速开始" README.md` | exit 0 |
| AC-6 | .gitignore 排除关键路径 | `test -f .gitignore && for p in .venv node_modules dist __pycache__ .pytest_cache .ruff_cache .mypy_cache .turbo ".claude/settings.local.json"; do grep -q "$p" .gitignore \|\| exit 1; done && git check-ignore -q .claude/settings.local.json` | exit 0 |
| AC-7 | apps/api 文件齐全 + `/healthz` 存在 | `for f in pyproject.toml dataplat_api/__init__.py dataplat_api/main.py tests/__init__.py tests/test_health.py; do test -f apps/api/$f \|\| exit 1; done && grep -q "healthz" apps/api/dataplat_api/main.py` | exit 0 |
| AC-8 | apps/web 文件齐全 | `for f in package.json vite.config.ts tsconfig.json tsconfig.node.json index.html src/main.tsx src/App.tsx; do test -f apps/web/$f \|\| exit 1; done` | exit 0 |
| AC-9 | packages/core / sdk-py + worker 占位 | `test -f packages/core/pyproject.toml && test -f packages/core/src/dataplat_core/__init__.py && test -f packages/sdk-py/pyproject.toml && test -f packages/sdk-py/src/dataplat_sdk/__init__.py && test -f worker/pyproject.toml && test -f worker/src/dataplat_worker/__init__.py` | exit 0 |
| AC-10 | packages/api-types 占位 | `test -f packages/api-types/package.json && test -f packages/api-types/src/generated.ts` | exit 0 |
| AC-11 | plugins/recipes/docs README ≥ 10 行 | `for f in plugins/README.md recipes/README.md docs/README.md; do test -f $f && [ "$(wc -l < $f)" -ge 10 ] \|\| exit 1; done` | exit 0 |
| AC-12 | docker-compose.dev.yml 合法 + 3 service | `python3 -c "import yaml; d=yaml.safe_load(open('docker/docker-compose.dev.yml')); s=d.get('services',{}); [s[k] for k in ['postgres','minio','redis']]"` | exit 0 |
| AC-13 | 3 个 Dockerfile 存在 | `for f in api.Dockerfile worker.Dockerfile web.Dockerfile; do test -f docker/images/$f \|\| exit 1; done` | exit 0 |
| AC-14 | export_openapi.py 存在且可调用 | `test -f scripts/export_openapi.py && python3 -c "import ast; ast.parse(open('scripts/export_openapi.py').read())"` | exit 0 |
| AC-15 | ci.yml 合法 + 必备 job | `python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/ci.yml')); j=d['jobs']; [j[k] for k in ['python-lint-type','python-test','web-lint-type','web-test','codegen-check']]; assert d['concurrency']['cancel-in-progress'] is True"` | exit 0 |
| AC-16 | apps/api pytest PASS | `cd apps/api && uv run pytest -q tests/test_health.py` 退出码 == 0（pytest 在 0 collected 时退出 5，有 fail 时退出 1；退出 0 隐含 passed == total ≥ 1） | exit 0 |
| AC-17 | apps/web build 成功 | `pnpm --filter web build && test -f apps/web/dist/index.html` | exit 0 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| `uv sync` 第一次拉依赖耗时长或失败（网络/镜像） | 中 | 阻塞 stage 5 测试 | 在 pyproject 里只引入最小依赖（fastapi / uvicorn / pydantic / httpx / pytest / pytest-asyncio）；如确实失败，允许 stage 5 用 `python -m pytest`（系统 Python）替代 `uv run pytest`，但要在 test_report 说明 |
| `pnpm install` 第一次拉依赖耗时长或失败 | 中 | 阻塞 AC-17 | 同上，仅引入最小依赖（vite / react / react-dom / typescript / vitest） |
| Docker 服务未起或不可用 | 低 | docker-compose 健康检查跑不通 | 本变更不要求 `make up` 实际拉起所有服务通过健康检查；只要 yaml 合法 + 文件齐全即可（AC-12 仅校验 yaml 合法 + 必备 service 声明） |
| 镜像构建依赖外网（registry.internal/...）不可达 | 高 | 无法 docker build | Dockerfile 只用公开 base image（python:3.11-slim / node:20-slim / nginx:alpine）；CI 中 `docker-build` job 不在本变更内强制通过 |
| pytest 实际跑不通（如 fastapi 版本不兼容） | 低 | AC-16 FAIL | 实施时锁定 fastapi 兼容版本（≥ 0.110 < 0.130） |
| pnpm + Node 版本不可用 | 低 | AC-17 FAIL | 实施时 `package.json` 声明 `engines.node >= 20`；本地有 Node 即可，无需 CI |
| pnpm / npm registry 被墙（中国网络典型阻塞） | 高 | AC-17 + 任何 pnpm install 命令卡死 | 在 `package.json` 同级建议 `.npmrc` 候选镜像（如 `registry=https://registry.npmmirror.com`）；如真不通则在 test_report §已知问题段明示并 defer 到运维侧；本变更内**只要 vite.config.ts / src/App.tsx 等源文件齐全 + `pnpm-lock.yaml` 不强制存在** 即可视作 AC-8 满足；AC-17 build smoke 容忍跳过（test_report 显式声明） |
| Makefile recipe 误用空格而非 tab | 中 | AC-4 `make -n <target>` FAIL（make 报 *** missing separator） | 实施时确保 Makefile recipe 行**首字符是 tab**；编辑器 `:set list` 或 `cat -A Makefile` 抽查；本变更门禁内含 `make -n` 干跑作为兜底 |

## 受影响模块

- 仓库根：新增 `pyproject.toml` / `package.json` / `pnpm-workspace.yaml` / `turbo.json` / `Makefile` / `README.md` / `.gitignore`
- 新增 `apps/api/`、`apps/web/`、`packages/{core,api-types,sdk-py}/`、`worker/`、`plugins/`、`recipes/`、`docker/`、`scripts/`、`docs/`
- 新增 `.github/workflows/ci.yml`

## 不受影响但易混淆的模块

- `.harness/` 与 `wiki/`：本变更**完全不修改**它们（除了在 `.harness/changes/bootstrap-monorepo-20260516/` 下产出本变更档案）。
- `CLAUDE.md`：不修改。

## 待澄清问题

- [x] 是否本变更内 `git push` 到远端？答：否，无远端，留给 `harness-remote-push-*`（[summary §关键决策](../summary.md)）。
- [x] CI workflow 是否要求实际触发？答：否，本变更内本地 yaml 合法 + lint/test 等价跑通即可。
- [x] 是否允许 docker-compose 实际启动服务？答：不强制——AC-12 仅校验 yaml 合法。
- [x] 用户的 stage 10 确认：用户会话级授权"所有的东西不需要我进行确认"，Generator 代表用户做自我确认。

## 引用

- `.harness/design.md` §11.3 / §11.4 / §11.5 / §11.6 / §11.7
- `harness-bootstrap-20260516/summary.md` §Deferred 表中相关 follow-up 项
- `harness-bootstrap-20260516/coding/review/code_review_v1.md` SHOULD FIX #1（`.claude/settings.local.json` 入库风险）—— 本变更 AC-6 落实
