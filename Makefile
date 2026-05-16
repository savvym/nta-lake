.PHONY: up down api web worker migrate seed codegen test lint typecheck install clean help

SHELL := /bin/bash

help:
	@echo "dataplat 常用命令："
	@echo "  make install     - 一次性装好 uv 与 pnpm 依赖"
	@echo "  make up          - 起本地中间件（postgres / minio / redis）"
	@echo "  make down        - 关掉本地中间件"
	@echo "  make api         - 本地起 FastAPI（端口 8080）"
	@echo "  make web         - 本地起 Vite dev server（端口 5173）"
	@echo "  make worker      - 本地起 job runner"
	@echo "  make migrate     - alembic upgrade head"
	@echo "  make seed        - 灌种子数据"
	@echo "  make codegen     - 从 FastAPI 导出 OpenAPI -> 前端 TS 类型"
	@echo "  make test        - 跑全部测试"
	@echo "  make lint        - ruff + eslint"
	@echo "  make typecheck   - mypy + tsc --noEmit"
	@echo "  make clean       - 清缓存与 dist"

install:
	uv sync
	pnpm install

up:
	docker compose -f docker/docker-compose.dev.yml up -d

down:
	docker compose -f docker/docker-compose.dev.yml down

api:
	cd apps/api && uv run uvicorn dataplat_api.main:app --reload --port 8080

web:
	pnpm --filter web dev

worker:
	cd worker && uv run python -m dataplat_worker

migrate:
	cd apps/api && uv run alembic upgrade head

seed:
	@echo "seed 占位：当前没有种子脚本；后续 auth-scaffold 变更内引入 dataplat_api.seed 模块"

codegen:
	uv run python -m scripts.export_openapi
	pnpm --filter @dataplat/api-types run generate 2>/dev/null || echo "api-types generate 占位：当前 generated.ts 是 placeholder"

test:
	cd apps/api && uv run pytest -q
	pnpm --filter web test

lint:
	uv run ruff check apps/api packages worker || true
	pnpm --filter web lint || true

typecheck:
	uv run mypy apps/api/dataplat_api || true
	pnpm --filter web typecheck || true

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .turbo -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -prune -exec rm -rf {} + 2>/dev/null || true
