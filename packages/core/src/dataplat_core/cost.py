"""LLM cost 抽象：价格表 + Ledger + BudgetExceeded。

设计决策：
- 价格表 hard-coded（不引入 env / YAML）；变更走 PR 修常量。
- 进程内 ledger（asyncio.Lock 保并发安全）；跨 worker 持久化是 follow-up。
- fake-model rate = 0/0；CI 默认 FakeLLMProvider 不被预算阻断。
- _DEFAULT_RATE 兜底（sonnet 当前价位 0.003 input / 0.015 output per 1k tok）。
"""

from __future__ import annotations

import asyncio
from collections import defaultdict

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Rate / Entry
# ---------------------------------------------------------------------------


class CostRate(BaseModel):
    """单个 model 的 token 价格。"""

    model_config = ConfigDict(extra="forbid")

    model_id: str
    input_per_1k_usd: float
    output_per_1k_usd: float


class CostLedgerEntry(BaseModel):
    """单次 LLM 调用的计费记录。"""

    model_config = ConfigDict(extra="forbid")

    model_id: str
    input_tokens: int
    output_tokens: int
    usd: float
    scope: str = "default"


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class BudgetExceeded(Exception):
    """预算超额；包含上下文供 caller / 路由层返 402。"""

    def __init__(self, scope: str, current_usd: float, limit_usd: float) -> None:
        self.scope = scope
        self.current_usd = current_usd
        self.limit_usd = limit_usd
        super().__init__(
            f"Budget exceeded for scope={scope!r}: "
            f"current={current_usd:.6f} limit={limit_usd:.6f}"
        )


# ---------------------------------------------------------------------------
# Pure function
# ---------------------------------------------------------------------------


def compute_cost(rate: CostRate, input_tokens: int, output_tokens: int) -> float:
    """tokens → USD；纯函数，无副作用。"""
    return (
        rate.input_per_1k_usd * input_tokens / 1000.0
        + rate.output_per_1k_usd * output_tokens / 1000.0
    )


# ---------------------------------------------------------------------------
# Default price table
# ---------------------------------------------------------------------------

#: 已知 model 的价格；单位：USD / 1k tokens
DEFAULT_RATES: dict[str, CostRate] = {
    "claude-opus-4-7": CostRate(
        model_id="claude-opus-4-7",
        input_per_1k_usd=0.015,
        output_per_1k_usd=0.075,
    ),
    "claude-sonnet-4-6": CostRate(
        model_id="claude-sonnet-4-6",
        input_per_1k_usd=0.003,
        output_per_1k_usd=0.015,
    ),
    "claude-haiku-4-5-20251001": CostRate(
        model_id="claude-haiku-4-5-20251001",
        input_per_1k_usd=0.00025,
        output_per_1k_usd=0.00125,
    ),
    # fake-model：CI / 测试；price = 0 → budget 永不阻断
    "fake-model": CostRate(
        model_id="fake-model",
        input_per_1k_usd=0.0,
        output_per_1k_usd=0.0,
    ),
    # test-model：单元测试专用，非零价格
    "test-model": CostRate(
        model_id="test-model",
        input_per_1k_usd=0.003,
        output_per_1k_usd=0.015,
    ),
}

#: fallback：未知 model_id 时使用（sonnet 当前价位）
_DEFAULT_RATE = CostRate(
    model_id="__default__",
    input_per_1k_usd=0.003,
    output_per_1k_usd=0.015,
)


# ---------------------------------------------------------------------------
# CostLedger
# ---------------------------------------------------------------------------


class CostLedger:
    """进程内累计器；asyncio.Lock 保并发安全。

    内部结构：
      _entries[scope][model_id] = {"input_tokens": int, "output_tokens": int, "usd": float}
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        # scope → model_id → aggregated stats
        self._totals: dict[str, dict[str, dict[str, float]]] = defaultdict(
            lambda: defaultdict(lambda: {"input_tokens": 0.0, "output_tokens": 0.0, "usd": 0.0})
        )

    async def record(self, entry: CostLedgerEntry) -> None:
        """累加一条记录（加锁）。"""
        async with self._lock:
            bucket = self._totals[entry.scope][entry.model_id]
            bucket["input_tokens"] += entry.input_tokens
            bucket["output_tokens"] += entry.output_tokens
            bucket["usd"] += entry.usd

    def total_usd(self, scope: str | None = None) -> float:
        """返回累计 USD；scope=None 返全局合计（不加锁：读 float 原子性足够）。"""
        if scope is None:
            return sum(
                bucket["usd"]
                for models in self._totals.values()
                for bucket in models.values()
            )
        if scope not in self._totals:
            return 0.0
        return sum(bucket["usd"] for bucket in self._totals[scope].values())

    def breakdown(self, scope: str) -> list[dict]:
        """按 model_id 聚合；供 router GET 用。"""
        if scope not in self._totals:
            return []
        result = []
        for model_id, bucket in self._totals[scope].items():
            result.append(
                {
                    "model_id": model_id,
                    "input_tokens": int(bucket["input_tokens"]),
                    "output_tokens": int(bucket["output_tokens"]),
                    "usd": bucket["usd"],
                }
            )
        return result

    async def reset(self, scope: str | None = None) -> None:
        """清 ledger；scope=None 清全部，scope=X 只清该 scope。"""
        async with self._lock:
            if scope is None:
                self._totals.clear()
            else:
                self._totals.pop(scope, None)
