"""LLMGateway：装饰一个 provider，加 cache + 指数退避 retry。

执行流程：
1. cache.get(req) 命中 → 直接返
2. provider.call(req) 异常 → 指数退避（base_delay * 2**attempt）；max_retries+1 次后 raise
3. 成功 → cache.set(req, resp)（最佳努力，失败不阻塞 caller）→ 返
"""

from __future__ import annotations

import asyncio
import logging

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
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._max_retries = max_retries
        self._base_delay = base_delay

    async def call(self, req: LLMRequest) -> LLMResponse:
        if self._cache is not None:
            try:
                cached = await self._cache.get(req)
            except Exception:
                cached = None
                _logger.warning("LLM cache get failed; skipping", exc_info=True)
            if cached is not None:
                return cached

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = await self._provider.call(req)
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
