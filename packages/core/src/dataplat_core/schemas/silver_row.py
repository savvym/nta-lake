"""Silver 层行 schema（re-export）。

从 protocols.loader 稳定导出 SilverRow，让 schema_id 注册时 import 路径保持稳定。
SilverRow 定义本体在 dataplat_core.protocols.loader（W1-2 已落定，不移动）。
"""

from __future__ import annotations

from dataplat_core.protocols.loader import SilverRow

__all__ = ["SilverRow"]
