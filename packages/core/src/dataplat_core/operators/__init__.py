"""dataplat_core.operators：Operator Registry + 内置算子。

导出：
    OperatorRegistry          — 模块级单例，注册 / 查找 Operator 实现类
    IdentityOperator          — 标杆 Operator（原样透传 + lineage_ops 追加）
    FilterOperator            — 按 min_chars 过滤行
    DedupOperator             — 按 text / source_blob 去重
    ScoreOperator             — 按 text_chars / alpha_ratio 打分
    ChunkerOperator           — 按 max_chars 切分（1→N 语义）
    ImageStripOperator        — 清空 images 字段（W2-3）
    ImageCaptionStubOperator  — 将 images 元数据拼占位符注入 text（W2-3）
    SnapshotTagOperator       — 给行打 source_snapshot 标签（W2-4）
    SnapshotSampleOperator    — 基于 sha256 确定性哈希做按权重抽样（W2-4）
    EvalGenOperator           — 调 LLM 生成多选题写入 stats.eval_items（W4-8）
"""

from dataplat_core.operators.chunker import ChunkerOperator
from dataplat_core.operators.dedup import DedupOperator
from dataplat_core.operators.eval_gen import EvalGenOperator
from dataplat_core.operators.filter import FilterOperator
from dataplat_core.operators.identity import IdentityOperator
from dataplat_core.operators.image_caption_stub import ImageCaptionStubOperator
from dataplat_core.operators.image_strip import ImageStripOperator
from dataplat_core.operators.registry import OperatorRegistry
from dataplat_core.operators.score import ScoreOperator
from dataplat_core.operators.snapshot_sample import SnapshotSampleOperator
from dataplat_core.operators.snapshot_tag import SnapshotTagOperator

__all__ = [
    "OperatorRegistry",
    "IdentityOperator",
    "FilterOperator",
    "DedupOperator",
    "ScoreOperator",
    "ChunkerOperator",
    "ImageStripOperator",
    "ImageCaptionStubOperator",
    "SnapshotTagOperator",
    "SnapshotSampleOperator",
    "EvalGenOperator",
]

# 模块级自动注册 10 个内置算子；try/except 防止模块重复 import 时重复注册。
for _name, _cls in [
    ("identity", IdentityOperator),
    ("filter", FilterOperator),
    ("dedup", DedupOperator),
    ("score", ScoreOperator),
    ("chunker", ChunkerOperator),
    ("image_strip", ImageStripOperator),
    ("image_caption_stub", ImageCaptionStubOperator),
    ("snapshot_tag", SnapshotTagOperator),
    ("snapshot_sample", SnapshotSampleOperator),
    ("eval_gen", EvalGenOperator),
]:
    try:
        OperatorRegistry.register(_name, _cls)
    except ValueError:
        pass  # 已注册（模块重复 import 场景）
