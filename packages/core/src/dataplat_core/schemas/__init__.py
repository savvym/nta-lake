"""dataplat_core.schemas：SchemaRegistry + 内置行 schema。

导出：
    SchemaRegistry  — 模块级单例，注册 / 查找 row schema
    SchemaEntry     — 注册条目（schema_id + row_cls + layer）
    SilverRow       — Silver 层行 schema（re-export from protocols.loader）
    GoldSFTRow      — Gold SFT 行 schema

import 本模块时自动触发内置 schema 注册（silver-text-v1 / gold-sft-v1）。
"""

from dataplat_core.schemas.gold_row import GoldSFTRow
from dataplat_core.schemas.registry import SchemaEntry, SchemaRegistry
from dataplat_core.schemas.silver_row import SilverRow

from . import _builtin  # noqa: F401  触发内置 schema 注册

__all__ = [
    "SchemaRegistry",
    "SchemaEntry",
    "SilverRow",
    "GoldSFTRow",
]
