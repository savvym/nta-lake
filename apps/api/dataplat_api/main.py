"""dataplat API 入口。

当前是 bootstrap-monorepo-20260516 的最小占位实现：只有 /healthz。
业务路由（repos / commits / blobs / lineage / auth / pipelines / llm）由后续变更逐步引入。
"""

from fastapi import FastAPI
from pydantic import BaseModel

# 触发 adapters/__init__.py + processors/__init__.py 自动注册到 registries
from dataplat_api import adapters as _adapters  # noqa: F401
from dataplat_api import processors as _processors  # noqa: F401
from dataplat_api.routers.admin import router as admin_router
from dataplat_api.routers.auth import router as auth_router
from dataplat_api.routers.snapshots import router as snapshots_router
from dataplat_api.routers.ingest import router as ingest_router
from dataplat_api.routers.jobs import router as jobs_router
from dataplat_api.routers.pipelines import router as pipelines_router
from dataplat_api.routers.process import router as process_router
from dataplat_api.routers.repos import router as repos_router

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


# 注：router 已自带 prefix（/auth、/admin），include_router 不再传 prefix
# 见 cas-storage spec MUST FIX-1 与 stage 4 reviewer 钉死的唯一组合
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(repos_router)
app.include_router(snapshots_router)
app.include_router(ingest_router)
app.include_router(jobs_router)
app.include_router(process_router)
app.include_router(pipelines_router)
