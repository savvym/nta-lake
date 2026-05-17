"""argon2-cffi 密码哈希工具。

按 .harness/design.md §11.6：argon2 抗 GPU 暴破强于 bcrypt。
`PasswordHasher` 是 argon2-cffi 推荐用法，线程安全；本模块用单例。
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    """生成 argon2id 哈希；每次包含随机 salt（同 plain 产生不同 hash）。"""
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与 hash 是否匹配；不匹配 / hash 格式错均返 False。"""
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False
    except Exception:  # noqa: BLE001 — 容错：hash 格式坏 / 算法不支持 → 视作不匹配
        return False
