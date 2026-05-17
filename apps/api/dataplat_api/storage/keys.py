"""CAS blob 的 storage key 规范工具。

按 .harness/design.md §5.2：key = `blobs/{sha256[0:2]}/{sha256}`。
所有 producer / consumer 必须通过本工具构造 key，不允许字符串字面拼接。
"""

from __future__ import annotations

import re

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def storage_key_for(sha256: str) -> str:
    """从纯 64-hex sha256 构造 CAS 存储 key。

    Args:
        sha256: 64 字符小写 hex；大写 / 非 hex / 长度错误均 raise ValueError

    Returns:
        `blobs/{前两位}/{完整 sha256}`
    """
    if not _SHA256_RE.match(sha256):
        raise ValueError(
            f"sha256 必须是 64 字符小写 hex；得到 len={len(sha256)} value={sha256!r}"
        )
    return f"blobs/{sha256[:2]}/{sha256}"
