"""RedisLLMCache：LLM 响应缓存。

Key：`f"llm:{sha256(canonical_json(model_id, messages, max_tokens, temperature, seed))}"`
Value：LLMResponse.model_dump_json() 字符串
默认 TTL 1 天。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from dataplat_core.protocols.llm import LLMRequest, LLMResponse


def _canonical_key(req: LLMRequest) -> str:
    payload = {
        "model_id": req.model_id,
        "messages": [{"role": m.role, "content": m.content} for m in req.messages],
        "max_tokens": req.max_tokens,
        "temperature": req.temperature,
        "seed": req.seed,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return f"llm:{hashlib.sha256(blob).hexdigest()}"


class RedisLLMCache:
    """`redis.Redis`（同步客户端）背后的 LLM 响应缓存。"""

    def __init__(self, redis_client: Any, ttl_seconds: int = 86400) -> None:
        self._redis = redis_client
        self._ttl = ttl_seconds

    async def get(self, req: LLMRequest) -> LLMResponse | None:
        raw = self._redis.get(_canonical_key(req))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return LLMResponse.model_validate_json(raw)

    async def set(self, req: LLMRequest, resp: LLMResponse) -> None:
        self._redis.set(_canonical_key(req), resp.model_dump_json(), ex=self._ttl)
