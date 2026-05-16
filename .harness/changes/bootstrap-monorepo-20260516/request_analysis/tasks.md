---
change_id: bootstrap-monorepo-20260516
version: 1
authored_at: 2026-05-16T22:10:00Z
---

# Tasks

## 任务清单

```yaml
tasks:
  - id: T-1
    title: 顶层 pyproject.toml + uv workspace 配置
    description: 声明 [project] 占位 / [tool.uv.workspace] members 含 apps/api、packages/core、packages/sdk-py、worker；ruff / mypy / pytest 配置可放 [tool.ruff] / [tool.mypy] / [tool.pytest.ini_options]
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending

  - id: T-2
    title: 顶层 package.json + pnpm-workspace.yaml + turbo.json
    description: pnpm-workspace.yaml 含 apps/web 与 packages/api-types；package.json 含 turbo devDep + 必要脚本；turbo.json 声明 lint/typecheck/test/build 四 pipeline
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-2, AC-3]
    status: pending

  - id: T-3
    title: 顶层 Makefile（核心 target 全量）
    description: up / down / api / web / worker / migrate / seed / codegen / test / lint / typecheck，每个 target 给出实际命令；codegen 链路含 scripts/export_openapi.py + pnpm api-types generate
    depends_on: [T-1, T-2]
    estimated_stage: coding
    covers_ac: [AC-4]
    status: pending

  - id: T-4
    title: 顶层 README.md
    description: 项目一句话简介 + 设计文档链接（.harness/design.md）+ quickstart（uv / pnpm / make up / make api / make web）+ 目录结构示意
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-5]
    status: pending

  - id: T-5
    title: 顶层 .gitignore
    description: 排除 .venv / node_modules / dist / __pycache__ / *.pyc / .pytest_cache / .ruff_cache / .mypy_cache / .turbo / .claude/settings.local.json / *.egg-info / .coverage 等；逐行注释分组
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-6]
    status: pending

  - id: T-6
    title: apps/api FastAPI hello world
    description: pyproject.toml（含 fastapi / uvicorn / pydantic v2 / httpx / pytest / pytest-asyncio）；dataplat_api/main.py 创建 FastAPI app + /healthz 路由；dataplat_api/__init__.py 占位
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-7]
    status: pending

  - id: T-7
    title: apps/api 测试骨架
    description: tests/__init__.py + tests/test_health.py 用 httpx.AsyncClient 测 /healthz 返回 200 + {"status":"ok"}；用 pytest.mark.asyncio
    depends_on: [T-6]
    estimated_stage: unit_test
    covers_ac: [AC-7, AC-16]
    status: pending

  - id: T-8
    title: apps/web Vite + React 最小工程
    description: package.json（vite / react / react-dom / typescript / vitest / @vitejs/plugin-react）；vite.config.ts + tsconfig.json + tsconfig.node.json + index.html + src/main.tsx + src/App.tsx
    depends_on: [T-2]
    estimated_stage: coding
    covers_ac: [AC-8, AC-17]
    status: pending

  - id: T-9
    title: packages/core 占位 Python 包
    description: pyproject.toml（包名 dataplat_core，src layout）+ src/dataplat_core/__init__.py（空，留 __version__）
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-9]
    status: pending

  - id: T-10
    title: packages/sdk-py 占位 Python 包
    description: pyproject.toml + src/dataplat_sdk/__init__.py
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-9]
    status: pending

  - id: T-11
    title: worker/ 占位 Python 包
    description: pyproject.toml + src/dataplat_worker/__init__.py + dataplat_worker/__main__.py（空 main()，留待变更 ?? 实现 RQ consumer）
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-9]
    status: pending

  - id: T-12
    title: packages/api-types 占位 TS 包
    description: package.json + src/generated.ts（export const PLACEHOLDER = true）
    depends_on: [T-2]
    estimated_stage: coding
    covers_ac: [AC-10]
    status: pending

  - id: T-13
    title: plugins / recipes / docs 占位 README
    description: 每个 README ≥ 10 行，描述本目录用途、何时新增内容；recipes/examples/ 子目录可空
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-11]
    status: pending

  - id: T-14
    title: docker/docker-compose.dev.yml
    description: postgres:16 (5432, volume) + minio (9000+9001 console) + minio-init (建 bucket) + redis:7 (6379) + 可选 mailpit；每 service 含 image / ports / volumes / restart policy / healthcheck
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-12]
    status: pending

  - id: T-15
    title: docker/images/{api,worker,web}.Dockerfile 骨架
    description: api/worker FROM python:3.11-slim 用 uv 装；web 用 node:20-slim build + nginx:alpine serve；每个仅声明 FROM / WORKDIR / 入口，本变更不要求 build 通过
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-13]
    status: pending

  - id: T-16
    title: scripts/export_openapi.py + scripts/__init__.py
    description: 占位实现：import apps.api.dataplat_api.main 的 app；json.dump(app.openapi(), file)；目标路径 packages/api-types/openapi.json；可 `python -m scripts.export_openapi` 调用。**scripts/__init__.py 同步建立**，否则 `python -m scripts.export_openapi` 会报 No module named scripts（stage 2 review tasks SHOULD FIX #1 调整）
    depends_on: [T-6, T-12]
    estimated_stage: coding
    covers_ac: [AC-14]
    status: pending

  - id: T-17
    title: .github/workflows/ci.yml
    description: 触发 PR + main push；jobs：python-lint-type（ruff+mypy）/ python-test（pytest --junitxml）/ web-lint-type（pnpm lint + tsc）/ web-test（pnpm vitest）/ codegen-check（make codegen + git diff --exit-code）；concurrency cancel-in-progress
    depends_on: [T-3, T-6, T-8, T-16]
    estimated_stage: coding
    covers_ac: [AC-15]
    status: pending

  - id: T-18
    title: apps/web 最小测试 / build smoke
    description: src/App.test.tsx 用 vitest + @testing-library/react 渲染 App 断言文本 "dataplat" 出现；或仅依赖 `pnpm --filter web build` 作为 smoke（择一）
    depends_on: [T-8]
    estimated_stage: unit_test
    covers_ac: [AC-17]
    status: pending
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: pending

  - id: P-code-review
    estimated_stage: coding_review
    status: pending

  - id: P-test-review
    estimated_stage: unit_test_review
    status: pending

  - id: P-push
    estimated_stage: push
    status: pending
    reason: 本变更内本地 commit；远端 push 留给 follow-up harness-remote-push-*

  - id: P-ci
    estimated_stage: ci_result
    status: pending
    reason: 无远端，CI 实际触发不强制；本地等价校验通过即可

  - id: P-deploy
    estimated_stage: deployment
    status: skipped
    reason: 纯骨架，无部署面

  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
    reason: 用户会话级授权由 Generator 自我确认
```

## DAG 健全性

依赖：

- T-3 → T-1, T-2（Makefile 引用 uv / pnpm）
- T-7 → T-6（测试依赖 API hello world）
- T-9/T-10/T-11 → T-1（共享 uv workspace 配置）
- T-12 → T-2（共享 pnpm workspace）
- T-16 → T-6, T-12（openapi 导出需要 FastAPI app 与 ts 包目标）
- T-17 → T-3, T-6, T-8, T-16（CI 命令引用 Makefile / api / web / codegen）
- T-18 → T-8（测试依赖 React 工程）

无循环。

## 验收覆盖矩阵

| AC | 关联任务 |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3 | T-2 |
| AC-4 | T-3 |
| AC-5 | T-4 |
| AC-6 | T-5 |
| AC-7 | T-6, T-7 |
| AC-8 | T-8 |
| AC-9 | T-9, T-10, T-11 |
| AC-10 | T-12 |
| AC-11 | T-13 |
| AC-12 | T-14 |
| AC-13 | T-15 |
| AC-14 | T-16 |
| AC-15 | T-17 |
| AC-16 | T-7 |
| AC-17 | T-18 |

每条 AC 至少一个 T-* 关联。
