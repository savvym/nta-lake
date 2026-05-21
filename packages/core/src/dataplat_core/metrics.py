"""Operator metrics：进程内累计器 + 快照。

设计决策（W4-7）：
- per-operator 统计：runs / rows_in / rows_out / errors / duration_ms_total
- asyncio.Lock 保并发安全（与 [[cost-ledger-asyncio-lock]] 同模式）
- 进程内单例：get_metrics_registry() / reset_metrics_registry()
- snapshot() 按 operator_name 字母序，不加锁（读 float/int 原子性足够）
- duration_ms_avg 在 snapshot 时计算（避免存两份同步状态）
"""

from __future__ import annotations

import asyncio
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, computed_field

# ---------------------------------------------------------------------------
# OperatorMetrics — 单个 operator 的累计统计快照
# ---------------------------------------------------------------------------


class OperatorMetrics(BaseModel):
    """单个 operator 的运行统计快照（只读，在 snapshot() 时构造）。"""

    model_config = ConfigDict(extra="forbid")

    operator_name: str
    runs: int
    rows_in: int
    rows_out: int
    errors: int
    duration_ms_total: float

    @computed_field  # type: ignore[misc]
    @property
    def duration_ms_avg(self) -> float:
        """平均耗时（ms）；runs=0 时返 0.0。"""
        if self.runs == 0:
            return 0.0
        return self.duration_ms_total / self.runs


# ---------------------------------------------------------------------------
# MetricsRegistry — 进程内累计器
# ---------------------------------------------------------------------------


class MetricsRegistry:
    """进程内 operator 运行统计累计器；asyncio.Lock 保并发安全。

    内部结构：
      _data[operator_name] = {
          "runs": int,
          "rows_in": int,
          "rows_out": int,
          "errors": int,
          "duration_ms_total": float,
      }
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._data: dict[str, dict[str, int | float]] = {}

    async def record_op_run(
        self,
        operator_name: str,
        rows_in: int,
        rows_out: int,
        duration_ms: float,
        error: bool = False,
    ) -> None:
        """记录一次 operator 运行（加锁）。

        Args:
            operator_name: 已注册的 operator 名称。
            rows_in:       输入 row 数（operator 调用前）。
            rows_out:      输出 row 数（operator 调用后）；error=True 时通常为 0。
            duration_ms:   耗时毫秒（perf_counter 测量）。
            error:         是否发生异常（True = error 计数 +1）。
        """
        async with self._lock:
            bucket = self._data.setdefault(
                operator_name,
                {"runs": 0, "rows_in": 0, "rows_out": 0, "errors": 0, "duration_ms_total": 0.0},
            )
            bucket["runs"] = int(bucket["runs"]) + 1
            bucket["rows_in"] = int(bucket["rows_in"]) + rows_in
            bucket["rows_out"] = int(bucket["rows_out"]) + rows_out
            bucket["errors"] = int(bucket["errors"]) + (1 if error else 0)
            bucket["duration_ms_total"] = float(bucket["duration_ms_total"]) + duration_ms

    def snapshot(self) -> list[OperatorMetrics]:
        """返回当前统计快照（不加锁；按 operator_name 字母序）。

        Returns:
            list[OperatorMetrics] 按 operator_name 升序排序。
        """
        result: list[OperatorMetrics] = []
        for name in sorted(self._data.keys()):
            b = self._data[name]
            result.append(
                OperatorMetrics(
                    operator_name=name,
                    runs=int(b["runs"]),
                    rows_in=int(b["rows_in"]),
                    rows_out=int(b["rows_out"]),
                    errors=int(b["errors"]),
                    duration_ms_total=float(b["duration_ms_total"]),
                )
            )
        return result

    async def reset(self) -> None:
        """清空所有统计（加锁；测试隔离用）。"""
        async with self._lock:
            self._data.clear()


# ---------------------------------------------------------------------------
# 进程内单例
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_metrics_registry() -> MetricsRegistry:
    """进程内单例；测试用 reset_metrics_registry() 清掉。"""
    return MetricsRegistry()


def reset_metrics_registry() -> None:
    """测试辅助：清掉单例，下次 get_metrics_registry() 重新构造。"""
    get_metrics_registry.cache_clear()
