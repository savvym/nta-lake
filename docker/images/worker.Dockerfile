# dataplat worker 镜像（占位骨架）
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
COPY worker ./worker
COPY packages ./packages
COPY plugins ./plugins

RUN uv sync --frozen --no-dev || true

CMD ["uv", "run", "python", "-m", "dataplat_worker"]
