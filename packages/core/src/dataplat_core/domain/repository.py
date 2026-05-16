"""Repository 与 Layer / Visibility / 分层 Subtype Literal。

按 .harness/design.md §2.2 定义。三层 Subtype 拆为 Literal 子类型，
union 成 `Subtype`，让 Pydantic 在 Repository 构造时严格校验。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Layer = Literal["bronze", "silver", "gold"]

Visibility = Literal["private", "internal", "public"]

BronzeSubtype = Literal[
    "pdf",
    "pdf-collection",
    "webpage",
    "webpage-collection",
    "book",
    "image-set",
]

SilverSubtype = Literal[
    "text-corpus",
    "qa-records",
    "dialog-corpus",
    "image-text-pairs",
]

GoldSubtype = Literal[
    "cpt",
    "sft",
    "dpo",
    "rlhf-pref",
    "eval",
]

Subtype = BronzeSubtype | SilverSubtype | GoldSubtype


class Repository(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    id: str
    owner: str
    name: str
    layer: Layer
    subtype: Subtype
    visibility: Visibility = "private"
    card_path: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    description: str | None = Field(
        default=None,
        description="可选简介；详细 card 走 card_path 指向的 Markdown",
    )
