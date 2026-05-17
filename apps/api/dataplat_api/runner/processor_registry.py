"""ProcessorRegistry：按 (name, version) 索引内置 Processor（spec processor-framework AC-2）。

与 AdapterRegistry 同模式；幂等 register。
"""

from __future__ import annotations

import logging

from dataplat_core.protocols.processor import Processor

_logger = logging.getLogger(__name__)


class ProcessorRegistry:
    def __init__(self) -> None:
        self._processors: dict[tuple[str, str], Processor] = {}

    def register(self, processor: Processor) -> None:
        key = (processor.name, processor.version)
        if key in self._processors:
            _logger.warning(
                "ProcessorRegistry: %s@%s 已注册，跳过", processor.name, processor.version
            )
            return
        self._processors[key] = processor

    def get(self, name: str, version: str) -> Processor | None:
        return self._processors.get((name, version))

    def list_all(self) -> list[tuple[str, str]]:
        return sorted(self._processors.keys())


_registry = ProcessorRegistry()


def get_processor_registry() -> ProcessorRegistry:
    return _registry
