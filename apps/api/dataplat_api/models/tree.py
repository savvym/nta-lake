"""trees + tree_entries 表（拆两表，不用 JSONB；spec AC-9）。"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from dataplat_api.models.base import Base


class TreeORM(Base):
    __tablename__ = "trees"

    hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    repo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class TreeEntryORM(Base):
    __tablename__ = "tree_entries"
    __table_args__ = (
        UniqueConstraint("tree_hash", "name", name="uq_tree_entries_tree_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tree_hash: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("trees.hash", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    mode: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_type: Mapped[str] = mapped_column(String(8), nullable=False)
    target_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
