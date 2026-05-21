"""CostController：per-scope budget + ledger 组合。

get_cost_controller()：进程内单例（@lru_cache，与 get_llm_gateway 同模式）。
reset_cost_controller()：测试辅助，清单例。

并发保护：check + record 均 await asyncio.Lock，防止两路 caller 并发预检都通过
后 record 后超额（竞态窗口约 100 ms，LLM call 本身就需这么久）。
"""

from __future__ import annotations

from functools import lru_cache

from dataplat_core.cost import BudgetExceeded, CostLedger, CostLedgerEntry

import asyncio


class CostController:
    """组合 CostLedger + per-scope budget dict。

    接口：
    - set_budget(scope, limit_usd)
    - get_budget(scope) → float | None
    - clear_budget(scope)
    - async check(scope, projected_usd) — 超额 raise BudgetExceeded
    - async record(scope, entry) — 调 ledger.record
    - total_usd(scope) → float
    - breakdown(scope) → list[dict]
    - async reset(scope)
    """

    def __init__(self) -> None:
        self._ledger = CostLedger()
        self._budgets: dict[str, float] = {}
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Budget management
    # ------------------------------------------------------------------

    def set_budget(self, scope: str, limit_usd: float) -> None:
        self._budgets[scope] = limit_usd

    def get_budget(self, scope: str) -> float | None:
        return self._budgets.get(scope)

    def clear_budget(self, scope: str) -> None:
        self._budgets.pop(scope, None)

    # ------------------------------------------------------------------
    # Core async ops (lock guards check + record atomicity)
    # ------------------------------------------------------------------

    async def check(self, scope: str, projected_usd: float) -> None:
        """预检：(current + projected) > limit → raise BudgetExceeded。

        None limit = 无限制；0.0 limit = 已超（任何正 projected 均 raise）。
        """
        limit = self._budgets.get(scope)
        if limit is None:
            return  # 无预算限制

        async with self._lock:
            current = self._ledger.total_usd(scope)
            if current + projected_usd > limit:
                raise BudgetExceeded(
                    scope=scope,
                    current_usd=current,
                    limit_usd=limit,
                )

    async def record(self, scope: str, entry: CostLedgerEntry) -> None:
        """记账（通过 ledger，也在锁内保证 check→record 原子性）。"""
        async with self._lock:
            await self._ledger.record(entry)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def total_usd(self, scope: str) -> float:
        return self._ledger.total_usd(scope)

    def breakdown(self, scope: str) -> list[dict]:
        return self._ledger.breakdown(scope)

    async def reset(self, scope: str) -> None:
        """清 ledger scope + budget（供 DELETE /llm-budget 用）。"""
        self.clear_budget(scope)
        await self._ledger.reset(scope)


# ---------------------------------------------------------------------------
# Singleton helpers（与 get_llm_gateway 同模式）
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_cost_controller() -> CostController:
    """进程内单例；测试用 reset_cost_controller() 清掉。"""
    return CostController()


def reset_cost_controller() -> None:
    """测试辅助：清掉单例，下次 get_cost_controller() 重新构造。"""
    get_cost_controller.cache_clear()
