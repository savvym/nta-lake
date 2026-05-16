"""dataplat 领域模型（Pydantic v2）。

按 .harness/design.md §2 / §4.4 落地：Repository / Commit / Tree / TreeEntry / BlobRef /
Ref / Lineage / ProducedBy / InputRef，以及 SHA256 类型别名与 Layer / Visibility /
分层 Subtype Literal。

入口模块只暴露最常用的类型，避免下游被迫记长 import 路径。
"""

from dataplat_core.domain.blob import BlobRef
from dataplat_core.domain.commit import Commit
from dataplat_core.domain.lineage import InputRef, Lineage, ProducedBy
from dataplat_core.domain.refs import Ref
from dataplat_core.domain.repository import (
    BronzeSubtype,
    GoldSubtype,
    Layer,
    Repository,
    SilverSubtype,
    Subtype,
    Visibility,
)
from dataplat_core.domain.tree import Tree, TreeEntry
from dataplat_core.domain.types import SHA256

__all__ = [
    "SHA256",
    "Layer",
    "Visibility",
    "BronzeSubtype",
    "SilverSubtype",
    "GoldSubtype",
    "Subtype",
    "Repository",
    "BlobRef",
    "Tree",
    "TreeEntry",
    "Ref",
    "Commit",
    "Lineage",
    "ProducedBy",
    "InputRef",
]
