"""pipeline orchestrator tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-18 07:15:00

3 表：pipeline_runs / pipeline_node_runs / pipeline_cache（spec
pipeline-orchestrator-mvp-20260518 T-2，AC-4 / AC-8 支撑）。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pipeline_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("recipe_name", sa.String(255), nullable=False),
        sa.Column("recipe_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "status", sa.String(16), nullable=False, server_default="queued"
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_pipeline_runs_recipe_name", "pipeline_runs", ["recipe_name"]
    )
    op.create_index("ix_pipeline_runs_status", "pipeline_runs", ["status"])
    op.create_index(
        "ix_pipeline_runs_created_at", "pipeline_runs", ["created_at"]
    )

    op.create_table(
        "pipeline_node_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pipeline_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("node_id", sa.String(255), nullable=False),
        sa.Column("processor_name", sa.String(255), nullable=False),
        sa.Column("processor_version", sa.String(64), nullable=False),
        sa.Column("config_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "status", sa.String(16), nullable=False, server_default="pending"
        ),
        sa.Column(
            "cache_hit",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("output_commit_hash", sa.String(64), nullable=True),
        # v2 SHOULD #2：cache hit / miss 必写；
        # stage 4 SHOULD #1：error 兜底路径解析未完成时允许 NULL
        sa.Column("input_commits_json", postgresql.JSONB(), nullable=True),
        sa.Column("cache_key", sa.String(64), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_pipeline_node_runs_run_id", "pipeline_node_runs", ["run_id"]
    )
    op.create_index(
        "ix_pipeline_node_runs_cache_key",
        "pipeline_node_runs",
        ["cache_key"],
    )

    op.create_table(
        "pipeline_cache",
        sa.Column("cache_key", sa.String(64), primary_key=True),
        sa.Column(
            "output_commit_hash",
            sa.String(64),
            sa.ForeignKey("commits.hash", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("pipeline_cache")
    op.drop_index(
        "ix_pipeline_node_runs_cache_key", table_name="pipeline_node_runs"
    )
    op.drop_index(
        "ix_pipeline_node_runs_run_id", table_name="pipeline_node_runs"
    )
    op.drop_table("pipeline_node_runs")
    op.drop_index("ix_pipeline_runs_created_at", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_status", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_recipe_name", table_name="pipeline_runs")
    op.drop_table("pipeline_runs")
