"""commits 表：内嵌 lineage_json JSONB。"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dataplat_api.models.base import Base
from dataplat_api.models.tree import TreeORM


class CommitORM(Base):
    __tablename__ = "commits"

    hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    repo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tree_hash: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("trees.hash", ondelete="RESTRICT"),
        nullable=False,
    )
    parents: Mapped[list[str]] = mapped_column(
        ARRAY(String(64)),
        nullable=False,
        default=list,
    )
    author_id: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    message: Mapped[str | None] = mapped_column(nullable=True)
    lineage_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    tree: Mapped[TreeORM] = relationship(lazy="select")
