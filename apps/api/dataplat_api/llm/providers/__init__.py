"""LLM provider 实现集合。每个 provider 都实现 LLMClient Protocol。"""

from dataplat_api.llm.providers.anthropic import AnthropicProvider
from dataplat_api.llm.providers.fake import FakeLLMProvider

__all__ = ["AnthropicProvider", "FakeLLMProvider"]
