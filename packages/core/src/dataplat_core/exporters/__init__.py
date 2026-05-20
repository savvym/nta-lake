"""exporters：silver / gold snapshot 派生格式输出器。

每个 exporter 是无注册中心的纯函数 / 类（与 adapters / loaders / operators 不同——
exporters 是 caller 显式调，没有 dispatcher）。
"""

from dataplat_core.exporters.hf_datasets import (
    HfDatasetExportResult,
    export_to_hf_datasets,
)

__all__ = ["HfDatasetExportResult", "export_to_hf_datasets"]
