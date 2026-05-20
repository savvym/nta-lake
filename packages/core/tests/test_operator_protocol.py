"""Operator Protocol + Registry + IdentityOperator 行为测试 (W1-2)."""

from __future__ import annotations


def test_protocol_import_set() -> None:
    """AC-1: 5 个核心 + 1 个 IdentityOperator import + 类型校验."""
    from dataplat_core.protocols import Loader, LoadResult, Operator, OperatorSpec, SilverRow
    from dataplat_core.operators import IdentityOperator, OperatorRegistry

    assert Loader is not None
    assert LoadResult is not None
    assert SilverRow is not None
    assert Operator is not None
    assert OperatorSpec is not None
    assert IdentityOperator is not None
    assert OperatorRegistry is not None


def test_registry_register_and_lookup() -> None:
    """AC-2: register + get + list_names + 重复抛 ValueError + 缺失抛 KeyError."""
    import pytest
    from dataplat_core.operators import IdentityOperator, OperatorRegistry

    # 用唯一前缀避免跨测试污染（OperatorRegistry 模块级单例）
    name = "identity_test_ac2"
    OperatorRegistry.register(name, IdentityOperator)
    assert OperatorRegistry.get(name) is IdentityOperator
    assert name in OperatorRegistry.list_names()
    with pytest.raises(ValueError):
        OperatorRegistry.register(name, IdentityOperator)
    with pytest.raises(KeyError):
        OperatorRegistry.get("does-not-exist-x")


def test_identity_operator_passthrough() -> None:
    """AC-3: IdentityOperator 返新 row，lineage_ops 追加 identity 一条，输入不被 mutate."""
    from dataplat_core.operators import IdentityOperator
    from dataplat_core.protocols import SilverRow

    # 注意：RunContext 是 Protocol；测试可用 SimpleNamespace 或 minimal class
    from types import SimpleNamespace

    ctx = SimpleNamespace()  # type: ignore[assignment]

    row = SilverRow(
        text="hello",
        images=[],
        source_ref={"blob_sha": "a" * 64, "path": "x.txt"},
        stats={"tokens": 1},
        lineage_ops=[],
    )
    op = IdentityOperator()
    out = op.run(row, config={}, ctx=ctx)  # type: ignore[arg-type]

    assert len(out) == 1
    assert out[0].text == "hello"
    assert out[0].source_ref == {"blob_sha": "a" * 64, "path": "x.txt"}
    assert out[0].stats == {"tokens": 1}
    assert out[0].lineage_ops == [{"op": "identity", "version": "1.0"}]
    # 输入未被 mutate
    assert row.lineage_ops == []
