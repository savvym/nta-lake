"""refs 表：(repo_id, name) → commit_hash 可变指针。"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from dataplat_api.models.base import Base, TimestampMixin


class RefORM(Base, TimestampMixin):
    __tablename__ = "refs"
    __table_args__ = (
        UniqueConstraint("repo_id", "name", name="uq_refs_repo_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    repo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(nullable=False)
    commit_hash: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("commits.hash", ondelete="RESTRICT"),
        nullable=False,
    )
