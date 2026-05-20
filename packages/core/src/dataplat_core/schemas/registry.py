"""SchemaRegistry：模块级单例，管理 Silver/Gold row schema 的注册与查找。

用法：
    from dataplat_core.schemas.registry import SchemaRegistry, SchemaEntry

    SchemaRegistry.register("silver-text-v1", SilverRow, "silver")
    entry = SchemaRegistry.get("silver-text-v1")
    ids = SchemaRegistry.list_ids()
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from dataplat_core.domain.repository import Layer

_REGISTRY: dict[str, "SchemaEntry"] = {}


class SchemaEntry(BaseModel):
    """一条 schema 注册记录。"""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    schema_id: str
    row_cls: type[BaseModel]
    layer: Layer


class SchemaRegistry:
    """Schema 注册中心（模块级单例，无需实例化）。"""

    @staticmethod
    def register(schema_id: str, row_cls: type[BaseModel], layer: Layer) -> None:
        """注册一个 row schema。

        Args:
            schema_id: schema 唯一 ID（如 "silver-text-v1"）。
            row_cls:   Pydantic BaseModel 子类，代表一行数据的 schema。
            layer:     该 schema 所属 Layer（"silver" / "gold"）。

        Raises:
            ValueError: schema_id 已注册（防止静默覆盖）。
        """
        if schema_id in _REGISTRY:
            raise ValueError(
                f"Schema '{schema_id}' is already registered. "
                "已注册的 schema_id 不能重复注册。"
            )
        _REGISTRY[schema_id] = SchemaEntry(
            schema_id=schema_id,
            row_cls=row_cls,
            layer=layer,
        )

    @staticmethod
    def get(schema_id: str) -> SchemaEntry:
        """按 schema_id 查找已注册的 SchemaEntry。

        Raises:
            KeyError: schema_id 未注册。
        """
        if schema_id not in _REGISTRY:
            raise KeyError(
                f"Schema '{schema_id}' is not registered. "
                f"已注册的 schema_id: {list(_REGISTRY.keys())}"
            )
        return _REGISTRY[schema_id]

    @staticmethod
    def list_ids() -> list[str]:
        """返回当前已注册的所有 schema_id 列表（顺序不定）。"""
        return list(_REGISTRY.keys())

    @staticmethod
    def is_registered(schema_id: str) -> bool:
        """判断 schema_id 是否已注册。"""
        return schema_id in _REGISTRY
