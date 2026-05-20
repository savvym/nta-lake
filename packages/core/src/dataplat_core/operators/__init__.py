"""dataplat_core.operators：Operator Registry + 内置算子。

导出：
    OperatorRegistry  — 模块级单例，注册 / 查找 Operator 实现类
    IdentityOperator  — 标杆 Operator（原样透传 + lineage_ops 追加）
    FilterOperator    — 按 min_chars 过滤行
    DedupOperator     — 按 text / source_blob 去重
    ScoreOperator     — 按 text_chars / alpha_ratio 打分
"""

from dataplat_core.operators.dedup import DedupOperator
from dataplat_core.operators.filter import FilterOperator
from dataplat_core.operators.identity import IdentityOperator
from dataplat_core.operators.registry import OperatorRegistry
from dataplat_core.operators.score import ScoreOperator

__all__ = [
    "OperatorRegistry",
    "IdentityOperator",
    "FilterOperator",
    "DedupOperator",
    "ScoreOperator",
]

# 模块级自动注册 4 个内置算子；try/except 防止模块重复 import 时重复注册。
for _name, _cls in [
    ("identity", IdentityOperator),
    ("filter", FilterOperator),
    ("dedup", DedupOperator),
    ("score", ScoreOperator),
]:
    try:
        OperatorRegistry.register(_name, _cls)
    except ValueError:
        pass  # 已注册（模块重复 import 场景）
