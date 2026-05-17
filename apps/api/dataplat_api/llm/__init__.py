"""LLM Gateway 子模块（design.md §4.5 / §11.2）。

集中所有 provider / cache / retry / 单例。processor 通过 ctx.llm.call(req) 调用。
"""

from dataplat_api.llm.factory import get_llm_gateway
from dataplat_api.llm.gateway import LLMGateway

__all__ = ["LLMGateway", "get_llm_gateway"]
