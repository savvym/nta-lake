"""dataplat Adapter Runner 模块。

暴露 `AdapterRegistry` + `get_registry()` 单例（用于注册 SourceAdapter）+
`StandardRunContext` + `AdapterRunner`（spec adapter-framework-20260517）。
"""

from dataplat_api.runner.adapter_runner import AdapterRunner
from dataplat_api.runner.registry import AdapterRegistry, get_registry
from dataplat_api.runner.runcontext import StandardRunContext

__all__ = [
    "AdapterRegistry",
    "AdapterRunner",
    "StandardRunContext",
    "get_registry",
]
