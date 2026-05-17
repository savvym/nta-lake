"""JWT 双 token：access 15min / refresh 7d，HS256。

设计要点（spec MUST FIX-2）：secret 在每次 encode/decode 时 `os.environ.get`
读取，**不得 cache 模块级常量**——避免 conftest `monkeypatch.setenv` 失效。
"""

from __future__ import annotations

import os
import time
from typing import Any

import jwt

ACCESS_TTL_SECONDS = 15 * 60
REFRESH_TTL_SECONDS = 7 * 24 * 60 * 60
_ALGORITHM = "HS256"


class TokenError(Exception):
    """JWT 解码 / secret 缺失 / 过期 等错误的统一类型。"""


def _get_secret() -> str:
    secret = os.environ.get("DATAPLAT_JWT_SECRET")
    if not secret:
        raise TokenError("DATAPLAT_JWT_SECRET 未设置")
    return secret


def encode_access_token(user_id: str, role: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "role": role,
        "typ": "access",
        "iat": now,
        "exp": now + ACCESS_TTL_SECONDS,
    }
    return jwt.encode(payload, _get_secret(), algorithm=_ALGORITHM)


def encode_refresh_token(user_id: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "typ": "refresh",
        "iat": now,
        "exp": now + REFRESH_TTL_SECONDS,
    }
    return jwt.encode(payload, _get_secret(), algorithm=_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _get_secret(), algorithms=[_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
