"""dataplat 认证模块。

汇出常用 API；具体定义在各子模块。
"""

from dataplat_api.auth.cookies import (
    ACCESS_COOKIE_NAME,
    REFRESH_COOKIE_NAME,
    clear_auth_cookies,
    set_access_cookie,
    set_auth_cookies,
)
from dataplat_api.auth.deps import get_current_user, require_admin
from dataplat_api.auth.local_provider import LocalAuthProvider
from dataplat_api.auth.password import hash_password, verify_password
from dataplat_api.auth.tokens import (
    ACCESS_TTL_SECONDS,
    REFRESH_TTL_SECONDS,
    TokenError,
    decode_token,
    encode_access_token,
    encode_refresh_token,
)

__all__ = [
    "ACCESS_COOKIE_NAME",
    "REFRESH_COOKIE_NAME",
    "ACCESS_TTL_SECONDS",
    "REFRESH_TTL_SECONDS",
    "TokenError",
    "LocalAuthProvider",
    "clear_auth_cookies",
    "set_access_cookie",
    "set_auth_cookies",
    "decode_token",
    "encode_access_token",
    "encode_refresh_token",
    "hash_password",
    "verify_password",
    "get_current_user",
    "require_admin",
]
