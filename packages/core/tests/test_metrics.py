"""MetricsRegistry 行为测试（W4-7 AC-2）。

4 tests（asyncio_mode="auto" at workspace root，不需 @pytest.mark.asyncio）：
1. record happy path：N 次 → runs/rows_in/rows_out 累计正确
2. record error=True：errors 自增 1；rows_out 不计
3. snapshot 排序：多 operator 按 name 字母序
4. reset 清空 registry
"""

from __future__ import annotations

import pytest
from dataplat_core.metrics import (
    get_metrics_registry,
    reset_metrics_registry,
)

# ---------------------------------------------------------------------------
# Test 1: record happy path
# ---------------------------------------------------------------------------


async def test_record_happy_path() -> None:
    """record_op_run happy path：N 次 → runs/rows_in/rows_out 累计正确。"""
    reset_metrics_registry()
    registry = get_metrics_registry()

    await registry.record_op_run("filter", rows_in=10, rows_out=8, duration_ms=5.0)
    await registry.record_op_run("filter", rows_in=5, rows_out=5, duration_ms=2.5)

    snaps = registry.snapshot()
    assert len(snaps) == 1
    snap = snaps[0]
    assert snap.operator_name == "filter"
    assert snap.runs == 2
    assert snap.rows_in == 15
    assert snap.rows_out == 13
    assert snap.errors == 0
    assert snap.duration_ms_total == pytest.approx(7.5)
    assert snap.duration_ms_avg == pytest.approx(3.75)


# ---------------------------------------------------------------------------
# Test 2: record error=True
# ---------------------------------------------------------------------------


async def test_record_error() -> None:
    """record_op_run error=True：errors 自增 1；rows_out 不累计（传 0）。"""
    reset_metrics_registry()
    registry = get_metrics_registry()

    await registry.record_op_run("chunker", rows_in=5, rows_out=0, duration_ms=3.0, error=True)

    snaps = registry.snapshot()
    assert len(snaps) == 1
    snap = snaps[0]
    assert snap.operator_name == "chunker"
    assert snap.runs == 1
    assert snap.rows_in == 5
    assert snap.rows_out == 0
    assert snap.errors == 1
    assert snap.duration_ms_avg == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Test 3: snapshot 字母序
# ---------------------------------------------------------------------------


async def test_snapshot_sorted() -> None:
    """snapshot 返回按 operator_name 字母序排列的列表。"""
    reset_metrics_registry()
    registry = get_metrics_registry()

    # 故意乱序注册
    await registry.record_op_run("snapshot_tag", rows_in=2, rows_out=2, duration_ms=1.0)
    await registry.record_op_run("chunker", rows_in=2, rows_out=4, duration_ms=2.0)
    await registry.record_op_run("filter", rows_in=4, rows_out=3, duration_ms=1.5)

    snaps = registry.snapshot()
    assert len(snaps) == 3
    names = [s.operator_name for s in snaps]
    assert names == sorted(names), f"期望字母序，实得：{names}"
    assert names == ["chunker", "filter", "snapshot_tag"]


# ---------------------------------------------------------------------------
# Test 4: reset 清空
# ---------------------------------------------------------------------------


async def test_reset() -> None:
    """reset() 清空 registry；清后 snapshot() 返空列表；再记录后仍正常工作。"""
    reset_metrics_registry()
    registry = get_metrics_registry()

    await registry.record_op_run("filter", rows_in=3, rows_out=3, duration_ms=1.0)
    assert len(registry.snapshot()) == 1

    await registry.reset()
    assert registry.snapshot() == []

    # 清后再记录，仍正常
    await registry.record_op_run("filter", rows_in=1, rows_out=1, duration_ms=0.5)
    snaps = registry.snapshot()
    assert len(snaps) == 1
    assert snaps[0].runs == 1
