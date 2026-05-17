"""AdapterRegistry：按 (name, version) 索引内置 SourceAdapter（spec AC-2）。

MVP：module load 时静态注册（adapters/__init__.py import 触发 register()）；
后续 follow-up 可演进为 Python entrypoints 发现机制（L2 plugin）。
"""

from __future__ import annotations

import logging

from dataplat_core.protocols.adapter import SourceAdapter

_logger = logging.getLogger(__name__)


class AdapterRegistry:
    """无 state（单例由 module-level _registry 持有）。

    register 幂等：重复 key 记 warning 跳过，不 raise。
    """

    def __init__(self) -> None:
        self._adapters: dict[tuple[str, str], SourceAdapter] = {}

    def register(self, adapter: SourceAdapter) -> None:
        key = (adapter.name, adapter.version)
        if key in self._adapters:
            _logger.warning(
                "AdapterRegistry: %s@%s 已注册，跳过重复 register",
                adapter.name,
                adapter.version,
            )
            return
        self._adapters[key] = adapter

    def get(self, name: str, version: str) -> SourceAdapter | None:
        return self._adapters.get((name, version))

    def list_all(self) -> list[tuple[str, str]]:
        return sorted(self._adapters.keys())


_registry = AdapterRegistry()


def get_registry() -> AdapterRegistry:
    return _registry
