"""pytest 配置：module-scoped event loop，避免 asyncpg 跨用例清理时序冲突。

详见：
- https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncio-scoped-session
- pytest-asyncio v1+ 的 loop_scope。
"""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """所有 async test 用 module-scoped loop，避免 engine 重复打开/关闭。"""
    for item in items:
        if "asyncio" in (m.name for m in item.iter_markers()):
            item.add_marker(pytest.mark.asyncio(loop_scope="module"))
