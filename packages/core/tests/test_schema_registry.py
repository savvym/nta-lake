"""SchemaRegistry + builtin schemas 行为测试 (W1-3 silver-schema-enforce AC-1)."""

from __future__ import annotations


def test_registry_imports_and_builtins() -> None:
    """AC-1: SchemaRegistry + SchemaEntry + 2 builtin 注册 + 跨层抛 ValueError + 重复抛 ValueError + 缺失抛 KeyError."""
    import pytest
    from dataplat_core.schemas import GoldSFTRow, SchemaEntry, SchemaRegistry, SilverRow

    # 2 个 builtin 已注册
    assert SchemaRegistry.is_registered("silver-text-v1")
    assert SchemaRegistry.is_registered("gold-sft-v1")

    silver_entry = SchemaRegistry.get("silver-text-v1")
    assert isinstance(silver_entry, SchemaEntry)
    assert silver_entry.row_cls is SilverRow
    assert silver_entry.layer == "silver"

    gold_entry = SchemaRegistry.get("gold-sft-v1")
    assert gold_entry.row_cls is GoldSFTRow
    assert gold_entry.layer == "gold"

    # 重复 register 抛 ValueError
    with pytest.raises(ValueError):
        SchemaRegistry.register("silver-text-v1", SilverRow, "silver")

    # 缺失 get 抛 KeyError
    with pytest.raises(KeyError):
        SchemaRegistry.get("does-not-exist")

    # list_ids 含两个
    ids = SchemaRegistry.list_ids()
    assert "silver-text-v1" in ids
    assert "gold-sft-v1" in ids
