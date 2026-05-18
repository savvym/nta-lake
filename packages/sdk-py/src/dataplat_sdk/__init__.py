"""dataplat Python SDK + CLI（用户侧）。

`Client(base_url, ...)` 是同步 HTTP 客户端；`cli.app` 是 Typer 命令行 entry
（PATH 上的 `dataplat` 命令）。设计文档：design.md §7.2 / §7.3。
"""

from dataplat_sdk.client import Client

__all__ = ["Client"]
__version__ = "0.1.0"
