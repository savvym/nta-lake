"""dataplat_core 内置 Source Adapter 集合。

import 时自动注册到 get_default() registry（idempotent，try/except ValueError）。
"""

from dataplat_core.adapters.raw_upload import RawFileUploadAdapter
from dataplat_core.adapters.registry import AdapterRegistry, get_default

_registry = get_default()

try:
    _registry.register(RawFileUploadAdapter())
except ValueError:
    pass

__all__ = ["AdapterRegistry", "RawFileUploadAdapter", "get_default"]
