# dataplat API 镜像（占位骨架，bootstrap-monorepo 不要求 build 通过）
FROM python:3.11-slim

WORKDIR /app

# 引入 uv（与本地开发一致）
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY apps/api ./apps/api
COPY packages ./packages

RUN uv sync --frozen --no-dev || true

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "dataplat_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
