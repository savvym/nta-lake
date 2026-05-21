"""LLMGateway：装饰一个 provider，加 cache + 指数退避 retry + cost budget。

执行流程：
1. cache.get(req) 命中 → 直接返（不计费；cache hit 视为零成本）
2. **预检**：若 cost 非 None，用 req.max_tokens 作上界估算 projected_usd
   → await cost.check(scope, projected_usd) → 超额 raise BudgetExceeded（不走 retry）
3. provider.call(req) 异常 → 指数退避（base_delay * 2**attempt）；max_retries+1 次后 raise
4. 成功 → **后置 record**：用 resp 真实 tokens → await cost.record(scope, entry)
5. cache.set(req, resp)（最佳努力，失败不阻塞 caller）→ 返
"""

from __future__ import annotations

import asyncio
import logging

from dataplat_core.cost import (
    CostLedgerEntry,
    CostRate,
    DEFAULT_RATES,
    _DEFAULT_RATE,
    compute_cost,
)
from dataplat_core.protocols.llm import LLMClient, LLMRequest, LLMResponse

from dataplat_api.llm.cache import RedisLLMCache

_logger = logging.getLogger("dataplat.llm")


class LLMGateway:
    """统一 LLM 调用入口。"""

    def __init__(
        self,
        provider: LLMClient,
        cache: RedisLLMCache | None = None,
        max_retries: int = 3,
        base_delay: float = 0.1,
        cost: "CostController | None" = None,  # type: ignore[name-defined]  # noqa: F821
        rates: dict[str, CostRate] | None = None,
        scope: str = "default",
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._cost = cost
        self._rates = rates if rates is not None else DEFAULT_RATES
        self._scope = scope

    def _get_rate(self, model_id: str) -> CostRate:
        return self._rates.get(model_id, _DEFAULT_RATE)

    async def call(self, req: LLMRequest) -> LLMResponse:
        # Step 1: cache hit → return immediately (no cost)
        if self._cache is not None:
            try:
                cached = await self._cache.get(req)
            except Exception:
                cached = None
                _logger.warning("LLM cache get failed; skipping", exc_info=True)
            if cached is not None:
                return cached

        # Step 2: pre-check budget (before retry loop; BudgetExceeded is deterministic)
        if self._cost is not None:
            rate = self._get_rate(req.model_id)
            projected = compute_cost(rate, req.max_tokens, req.max_tokens)
            await self._cost.check(self._scope, projected)

        # Step 3: provider call with retry
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = await self._provider.call(req)

                # Step 4: post-record with real tokens
                if self._cost is not None:
                    rate = self._get_rate(req.model_id)
                    usd = compute_cost(
                        rate,
                        getattr(resp, "input_tokens", 0),
                        getattr(resp, "output_tokens", 0),
                    )
                    entry = CostLedgerEntry(
                        model_id=resp.model_id,
                        input_tokens=getattr(resp, "input_tokens", 0),
                        output_tokens=getattr(resp, "output_tokens", 0),
                        usd=usd,
                        scope=self._scope,
                    )
                    await self._cost.record(self._scope, entry)

                # Step 5: cache set
                if self._cache is not None:
                    try:
                        await self._cache.set(req, resp)
                    except Exception:
                        _logger.warning("LLM cache set failed; ignored", exc_info=True)
                return resp
            except Exception as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    break
                delay = self._base_delay * (2**attempt)
                _logger.warning(
                    "LLM provider call failed (attempt %d/%d); retry in %.2fs",
                    attempt + 1,
                    self._max_retries + 1,
                    delay,
                )
                await asyncio.sleep(delay)
        assert last_exc is not None
        raise last_exc


# Avoid circular import: CostController lives in dataplat_api.llm.cost
# TYPE_CHECKING import only
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dataplat_api.llm.cost import CostController
