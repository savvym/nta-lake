"""dataplat 内置 Processor 集合。

module import 时自动注册所有内置 processor 到 `get_processor_registry()`。
"""

from dataplat_api.processors.llm_qa_gen import LLMQAGenProcessor
from dataplat_api.processors.llm_summarize import LLMSummarizeProcessor
from dataplat_api.processors.markdown_normalize import MarkdownNormalizeProcessor
from dataplat_api.processors.pdf_mineru import PdfMineruProcessor
from dataplat_api.runner.processor_registry import get_processor_registry

_registry = get_processor_registry()
_registry.register(MarkdownNormalizeProcessor())
_registry.register(LLMSummarizeProcessor())
_registry.register(LLMQAGenProcessor())
_registry.register(PdfMineruProcessor())

__all__ = [
    "LLMQAGenProcessor",
    "LLMSummarizeProcessor",
    "MarkdownNormalizeProcessor",
    "PdfMineruProcessor",
]
