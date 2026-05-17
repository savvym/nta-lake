"""get_llm_gateway：基于 env 的进程内单例。

env `DATAPLAT_LLM_PROVIDER` ∈ {`anthropic`, `fake`}；缺省 `fake`（CI/dev
默认 deterministic 不消耗 API 配额）。
"""

from __future__ import annotations

import os
from functools import lru_cache

from dataplat_core.protocols.llm import LLMClient

from dataplat_api.jobs.redis_client import get_redis
from dataplat_api.llm.cache import RedisLLMCache
from dataplat_api.llm.gateway import LLMGateway
from dataplat_api.llm.providers.anthropic import AnthropicProvider
from dataplat_api.llm.providers.fake import FakeLLMProvider


def _build_provider() -> LLMClient:
    name = os.environ.get("DATAPLAT_LLM_PROVIDER", "fake").lower()
    if name == "anthropic":
        return AnthropicProvider()
    return FakeLLMProvider()


@lru_cache(maxsize=1)
def get_llm_gateway() -> LLMGateway:
    provider = _build_provider()
    try:
        cache: RedisLLMCache | None = RedisLLMCache(get_redis())
    except Exception:
        cache = None
    return LLMGateway(provider=provider, cache=cache)


def reset_llm_gateway() -> None:
    """测试辅助：清掉单例，下次 get_llm_gateway() 重新构造。"""

    get_llm_gateway.cache_clear()
