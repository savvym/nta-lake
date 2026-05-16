"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-17 01:00:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("layer", sa.String(), nullable=False),
        sa.Column("subtype", sa.String(), nullable=False),
        sa.Column("visibility", sa.String(), nullable=False, server_default="private"),
        sa.Column("card_path", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("owner", "name", name="uq_repositories_owner_name"),
    )
    op.create_index("ix_repositories_owner", "repositories", ["owner"])
    op.create_index("ix_repositories_layer", "repositories", ["layer"])

    op.create_table(
        "blobs",
        sa.Column("sha256", sa.String(64), primary_key=True),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "trees",
        sa.Column("hash", sa.String(64), primary_key=True),
        sa.Column(
            "repo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_trees_repo_id", "trees", ["repo_id"])

    op.create_table(
        "tree_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "tree_hash",
            sa.String(64),
            sa.ForeignKey("trees.hash", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("mode", sa.Integer(), nullable=False),
        sa.Column("entry_type", sa.String(8), nullable=False),
        sa.Column("target_hash", sa.String(64), nullable=False),
        sa.UniqueConstraint("tree_hash", "name", name="uq_tree_entries_tree_name"),
    )
    op.create_index("ix_tree_entries_tree_hash", "tree_entries", ["tree_hash"])
    op.create_index("ix_tree_entries_target_hash", "tree_entries", ["target_hash"])

    op.create_table(
        "commits",
        sa.Column("hash", sa.String(64), primary_key=True),
        sa.Column(
            "repo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tree_hash",
            sa.String(64),
            sa.ForeignKey("trees.hash", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "parents",
            postgresql.ARRAY(sa.String(64)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("author_id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("lineage_json", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_commits_repo_id", "commits", ["repo_id"])

    op.create_table(
        "refs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repo_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "commit_hash",
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("repo_id", "name", name="uq_refs_repo_name"),
    )
    op.create_index("ix_refs_repo_id", "refs", ["repo_id"])


def downgrade() -> None:
    op.drop_table("refs")
    op.drop_table("commits")
    op.drop_table("tree_entries")
    op.drop_table("trees")
    op.drop_table("blobs")
    op.drop_table("repositories")
