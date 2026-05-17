"""FakeLLMProvider：deterministic 测试桩（CI 默认 provider）。

同 LLMRequest（model_id + messages + sampling）→ 同 LLMResponse.text。
模板：`FAKE[{model_id}]: {first_user_message[:80]}`。
"""

from __future__ import annotations

from dataplat_core.protocols.llm import LLMRequest, LLMResponse


class FakeLLMProvider:
    """无外部依赖；不连任何 API。"""

    async def call(self, req: LLMRequest) -> LLMResponse:
        first_user = next(
            (m.content for m in req.messages if m.role == "user"),
            req.messages[0].content if req.messages else "",
        )
        text = f"FAKE[{req.model_id}]: {first_user[:80]}"
        return LLMResponse(
            text=text,
            model_id=req.model_id,
            input_tokens=sum(len(m.content) for m in req.messages),
            output_tokens=len(text),
            raw={"provider": "fake"},
        )
