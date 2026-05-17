"""httpOnly + Secure + SameSite=Lax cookies。

按 .harness/design.md §11.6：access/refresh 都走 cookie；前端拿不到、XSS 偷不走。
"""

from __future__ import annotations

import os

from fastapi import Response

from dataplat_api.auth.tokens import ACCESS_TTL_SECONDS, REFRESH_TTL_SECONDS

ACCESS_COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"


def _cookie_secure() -> bool:
    """生产默认 True；dev 用 HTTP 访问时设 env `DATAPLAT_COOKIE_SECURE=false`。"""
    return os.environ.get("DATAPLAT_COOKIE_SECURE", "true").lower() != "false"


def _set(response: Response, name: str, value: str, max_age: int) -> None:
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        path="/",
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
    )


def set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    _set(response, ACCESS_COOKIE_NAME, access, ACCESS_TTL_SECONDS)
    _set(response, REFRESH_COOKIE_NAME, refresh, REFRESH_TTL_SECONDS)


def set_access_cookie(response: Response, access: str) -> None:
    """仅刷新 access cookie（用于 /auth/refresh）。"""
    _set(response, ACCESS_COOKIE_NAME, access, ACCESS_TTL_SECONDS)


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
