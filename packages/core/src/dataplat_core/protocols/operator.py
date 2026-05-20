"""Operator Protocol：Silver row → Silver rows 的行级变换协议。

按 .harness/design.md § 北极星：Operator 是 Silver 层的行级算子，
run() 返 list[SilverRow] 覆盖三种语义：
  1→0  过滤（drop）
  1→1  变换（map）
  1→N  切分（split，如 chunker）

具体 Operator 实现见 packages/core/src/dataplat_core/operators/（registry + W2-1 suite）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.runcontext import RunContext


class OperatorSpec(BaseModel):
    """Operator 元数据描述。

    - `name`：全局唯一算子名（与 OperatorRegistry key 保持一致）。
    - `version`：语义版本字符串，用于 lineage_ops 追踪。
    - `config_schema`：JSON Schema dict（可为空 dict 表示无配置项）。
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    config_schema: dict[str, Any] = {}


@runtime_checkable
class Operator(Protocol):
    """行级算子协议。

    实现者须声明 name / version / spec 三个属性，并实现 run()。
    run() 必须返回新 row 列表，**不得原地修改输入 row**（lineage_ops 不变性）。
    """

    name: str
    version: str
    spec: OperatorSpec

    def run(
        self,
        row: SilverRow,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> list[SilverRow]: ...
