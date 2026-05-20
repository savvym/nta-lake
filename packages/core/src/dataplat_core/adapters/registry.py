"""AdapterRegistry：内置 Source Adapter 集合。

存 SourceAdapter 实例（与 LoaderRegistry/OperatorRegistry 不同：那两个存 class）。
"""

from __future__ import annotations

from dataplat_core.protocols.adapter import SourceAdapter


class AdapterRegistry:
    """内置 source adapter registry。"""

    def __init__(self) -> None:
        self._registry: dict[str, SourceAdapter] = {}

    def register(self, adapter: SourceAdapter) -> None:
        name = adapter.name
        if name in self._registry:
            raise ValueError(f"adapter '{name}' already registered")
        self._registry[name] = adapter

    def get(self, name: str) -> SourceAdapter:
        if name not in self._registry:
            raise KeyError(name)
        return self._registry[name]

    def list_names(self) -> list[str]:
        return sorted(self._registry.keys())


_default = AdapterRegistry()


def get_default() -> AdapterRegistry:
    return _default
