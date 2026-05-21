"""Metrics 路由（W4-7）：operator 运行统计暴露。

端点（admin only）：
- GET /metrics  → 返回 { operators: list[OperatorMetrics], collected_at: <isoformat> }

进程内 MetricsRegistry 由 run_recipe_v2 埋点填充；此路由只读。
非 admin → 403（与 W3-1..W3-3 / W4-5 admin 路径同模式）。
"""

from __future__ import annotations

import datetime

from dataplat_core.metrics import OperatorMetrics, get_metrics_registry
from dataplat_core.protocols.auth import AuthenticatedUser
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from dataplat_api.auth.deps import require_admin

router = APIRouter(prefix="/metrics", tags=["metrics"])


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class MetricsResponse(BaseModel):
    """GET /metrics 响应体。"""

    operators: list[OperatorMetrics]
    collected_at: str  # ISO 8601 UTC


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=MetricsResponse,
)
async def get_metrics(
    _admin: AuthenticatedUser = Depends(require_admin),
) -> MetricsResponse:
    """返回当前进程内的 operator 运行统计快照（admin only）。

    统计覆盖进程启动以来所有通过 run_recipe_v2 执行的 operator 运行记录；
    进程重启即清零（进程内 MVP；持久化见 follow-up metrics-persist-*）。
    """
    registry = get_metrics_registry()
    operators = registry.snapshot()
    collected_at = datetime.datetime.now(tz=datetime.UTC).isoformat()
    return MetricsResponse(operators=operators, collected_at=collected_at)
