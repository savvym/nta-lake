"""dataplat API 入口。

当前是 bootstrap-monorepo-20260516 的最小占位实现：只有 /healthz。
业务路由（repos / commits / blobs / lineage / auth / pipelines / llm）由后续变更逐步引入。
"""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="dataplat API",
    version="0.0.0",
    description="LLM 训练数据管理平台后端。",
)


class HealthResponse(BaseModel):
    status: str


@app.get("/healthz", response_model=HealthResponse, tags=["meta"])
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok")
