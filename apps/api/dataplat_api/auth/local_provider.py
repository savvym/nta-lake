"""LocalAuthProvider：MVP 内置账户体系（password_hash 校验）。

实现 `dataplat_core.protocols.auth.AuthProvider` Protocol。

按 .harness/design.md §11.6：不引入 `fastapi-users`，自己写更可控。
"""

from __future__ import annotations

from dataplat_core.protocols.auth import AuthenticatedUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dataplat_api.auth.password import verify_password
from dataplat_api.models import UserORM


class LocalAuthProvider:
    """从 users 表读 password_hash 校验。"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def authenticate(
        self, username: str, password: str
    ) -> AuthenticatedUser | None:
        async with self._session_factory() as session:
            stmt = select(UserORM).where(UserORM.username == username)
            user = (await session.execute(stmt)).scalar_one_or_none()

        if user is None:
            return None
        if not user.is_active:
            return None
        if user.password_hash is None:
            # SSO 用户无本地密码 → 不能走 local provider 认证
            return None
        if not verify_password(password, user.password_hash):
            return None

        return AuthenticatedUser(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        )
