"""dataplat_core.operators：Operator Registry + 内置算子。

导出：
    OperatorRegistry  — 模块级单例，注册 / 查找 Operator 实现类
    IdentityOperator  — 标杆 Operator（原样透传 + lineage_ops 追加）
"""

from dataplat_core.operators.identity import IdentityOperator
from dataplat_core.operators.registry import OperatorRegistry

__all__ = [
    "OperatorRegistry",
    "IdentityOperator",
]
