"""Processor Protocol：上游 Repository@version → 下游 Repository@new_version。

按 .harness/design.md §4.2。涵盖纯函数式 / 结构化抽取 / LLM 式 / Agentic /
人在回路 五大类 processor。
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from dataplat_core.protocols.runcontext import RunContext


class RepoView(Protocol):
    """processor 看到的上游 Repository 视图。只读。"""

    @property
    def repo_id(self) -> str: ...

    @property
    def commit_hash(self) -> str: ...

    def open(self, path: str) -> Any:
        """以二进制流形式打开 commit tree 内的某条 path。"""
        ...

    def iter_records(self) -> Iterable[dict[str, Any]]:
        """schema-driven 上游（Silver/Gold）支持；Bronze 可不实现。"""
        ...


class RepoSelector(BaseModel):
    """processor.accepts 用：声明能处理什么样的上游。"""

    model_config = ConfigDict(frozen=False, extra="forbid")

    layer: str | None = None
    subtype: str | None = None
    schema_id: str | None = None


class RepoSpec(BaseModel):
    """processor.produces 用：声明产出什么样的下游。"""

    model_config = ConfigDict(frozen=False, extra="forbid")

    layer: str
    subtype: str
    schema_id: str | None = None


class ProcessResult(BaseModel):
    """processor.run() 的产出元信息。"""

    model_config = ConfigDict(frozen=False, extra="forbid")

    record_count: int = 0
    file_count: int = 0
    bytes_written: int = 0
    notes: str | None = None


@runtime_checkable
class Processor(Protocol):
    """处理器协议。"""

    name: str
    version: str
    config_schema: dict[str, Any]
    accepts: list[RepoSelector]
    produces: RepoSpec

    def run(
        self,
        inputs: list[RepoView],
        config: dict[str, Any],
        workspace: Path,
        ctx: RunContext,
    ) -> ProcessResult: ...
