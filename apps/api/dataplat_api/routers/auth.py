"""认证路由：/auth/login / /auth/logout / /auth/refresh / /auth/me。

Prefix 钉死（spec MUST FIX-1）：`router = APIRouter(prefix="/auth")`；
main.py 用 `app.include_router(router)` 不再传 prefix。
"""

from __future__ import annotations

import uuid

from dataplat_core.protocols.auth import AuthenticatedUser
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select

from dataplat_api.auth.cookies import (
    REFRESH_COOKIE_NAME,
    clear_auth_cookies,
    set_access_cookie,
    set_auth_cookies,
)
from dataplat_api.auth.deps import get_current_user
from dataplat_api.auth.local_provider import LocalAuthProvider
from dataplat_api.auth.tokens import (
    TokenError,
    decode_token,
    encode_access_token,
    encode_refresh_token,
)
from dataplat_api.db import AsyncSessionLocal
from dataplat_api.models import UserORM

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


def _get_provider() -> LocalAuthProvider:
    return LocalAuthProvider(AsyncSessionLocal)


@router.post("/login", response_model=AuthenticatedUser)
async def login(payload: LoginRequest, response: Response) -> AuthenticatedUser:
    provider = _get_provider()
    user = await provider.authenticate(payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    access = encode_access_token(user.user_id, user.role)
    refresh = encode_refresh_token(user.user_id)
    set_auth_cookies(response, access, refresh)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> Response:
    clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh(request: Request, response: Response) -> Response:
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺 refresh token",
        )
    try:
        payload = decode_token(refresh_token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh token 非法或过期",
        ) from exc
    if payload.get("typ") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 类型错",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token 缺 sub",
        )
    # refresh token 不含 role（避免长 TTL token 泄露权限信息）；
    # 这里查实时 users 表读 role + is_active
    # （stage 4 review MUST FIX #2：避免 admin 静默降权 + 防停用用户继续 refresh）
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token sub 非法",
        ) from exc

    async with AsyncSessionLocal() as session:
        stmt = select(UserORM).where(UserORM.id == user_uuid)
        user = (await session.execute(stmt)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已停用",
        )

    new_access = encode_access_token(user_id, user.role)
    set_access_cookie(response, new_access)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=AuthenticatedUser)
async def me(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    return current_user
