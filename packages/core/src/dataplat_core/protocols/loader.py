"""Loader Protocol：把 Bronze blob 解析为 SilverRow 列表。

按 .harness/design.md § 北极星：Loader 是 Bronze→Silver 层的行级解析器，
与 Operator（row→row）共同构成 Silver 层算子链的两端。

具体 Loader 实现见 plugins/loader-*（如 W1-4 pdf-mineru loader）。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from dataplat_core.domain.types import SHA256
from dataplat_core.protocols.runcontext import RunContext


class SilverRow(BaseModel):
    """Silver 层的一行数据。Loader 产出；Operator 消费 + 产出。

    - `text`：主文本内容，必填。
    - `images`：附属图片列表（每项为任意 dict，具体 schema 由 W1-3 定型）。
    - `source_ref`：溯源信息，至少含 blob_sha + path（由上游 Loader 填写）。
    - `stats`：token 数、字符数等统计；stats-first 原则，尽量在 Loader 层填充。
    - `lineage_ops`：已执行的 Operator 链，每项 `{"op": name, "version": ver, ...}`；
      Operator.run 必须追加而非原地修改，保证行级血缘可回溯。
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    text: str
    images: list[dict] = []
    source_ref: dict
    stats: dict = {}
    lineage_ops: list[dict] = []


class LoadResult(BaseModel):
    """Loader.load() 的产出汇总。"""

    model_config = ConfigDict(frozen=False, extra="forbid")

    rows: list[SilverRow]
    total_count: int
    notes: str | None = None


@runtime_checkable
class Loader(Protocol):
    """Bronze blob → Silver rows 解析协议。

    实现者须声明 name / version / input_subtype / output_schema_id 四个属性，
    并实现 load()。
    """

    name: str
    version: str
    input_subtype: str
    output_schema_id: str | None

    def load(
        self,
        bronze_blob_sha: SHA256,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> LoadResult: ...
