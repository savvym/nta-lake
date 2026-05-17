"""admin 路由：仅 admin 角色可访问。

POST /admin/users / PATCH /admin/users/{id} —— 创建 + 改 role / 重置密码 / 停用。
"""

from __future__ import annotations

import uuid
from typing import Literal

from dataplat_core.protocols.auth import AuthenticatedUser
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.auth.deps import require_admin
from dataplat_api.auth.password import hash_password
from dataplat_api.db import get_session
from dataplat_api.models import UserORM

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    username: str
    password: str | None = None       # None 表示 SSO 用户，password_hash 存 NULL
    email: str | None = None
    role: Literal["admin", "user"] = "user"
    external_id: str | None = None


class UpdateUserRequest(BaseModel):
    role: Literal["admin", "user"] | None = None
    new_password: str | None = None
    is_active: bool | None = None


@router.post("/users", response_model=AuthenticatedUser, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AuthenticatedUser:
    user = UserORM(
        id=uuid.uuid4(),
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password) if payload.password else None,
        role=payload.role,
        is_active=True,
        external_id=payload.external_id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return AuthenticatedUser(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


@router.patch("/users/{user_id}", response_model=AuthenticatedUser)
async def update_user(
    user_id: uuid.UUID,
    payload: UpdateUserRequest,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AuthenticatedUser:
    stmt = select(UserORM).where(UserORM.id == user_id)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if payload.role is not None:
        user.role = payload.role
    if payload.new_password is not None:
        user.password_hash = hash_password(payload.new_password)
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await session.commit()
    await session.refresh(user)
    return AuthenticatedUser(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )
