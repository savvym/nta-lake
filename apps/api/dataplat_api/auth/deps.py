"""get_current_user FastAPI 依赖。

从 cookies['access_token'] 读 token → decode → 查 users 表 → 返 AuthenticatedUser。
缺 / 非法 / 过期 / 用户不存在 / 已停用 → HTTPException 401。
"""

from __future__ import annotations

import uuid

from dataplat_core.protocols.auth import AuthenticatedUser
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.auth.cookies import ACCESS_COOKIE_NAME
from dataplat_api.auth.tokens import TokenError, decode_token
from dataplat_api.db import get_session
from dataplat_api.models import UserORM

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="未认证",
)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AuthenticatedUser:
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        raise _UNAUTHORIZED

    try:
        payload = decode_token(token)
    except TokenError as exc:
        raise _UNAUTHORIZED from exc

    # 安全：必须验证 typ == 'access'，避免 refresh token 被当 access 用
    # （stage 4 review MUST FIX #1）
    if payload.get("typ") != "access":
        raise _UNAUTHORIZED

    user_id = payload.get("sub")
    if not user_id:
        raise _UNAUTHORIZED

    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError) as exc:
        raise _UNAUTHORIZED from exc

    stmt = select(UserORM).where(UserORM.id == user_uuid)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if user is None or not user.is_active:
        raise _UNAUTHORIZED

    return AuthenticatedUser(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


async def require_admin(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """admin 角色守卫；普通用户返 403。"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需 admin 角色",
        )
    return current_user
