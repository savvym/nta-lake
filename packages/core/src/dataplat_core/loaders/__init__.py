"""dataplat_core.loaders：Loader Registry + 内置 Loader 注册。"""

from dataplat_core.loaders.docx import DocxLoader
from dataplat_core.loaders.html_md import HtmlMdLoader
from dataplat_core.loaders.pptx import PptxLoader
from dataplat_core.loaders.registry import LoaderRegistry

for _name, _cls in (("html-md", HtmlMdLoader), ("docx", DocxLoader), ("pptx", PptxLoader)):
    try:
        LoaderRegistry.register(_name, _cls)
    except ValueError:
        pass

__all__ = [
    "DocxLoader",
    "HtmlMdLoader",
    "LoaderRegistry",
    "PptxLoader",
]
