"""image-to-text Operator suite (W2-3) 行为测试。

AC-1: ImageStripOperator 清空 images + 写 stats.image_count=0
AC-2: ImageCaptionStubOperator 有 images → 追加 caption marker 到 text
AC-3: ImageCaptionStubOperator images=[] → no-op（text 不变，lineage_ops 仍追加）
AC-4: OperatorRegistry import 后含 "image_strip" 和 "image_caption_stub"，总数 == 7
"""

from __future__ import annotations

from types import SimpleNamespace

from dataplat_core.operators.image_caption_stub import ImageCaptionStubOperator
from dataplat_core.operators.image_strip import ImageStripOperator
from dataplat_core.protocols.loader import SilverRow

_SOURCE_REF = {"blob_sha": "a" * 64, "path": "test.pdf"}

_IMAGES_2 = [
    {"filename": "fig1.png", "blob_sha": "deadbeef" + "0" * 56},
    {"filename": "fig2.jpg", "blob_sha": "cafebabe" + "0" * 56},
]


def _make_row(
    text: str = "hello world",
    stats: dict | None = None,
    lineage_ops: list[dict] | None = None,
    images: list[dict] | None = None,
) -> SilverRow:
    return SilverRow(
        text=text,
        images=images if images is not None else [],
        source_ref=_SOURCE_REF,
        stats=stats or {},
        lineage_ops=lineage_ops or [],
    )


def test_image_strip_clears_images() -> None:
    """AC-1: 喂 row 带 2 images → 返 1 row，images=[]，stats.image_count=0，
    lineage_ops 追加正确，原 row 未 mutate。
    """
    orig_stats = {"tokens": 10, "image_count": 2}
    orig_lineage: list[dict] = [{"op": "score", "version": "1.0", "metric": "text_chars"}]

    row = _make_row(
        text="some text",
        stats=orig_stats,
        lineage_ops=orig_lineage,
        images=list(_IMAGES_2),  # 拷贝，防 mutate 检测干扰
    )
    op = ImageStripOperator()
    ctx = SimpleNamespace()  # type: ignore[assignment]

    out = op.run(row, {}, ctx)  # type: ignore[arg-type]

    # 返回 1 row（1→1）
    assert len(out) == 1
    new_row = out[0]

    # images 清空
    assert new_row.images == []

    # stats.image_count 写为 0；原 stats 其他字段保留
    assert new_row.stats["image_count"] == 0
    assert new_row.stats["tokens"] == 10

    # lineage_ops 追加正确
    assert new_row.lineage_ops[-1] == {"op": "image_strip", "version": "1.0"}
    # 原 lineage 前缀保留
    assert new_row.lineage_ops[0] == orig_lineage[0]

    # 原 row 未 mutate
    assert row.images == _IMAGES_2
    assert row.stats == orig_stats
    assert row.lineage_ops == orig_lineage

    # text / source_ref 透传不变
    assert new_row.text == row.text
    assert new_row.source_ref is row.source_ref


def test_image_caption_stub_appends_markers() -> None:
    """AC-2: 喂 row text="hello" + 2 images → 返 1 row，
    text 含原文本 + 2 个 caption marker，stats.image_captions_added=2，images 保留原值。
    """
    row = _make_row(
        text="hello",
        images=list(_IMAGES_2),
    )
    op = ImageCaptionStubOperator()
    ctx = SimpleNamespace()  # type: ignore[assignment]

    out = op.run(row, {}, ctx)  # type: ignore[arg-type]

    # 返回 1 row（1→1）
    assert len(out) == 1
    new_row = out[0]

    # 期望占位符（默认 template + separator）
    sep = "\n\n"
    img1_marker = f"[image: fig1.png ({_IMAGES_2[0]['blob_sha'][:8]})]"
    img2_marker = f"[image: fig2.jpg ({_IMAGES_2[1]['blob_sha'][:8]})]"
    expected_text = "hello" + sep + img1_marker + sep + img2_marker
    assert new_row.text == expected_text

    # stats.image_captions_added=2
    assert new_row.stats["image_captions_added"] == 2

    # images 保留原值（不清空）
    assert new_row.images == _IMAGES_2

    # lineage_ops 追加正确
    assert new_row.lineage_ops[-1] == {
        "op": "image_caption_stub",
        "version": "1.0",
        "image_count": 2,
    }

    # 原 row 未 mutate
    assert row.text == "hello"
    assert row.images == _IMAGES_2


def test_image_caption_stub_no_images_noop() -> None:
    """AC-3: 喂 row images=[] → 返 1 row，text 不变，lineage_ops 仍追加。"""
    row = _make_row(
        text="no images here",
        images=[],
    )
    op = ImageCaptionStubOperator()
    ctx = SimpleNamespace()  # type: ignore[assignment]

    out = op.run(row, {}, ctx)  # type: ignore[arg-type]

    # 返回 1 row（1→1 no-op）
    assert len(out) == 1
    new_row = out[0]

    # text 不变
    assert new_row.text == "no images here"

    # stats 不变（无 image_captions_added key）
    assert "image_captions_added" not in new_row.stats

    # lineage_ops 仍追加（image_count=0）
    assert new_row.lineage_ops[-1] == {
        "op": "image_caption_stub",
        "version": "1.0",
        "image_count": 0,
    }

    # images 仍为空
    assert new_row.images == []


def test_image_operators_registered() -> None:
    """AC-4: import operators 包后 list_names() 含 "image_strip" 和 "image_caption_stub"，
    且总注册数 == 7。
    """
    from dataplat_core.operators import OperatorRegistry  # noqa: PLC0415

    names = OperatorRegistry.list_names()

    assert "image_strip" in names
    assert "image_caption_stub" in names
    assert len(names) >= 9  # W2-4 后至少 9 个内置算子（7 + snapshot_tag + snapshot_sample）
