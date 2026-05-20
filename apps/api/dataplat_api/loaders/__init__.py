"""dataplat 内置 Loader 集合。

module import 时自动注册所有内置 loader 到 LoaderRegistry。
"""

from dataplat_core.loaders import LoaderRegistry

from dataplat_api.loaders.pdf_mineru import PdfMineruLoader

LoaderRegistry.register("pdf-mineru", PdfMineruLoader)

__all__ = [
    "PdfMineruLoader",
]
