"""ORM 基类：DeclarativeBase + TimestampMixin。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 dataplat ORM 表的根基类。"""


class TimestampMixin:
    """给业务表加 created_at / updated_at（TIMESTAMP WITH TIME ZONE）。

    commits / blobs 的内容寻址表本身不可变，不需要 updated_at，所以不混入。
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
