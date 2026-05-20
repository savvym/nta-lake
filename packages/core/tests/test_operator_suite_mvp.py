"""operator-suite-mvp (W2-1) 行为测试：FilterOperator / DedupOperator / ScoreOperator + auto-register。"""

from __future__ import annotations

from types import SimpleNamespace

from dataplat_core.operators.dedup import DedupOperator
from dataplat_core.operators.filter import FilterOperator
from dataplat_core.operators.score import ScoreOperator
from dataplat_core.protocols.loader import SilverRow

_SOURCE_REF = {"blob_sha": "a" * 64, "path": "test.txt"}


def _make_row(text: str, stats: dict | None = None) -> SilverRow:
    return SilverRow(
        text=text,
        images=[],
        source_ref=_SOURCE_REF,
        stats=stats or {},
        lineage_ops=[],
    )


def test_filter_operator_drop_and_keep() -> None:
    """AC-1: min_chars 丢弃短行；保留长行并追加 lineage_ops；输入未 mutate。"""
    op = FilterOperator()
    ctx = SimpleNamespace()  # type: ignore[assignment]

    row_short = _make_row("hi")           # 2 chars
    row_long = _make_row("a" * 20)        # 20 chars

    # 短行被丢弃
    assert op.run(row_short, {"min_chars": 10}, ctx) == []  # type: ignore[arg-type]

    # 长行保留
    out = op.run(row_long, {"min_chars": 10}, ctx)  # type: ignore[arg-type]
    assert len(out) == 1
    assert out[0].lineage_ops == [{"op": "filter", "version": "1.0", "min_chars": 10}]

    # 输入未被 mutate
    assert row_long.lineage_ops == []


def test_dedup_operator_text_key() -> None:
    """AC-2: 相同 text 的两行，第二行被去重；ctx._dedup_seen 仅 1 项。"""
    op = DedupOperator()
    ctx = SimpleNamespace()  # type: ignore[assignment]

    row1 = _make_row("hello")
    row2 = _make_row("hello")

    out1 = op.run(row1, {"key": "text"}, ctx)  # type: ignore[arg-type]
    out2 = op.run(row2, {"key": "text"}, ctx)  # type: ignore[arg-type]

    assert len(out1) == 1
    assert out2 == []
    assert len(ctx._dedup_seen) == 1
    assert out1[0].lineage_ops[-1] == {"op": "dedup", "version": "1.0", "key": "text"}


def test_score_operator_text_chars() -> None:
    """AC-3: text_chars metric 写入 stats；输入 stats / lineage_ops 未 mutate。"""
    op = ScoreOperator()

    row = SilverRow(
        text="hello world",
        images=[],
        source_ref=_SOURCE_REF,
        stats={"tokens": 2},
        lineage_ops=[],
    )

    out = op.run(row, {"metric": "text_chars"}, SimpleNamespace())  # type: ignore[arg-type]

    assert len(out) == 1
    assert out[0].stats == {"tokens": 2, "score_text_chars": 11}
    assert out[0].lineage_ops == [{"op": "score", "version": "1.0", "metric": "text_chars"}]

    # 输入未被 mutate
    assert row.stats == {"tokens": 2}
    assert row.lineage_ops == []


def test_all_four_operators_registered() -> None:
    """AC-4: import operators 包后 4 个内置算子均已自动注册。"""
    from dataplat_core.operators import OperatorRegistry  # noqa: PLC0415

    names = OperatorRegistry.list_names()
    assert "identity" in names
    assert "filter" in names
    assert "dedup" in names
    assert "score" in names
