"""dataplat_core.loaders：Loader Registry + 内置 Loader 注册。"""

from dataplat_core.loaders.html_md import HtmlMdLoader
from dataplat_core.loaders.registry import LoaderRegistry

try:
    LoaderRegistry.register("html-md", HtmlMdLoader)
except ValueError:
    pass

__all__ = [
    "HtmlMdLoader",
    "LoaderRegistry",
]
