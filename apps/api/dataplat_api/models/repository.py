"""repositories 表 ORM。"""

from __future__ import annotations

import uuid

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from dataplat_api.models.base import Base, TimestampMixin


class RepositoryORM(Base, TimestampMixin):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint("owner", "name", name="uq_repositories_owner_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    owner: Mapped[str] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    layer: Mapped[str] = mapped_column(nullable=False, index=True)
    subtype: Mapped[str] = mapped_column(nullable=False)
    visibility: Mapped[str] = mapped_column(nullable=False, default="private")
    card_path: Mapped[str | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(nullable=True)
    schema_id: Mapped[str | None] = mapped_column(nullable=True)
    row_format: Mapped[str | None] = mapped_column(nullable=True)
