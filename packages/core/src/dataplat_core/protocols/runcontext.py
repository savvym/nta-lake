"""RunContext：平台注入到 plugin 运行环境的对象。

按 .harness/design.md §4.1 / §4.5：暴露 logger / metrics / secrets / cancel /
llm 五类能力。当前是 Protocol（接口契约）；具体实现由 worker / api 子模块
提供，plugin 不应直接 import 实现。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RunContext(Protocol):
    """plugin 运行时上下文。"""

    @property
    def logger(self) -> Any: ...

    @property
    def metrics(self) -> Any: ...

    @property
    def secrets(self) -> Any: ...

    @property
    def cancel_event(self) -> Any:
        """asyncio.Event 或等价信号；plugin 长循环应周期性 check。"""
        ...

    @property
    def llm(self) -> Any:
        """LLM Gateway 客户端句柄；plugin 通过 ctx.llm.call(...) 调用。

        具体接口由后续 LLM Gateway 变更定义；当前仅占位 attribute。
        """
        ...
