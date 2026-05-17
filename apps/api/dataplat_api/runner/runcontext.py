"""StandardRunContext：实现 RunContext Protocol 的最小可用 dataclass（spec AC-3）。

MVP 只保证 logger 真实可用；metrics / secrets / cancel_event / llm 占位 None，
adapter 不应依赖。后续 follow-up（LLM Gateway / secret-management / job-cancel）
分别填实质实现。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any


@dataclass
class StandardRunContext:
    """RunContext Protocol 的最小实现。

    runtime_checkable 通过；结构等价于 Protocol 声明的 5 个 @property
    （logger / metrics / secrets / cancel_event / llm）。
    blob_store 是 processor-framework 引入的额外字段（processor 用 ctx.blob_store
    上传新 blob；不在 RunContext Protocol 上但 processor 实现可访问）。
    """

    logger: logging.Logger
    metrics: Any = None
    secrets: Any = None
    cancel_event: Any = None
    llm: Any = None
    blob_store: Any = None
