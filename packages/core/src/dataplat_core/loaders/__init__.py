"""dataplat_core.loaders：Loader Registry 骨架。

导出：
    LoaderRegistry  — 模块级单例，注册 / 查找 Loader 实现类
"""

from dataplat_core.loaders.registry import LoaderRegistry

__all__ = [
    "LoaderRegistry",
]
