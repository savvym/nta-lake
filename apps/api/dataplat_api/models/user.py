"""users 表：MVP 认证（design.md §11.6）。

字段：
- id (UUID PK)
- username (str, unique, NOT NULL)
- email (str, unique, nullable)
- password_hash (str, nullable; NULL 表示 SSO 用户)
- role (str, NOT NULL, default 'user')
- is_active (bool, NOT NULL, default True)
- external_id (str, unique, nullable; 预留 SSO subject id)
- created_at / updated_at

Repository 级 ACL 留给 Phase 2。本变更只引入扁平 role（admin / user）。
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from dataplat_api.models.base import Base, TimestampMixin


class UserORM(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("external_id", name="uq_users_external_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
