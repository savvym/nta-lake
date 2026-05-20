"""内置 schema 注册。

模块顶层执行两个 SchemaRegistry.register 调用，
在 schemas/__init__.py import 时自动触发（import-once 原则）。

预注册：
    silver-text-v1  → SilverRow  (layer="silver")
    gold-sft-v1     → GoldSFTRow (layer="gold")
"""

from __future__ import annotations

from dataplat_core.schemas.gold_row import GoldSFTRow
from dataplat_core.schemas.registry import SchemaRegistry
from dataplat_core.schemas.silver_row import SilverRow

SchemaRegistry.register("silver-text-v1", SilverRow, "silver")
SchemaRegistry.register("gold-sft-v1", GoldSFTRow, "gold")
