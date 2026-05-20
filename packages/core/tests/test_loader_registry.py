"""LoaderRegistry 行为测试 (W1-4 AC-1)."""

from __future__ import annotations

import pytest


def test_loader_registry_full_behavior() -> None:
    """AC-1: register / get / list_names / 重复 ValueError / 缺失 KeyError."""
    from dataplat_core.loaders import LoaderRegistry

    # 用唯一前缀避免跨测试污染（LoaderRegistry 模块级单例）
    name = "test-loader-ac1-unique"

    # register + get
    class FakeLoader:
        name = "test-loader-ac1-unique"
        version = "0.1"
        input_subtype = "pdf"
        output_schema_id = "silver-text-v1"

    LoaderRegistry.register(name, FakeLoader)
    assert LoaderRegistry.get(name) is FakeLoader

    # list_names 包含已注册名称
    assert name in LoaderRegistry.list_names()

    # 重复注册 → ValueError
    with pytest.raises(ValueError, match=name):
        LoaderRegistry.register(name, FakeLoader)

    # 未注册名称 → KeyError
    with pytest.raises(KeyError):
        LoaderRegistry.get("does-not-exist-loader-xyz")
