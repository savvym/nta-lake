"""ChunkerOperator (W2-2) 行为测试：1→N 切分语义 + auto-register。"""

from __future__ import annotations

from types import SimpleNamespace

from dataplat_core.operators.chunker import ChunkerOperator
from dataplat_core.protocols.loader import SilverRow

_SOURCE_REF = {"blob_sha": "b" * 64, "path": "test.txt"}


def _make_row(
    text: str,
    stats: dict | None = None,
    lineage_ops: list[dict] | None = None,
    images: list[dict] | None = None,
) -> SilverRow:
    return SilverRow(
        text=text,
        images=images or [],
        source_ref=_SOURCE_REF,
        stats=stats or {},
        lineage_ops=lineage_ops or [],
    )


def test_chunker_basic_split() -> None:
    """AC-1: text 25 chars + max_chars=10 → 切 3 个 (10/10/5)。

    校验：
    - len(out) == 3
    - 每个 out[i].text 正确
    - stats.chunk_index / chunk_total / text_chars 正确
    - lineage_ops 追加正确（含 max_chars + chunk_index + chunk_total）
    - 原 row 未 mutate（lineage_ops / stats 不变）
    - source_ref / images 透传不变
    """
    text = "a" * 10 + "b" * 10 + "c" * 5  # 25 chars
    op = ChunkerOperator()
    ctx = SimpleNamespace()  # type: ignore[assignment]

    orig_lineage: list[dict] = [{"op": "score", "version": "1.0", "metric": "text_chars"}]
    orig_stats: dict = {"tokens": 5, "text_chars": 25}
    images: list[dict] = [{"url": "img.png"}]

    row = _make_row(text, stats=orig_stats, lineage_ops=orig_lineage, images=images)
    out = op.run(row, {"max_chars": 10}, ctx)  # type: ignore[arg-type]

    # 切片数量
    assert len(out) == 3

    # 每个切片文本正确
    assert [r.text for r in out] == [text[0:10], text[10:20], text[20:25]]

    # stats.chunk_index 正确
    assert out[0].stats["chunk_index"] == 0
    assert out[1].stats["chunk_index"] == 1
    assert out[2].stats["chunk_index"] == 2

    # stats.chunk_total 均为 3
    assert all(r.stats["chunk_total"] == 3 for r in out)

    # stats.text_chars 覆盖为切片长度
    assert out[0].stats["text_chars"] == 10
    assert out[1].stats["text_chars"] == 10
    assert out[2].stats["text_chars"] == 5

    # 原 stats 的其他字段保留
    assert all(r.stats["tokens"] == 5 for r in out)

    # lineage_ops 最后一项正确
    assert out[0].lineage_ops[-1] == {
        "op": "chunker",
        "version": "1.0",
        "max_chars": 10,
        "chunk_index": 0,
        "chunk_total": 3,
    }
    assert out[2].lineage_ops[-1] == {
        "op": "chunker",
        "version": "1.0",
        "max_chars": 10,
        "chunk_index": 2,
        "chunk_total": 3,
    }

    # lineage_ops 前缀（原 lineage）保留
    assert all(r.lineage_ops[0] == orig_lineage[0] for r in out)

    # 原 row 未 mutate
    assert row.lineage_ops == orig_lineage
    assert row.stats == orig_stats

    # source_ref / images 透传
    assert all(r.source_ref is row.source_ref for r in out)
    assert all(r.images == images for r in out)


def test_chunker_empty_returns_empty() -> None:
    """AC-2: text="" → 返 []（drop empty）。"""
    op = ChunkerOperator()
    ctx = SimpleNamespace()  # type: ignore[assignment]

    row = _make_row("")
    out = op.run(row, {"max_chars": 10}, ctx)  # type: ignore[arg-type]

    assert out == []


def test_chunker_exact_boundary() -> None:
    """AC-3: text 长度恰好 == max_chars → 返 1 row，chunk_index=0, chunk_total=1。"""
    text = "x" * 10
    op = ChunkerOperator()
    ctx = SimpleNamespace()  # type: ignore[assignment]

    row = _make_row(text)
    out = op.run(row, {"max_chars": 10}, ctx)  # type: ignore[arg-type]

    assert len(out) == 1
    assert out[0].text == text
    assert out[0].stats["chunk_index"] == 0
    assert out[0].stats["chunk_total"] == 1
    assert out[0].stats["text_chars"] == 10
    assert out[0].lineage_ops[-1] == {
        "op": "chunker",
        "version": "1.0",
        "max_chars": 10,
        "chunk_index": 0,
        "chunk_total": 1,
    }


def test_chunker_registered() -> None:
    """AC-4: import operators 包后 "chunker" 已自动注册到 OperatorRegistry。"""
    from dataplat_core.operators import OperatorRegistry  # noqa: PLC0415

    assert "chunker" in OperatorRegistry.list_names()
