"""LLMClient Protocol + LLMRequest / LLMResponse / LLMMessage 数据契约。

按 design.md §4.5 / §5.1 / §11.2。LLM Gateway 把所有 provider 统一在
此 Protocol 后面；processor 通过 `ctx.llm.call(req)` 调用。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class LLMMessage(BaseModel):
    """单条对话消息（role + content）。"""

    model_config = ConfigDict(extra="forbid")

    role: str
    content: str


class LLMRequest(BaseModel):
    """LLM 调用请求。

    缓存 key 算法：sha256(canonical_json(model_id, messages, max_tokens,
    temperature, seed))。`canonical_json` 用 `model_dump(mode="json")` +
    `json.dumps(sort_keys=True)`，保证跨进程稳定。
    """

    model_config = ConfigDict(extra="forbid")

    model_id: str
    messages: list[LLMMessage]
    max_tokens: int = 256
    temperature: float | None = None
    seed: int | None = None


class LLMResponse(BaseModel):
    """LLM 调用结果。"""

    model_config = ConfigDict(extra="forbid")

    text: str
    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    raw: dict[str, str] = Field(default_factory=dict)


@runtime_checkable
class LLMClient(Protocol):
    """统一 LLM 客户端协议。"""

    async def call(self, req: LLMRequest) -> LLMResponse: ...
