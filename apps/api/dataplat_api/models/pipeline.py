"""Pipeline 编排 3 ORM（spec pipeline-orchestrator-mvp-20260518 T-2）。

- `pipeline_runs`：一次 recipe 执行的元数据
- `pipeline_node_runs`：每节点执行细节 + 审计字段（v2 SHOULD #2：input_commits_json + cache_key NOT NULL）
- `pipeline_cache`：(cache_key) → output_commit_hash 复用表

status 值域 queued|running|succeeded|failed（应用层约束；与 jobs 表同模式）。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dataplat_api.models.base import Base


class PipelineRunORM(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recipe_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    recipe_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="queued", index=True
    )
    error: Mapped[str | None] = mapped_column(nullable=True)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )


class PipelineNodeRunORM(Base):
    __tablename__ = "pipeline_node_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    processor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    processor_version: Mapped[str] = mapped_column(String(64), nullable=False)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    cache_hit: Mapped[bool] = mapped_column(nullable=False, default=False)
    output_commit_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # v2 SHOULD #2：cache hit / cache miss 必写两字段供审计；
    # v1→v2 stage 4 SHOULD #1：error 兜底路径解析未完成时允许 NULL（空串混淆 NOT NULL 索引语义）
    input_commits_json: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    cache_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    error: Mapped[str | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class PipelineCacheORM(Base):
    __tablename__ = "pipeline_cache"

    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    output_commit_hash: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("commits.hash", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
