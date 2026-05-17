"""dataplat 插件协议。

入口模块只暴露最常用的 Protocol / 数据类。具体定义放在子模块；不让本文件
import 整个 `dataplat_core.domain`，避免循环 import（spec §风险表）。
"""

from dataplat_core.protocols.adapter import IngestResult, SourceAdapter
from dataplat_core.protocols.processor import (
    Processor,
    ProcessResult,
    RepoSelector,
    RepoSpec,
    RepoView,
)
from dataplat_core.protocols.runcontext import RunContext
from dataplat_core.protocols.storage import BlobPutResult, BlobStore

__all__ = [
    "SourceAdapter",
    "IngestResult",
    "Processor",
    "ProcessResult",
    "RepoView",
    "RepoSelector",
    "RepoSpec",
    "RunContext",
    "BlobStore",
    "BlobPutResult",
]
