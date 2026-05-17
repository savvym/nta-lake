"""get_current_user + get_optional_user FastAPI 依赖。

`_decode_user_from_cookie` 共享解码逻辑——七路径全返 None（无 cookie / token 解码失败 /
typ != 'access' / sub 缺 / sub 非 UUID / user 不存在 / user inactive）。
- `get_current_user`: None → raise 401
- `get_optional_user`: None → 直接返 None（不 raise）

repo-api-mvp-20260517 spec MUST FIX-1 / tasks MUST FIX-1 钉死：两依赖共享底层避免漂移。
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


async def _decode_user_from_cookie(
    request: Request,
    session: AsyncSession,
) -> AuthenticatedUser | None:
    """七路径全返 None；get_current_user / get_optional_user 共享。"""
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        return None

    try:
        payload = decode_token(token)
    except TokenError:
        return None

    # 安全：必须验证 typ == 'access'（防 refresh→access 重用，stage 4 MUST FIX #1）
    if payload.get("typ") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        return None

    stmt = select(UserORM).where(UserORM.id == user_uuid)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return AuthenticatedUser(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AuthenticatedUser:
    """认证必须通过；失败 raise 401。

    硬契约（repo-api-mvp-20260517 tasks MUST FIX-1）：七路径全 raise 401，与 auth-scaffold
    既有 11 个 test_a~test_k 回归断言一致。
    """
    user = await _decode_user_from_cookie(request, session)
    if user is None:
        raise _UNAUTHORIZED
    return user


async def get_optional_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AuthenticatedUser | None:
    """认证可选；无效 / 缺失返 None（**不 raise**），允许匿名路径继续。

    用于 visibility=public 路径（spec AC-5 + AC-6）。
    """
    return await _decode_user_from_cookie(request, session)


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
