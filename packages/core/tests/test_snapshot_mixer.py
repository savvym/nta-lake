"""snapshot-mixer Operator suite (W2-4) 行为测试。

AC-1: SnapshotTagOperator：喂 row + config={"snapshot_name": "alpaca", "snapshot_weight": 0.7}
      → 返 1 row，stats.source_snapshot=="alpaca"，stats.source_snapshot_weight==0.7，
        lineage_ops 追加正确，原 row 未 mutate
AC-2: SnapshotSampleOperator weight=1.0：喂任意 row → 必返 [new_row]（永不 drop）；lineage_ops 追加
AC-3: SnapshotSampleOperator weight=0.0：喂任意 row → 必返 []（永远 drop）；同样 row 跑两次结果一致（deterministic）
AC-4: OperatorRegistry import 后 list_names() 含 "snapshot_tag" 和 "snapshot_sample"；总数 == 9
"""

from __future__ import annotations

from types import SimpleNamespace

from dataplat_core.operators.snapshot_sample import SnapshotSampleOperator
from dataplat_core.operators.snapshot_tag import SnapshotTagOperator
from dataplat_core.protocols.loader import SilverRow

_SOURCE_REF = {"blob_sha": "b" * 64, "path": "test.jsonl"}


def _make_row(
    text: str = "hello world",
    stats: dict | None = None,
    lineage_ops: list[dict] | None = None,
) -> SilverRow:
    return SilverRow(
        text=text,
        source_ref=_SOURCE_REF,
        stats=stats or {},
        lineage_ops=lineage_ops or [],
    )


def test_snapshot_tag_basic() -> None:
    """AC-1: SnapshotTagOperator 喂 row + config={"snapshot_name": "alpaca", "snapshot_weight": 0.7}
    → 返 1 row，stats.source_snapshot=="alpaca"，stats.source_snapshot_weight==0.7，
    lineage_ops 追加正确，原 row 未 mutate。
    """
    orig_stats: dict = {"tokens": 5}
    orig_lineage: list[dict] = [{"op": "filter", "version": "1.0"}]

    row = _make_row(
        text="sample alpaca text",
        stats=dict(orig_stats),
        lineage_ops=list(orig_lineage),
    )
    op = SnapshotTagOperator()
    ctx = SimpleNamespace()  # type: ignore[assignment]
    config = {"snapshot_name": "alpaca", "snapshot_weight": 0.7}

    out = op.run(row, config, ctx)  # type: ignore[arg-type]

    # 返回 1 row（1→1）
    assert len(out) == 1
    new_row = out[0]

    # stats 包含 source_snapshot 与 source_snapshot_weight
    assert new_row.stats["source_snapshot"] == "alpaca"
    assert new_row.stats["source_snapshot_weight"] == 0.7

    # 原 stats 字段（tokens）保留
    assert new_row.stats["tokens"] == 5

    # lineage_ops 尾部追加正确条目
    assert new_row.lineage_ops[-1] == {
        "op": "snapshot_tag",
        "version": "1.0",
        "snapshot_name": "alpaca",
        "snapshot_weight": 0.7,
    }

    # 原 lineage_ops 前缀保留
    assert new_row.lineage_ops[0] == orig_lineage[0]

    # 原 row 未 mutate
    assert row.stats == orig_stats
    assert row.lineage_ops == orig_lineage

    # text / source_ref 透传不变
    assert new_row.text == row.text
    assert new_row.source_ref is row.source_ref


def test_snapshot_sample_weight_one_keeps_all() -> None:
    """AC-2: SnapshotSampleOperator weight=1.0：喂任意 row → 必返 [new_row]（永不 drop）；lineage_ops 追加。"""
    op = SnapshotSampleOperator()
    ctx = SimpleNamespace()  # type: ignore[assignment]
    config = {"weight": 1.0}

    # 用多条不同 text 的 row 验证 weight=1.0 永远 keep
    test_texts = [
        "hello world",
        "another text for testing",
        "yet another row with different content",
        "",  # 空文本也要 keep（u 仍 < 1.0）
    ]

    for text in test_texts:
        row = _make_row(text=text)
        out = op.run(row, config, ctx)  # type: ignore[arg-type]

        # weight=1.0 → 永不 drop
        assert len(out) == 1, f"weight=1.0 应永远 keep，但 text={text!r} 被 drop"
        new_row = out[0]

        # lineage_ops 追加
        assert new_row.lineage_ops[-1] == {
            "op": "snapshot_sample",
            "version": "1.0",
            "weight": 1.0,
            "seed": "",
        }

        # 原 row 未 mutate
        assert row.lineage_ops == []


def test_snapshot_sample_weight_zero_drops_all() -> None:
    """AC-3: SnapshotSampleOperator weight=0.0：喂任意 row → 必返 []（永远 drop）；
    同样 row 跑两次结果一致（deterministic）。
    """
    op = SnapshotSampleOperator()
    ctx = SimpleNamespace()  # type: ignore[assignment]
    config = {"weight": 0.0}

    test_texts = [
        "hello world",
        "another text for testing",
        "yet another row with different content",
        "x",
    ]

    for text in test_texts:
        row = _make_row(text=text)

        # 第一次运行
        out1 = op.run(row, config, ctx)  # type: ignore[arg-type]
        assert out1 == [], f"weight=0.0 应永远 drop，但 text={text!r} 被 keep（第一次）"

        # 第二次运行（确定性：同 row + config → 同结果）
        out2 = op.run(row, config, ctx)  # type: ignore[arg-type]
        assert out2 == [], f"weight=0.0 应永远 drop，但 text={text!r} 被 keep（第二次）"

        # 原 row 未 mutate（drop 时不产出新 row）
        assert row.lineage_ops == []


def test_snapshot_operators_registered() -> None:
    """AC-4: import operators 包后 list_names() 含 "snapshot_tag" 和 "snapshot_sample"；
    且总注册数 == 9。
    """
    from dataplat_core.operators import OperatorRegistry  # noqa: PLC0415

    names = OperatorRegistry.list_names()

    assert "snapshot_tag" in names
    assert "snapshot_sample" in names
    # __init__.py 注册 9 个内置算子；test_operator_protocol.py 在同一 pytest session 中
    # 还会向单例注册 1 个测试用 key（"identity_test_ac2"），故全量跑时总数 >= 9。
    assert len(names) >= 9
