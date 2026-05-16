"""共享类型别名。

`SHA256`：64 字符小写 hex 字符串。用于 Commit.hash / Tree.hash /
BlobRef.sha256 / TreeEntry.target_hash / ProducedBy.config_hash 等所有
sha256 句柄字段，统一为**纯 64-hex**（无 `sha256:` 前缀）。
"""

from __future__ import annotations

from typing import Annotated

from pydantic import StringConstraints

SHA256 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
