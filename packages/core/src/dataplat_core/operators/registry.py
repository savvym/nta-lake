"""OperatorRegistry：模块级单例，管理 Operator 实现类的注册与查找。

用法：
    from dataplat_core.operators.registry import OperatorRegistry

    OperatorRegistry.register("identity", IdentityOperator)
    cls = OperatorRegistry.get("identity")
    names = OperatorRegistry.list_names()
"""

from __future__ import annotations

_REGISTRY: dict[str, type] = {}


class OperatorRegistry:
    """Operator 注册中心（模块级单例，无需实例化）。"""

    @staticmethod
    def register(name: str, cls: type) -> None:
        """注册一个 Operator 实现类。

        Args:
            name: 算子唯一名称（与 OperatorSpec.name 保持一致）。
            cls:  实现了 Operator Protocol 的类对象。

        Raises:
            ValueError: 名称已注册（防止静默覆盖）。
        """
        if name in _REGISTRY:
            raise ValueError(f"Operator '{name}' is already registered.")
        _REGISTRY[name] = cls

    @staticmethod
    def get(name: str) -> type:
        """按名称查找 Operator 类。

        Raises:
            KeyError: 名称未注册。
        """
        if name not in _REGISTRY:
            raise KeyError(f"Operator '{name}' is not registered.")
        return _REGISTRY[name]

    @staticmethod
    def list_names() -> list[str]:
        """返回当前已注册的所有算子名称列表（顺序不定）。"""
        return list(_REGISTRY.keys())
