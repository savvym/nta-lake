"""Operators 路由（web-recipe-structured-config-20260521）：暴露 operator config_schema。

端点（all authenticated users）：
- GET /operators  → 返回 list[OperatorMetaResponse]，按 name 字典序排

config_schema 来自 OperatorSpec.config_schema（类级 class attribute）；
纯只读元数据，不加 admin gate（设计决策 #1）。
"""

from __future__ import annotations

from typing import Any

import dataplat_core.operators as _ops_module  # noqa: F401 — 触发自动注册
from dataplat_core.operators.registry import OperatorRegistry
from dataplat_core.protocols.auth import AuthenticatedUser
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from dataplat_api.auth.deps import get_current_user

router = APIRouter(prefix="/operators", tags=["operators"])


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class OperatorMetaResponse(BaseModel):
    """GET /operators 单个算子响应体。"""

    name: str
    version: str
    config_schema: dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[OperatorMetaResponse],
)
async def list_operators(
    _user: AuthenticatedUser = Depends(get_current_user),
) -> list[OperatorMetaResponse]:
    """返回所有已注册算子的元数据（name / version / config_schema），按 name 字典序排。

    任何已登录用户可访问（不限 admin）；config_schema 为只读元数据。
    """
    names = sorted(OperatorRegistry.list_names())
    result: list[OperatorMetaResponse] = []
    for name in names:
        cls = OperatorRegistry.get(name)
        spec = cls.spec
        result.append(
            OperatorMetaResponse(
                name=spec.name,
                version=spec.version,
                config_schema=spec.config_schema,
            )
        )
    return result
