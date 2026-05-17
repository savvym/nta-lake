"""AuthProvider Protocol + AuthenticatedUser。

按 .harness/design.md §11.6：MVP 用 LocalAuthProvider（password_hash 校验），
预留 OIDCAuthProvider / SAMLAuthProvider 实现同一接口。

业务路由通过 AuthProvider 抽象认证用户，不直接访问 password_hash 字段。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict


class AuthenticatedUser(BaseModel):
    """认证通过后的用户视图（不含密码 hash）。"""

    model_config = ConfigDict(frozen=False, extra="forbid")

    user_id: str
    username: str
    email: str | None = None
    role: str
    is_active: bool


@runtime_checkable
class AuthProvider(Protocol):
    """认证提供者抽象。

    MVP 实现：`apps/api/dataplat_api/auth/local_provider.LocalAuthProvider`。
    后续 SSO：`OIDCAuthProvider` / `SAMLAuthProvider` 实现同一接口。
    """

    async def authenticate(
        self, username: str, password: str
    ) -> AuthenticatedUser | None:
        """验证用户名+密码。

        Returns:
            认证成功返回 AuthenticatedUser；用户不存在 / 密码错 / 已停用 / SSO 用户无
            password_hash 一律返 None（不要 raise，简化路由逻辑）。
        """
        ...
