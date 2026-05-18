"""dataplat 内置 Source Adapter 集合。

module import 时自动把所有内置 adapter 注册到 `get_registry()`（spec AC-2 / AC-5）。
新 adapter 按下面模板补：import 类 + 一行 register。
"""

from dataplat_api.adapters.firecrawl_url import FirecrawlURLAdapter
from dataplat_api.adapters.raw_upload import RawFileUploadAdapter
from dataplat_api.runner import get_registry

_registry = get_registry()
_registry.register(RawFileUploadAdapter())
_registry.register(FirecrawlURLAdapter())

__all__ = ["FirecrawlURLAdapter", "RawFileUploadAdapter"]
