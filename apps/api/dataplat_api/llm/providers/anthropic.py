"""AnthropicProvider：包装 anthropic.AsyncAnthropic SDK。

构造**惰性**：__init__ 只存 api_key，不连 API；call 时才创建 AsyncAnthropic
客户端。这样无 ANTHROPIC_API_KEY 也能 import 类（满足 spec AC-2 类存在要求）。
"""

from __future__ import annotations

import os

from dataplat_core.protocols.llm import LLMRequest, LLMResponse


class AnthropicProvider:
    """Anthropic Claude provider。"""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    async def call(self, req: LLMRequest) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError(
                "AnthropicProvider 需要 ANTHROPIC_API_KEY env 或显式 api_key 参数"
            )
        from typing import Any, cast

        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        messages = cast(
            Any, [{"role": m.role, "content": m.content} for m in req.messages]
        )
        if req.temperature is not None:
            resp = await client.messages.create(
                model=req.model_id,
                max_tokens=req.max_tokens,
                messages=messages,
                temperature=req.temperature,
            )
        else:
            resp = await client.messages.create(
                model=req.model_id,
                max_tokens=req.max_tokens,
                messages=messages,
            )

        text = ""
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                text += getattr(block, "text", "")

        return LLMResponse(
            text=text,
            model_id=req.model_id,
            input_tokens=getattr(resp.usage, "input_tokens", 0),
            output_tokens=getattr(resp.usage, "output_tokens", 0),
            raw={"provider": "anthropic", "stop_reason": str(resp.stop_reason or "")},
        )
