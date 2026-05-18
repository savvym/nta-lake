"""pipeline_cache.output_commit_hash FK RESTRICT → CASCADE

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-18 11:35:00

由 stage9-followup-cleanup-20260518 T-2 引入：修 pipeline-orchestrator-mvp stage 9
deploy_verify_v1.md 发现的 FK 缺 CASCADE 问题——`DELETE /repos/...` 触发
ForeignKeyViolationError: pipeline_cache_output_commit_hash_fkey。

upgrade：把 `pipeline_cache.output_commit_hash` FK 的 ondelete 从 RESTRICT 改 CASCADE。
downgrade：反向（CASCADE → RESTRICT，回滚路径，dev 不依赖）。

设计决策（见 spec.md 决策栏）：选 CASCADE 而非 SET NULL，因为
`PipelineCacheORM.output_commit_hash` nullable=False，SET NULL 物理违反 NOT NULL，
必须先改 nullable=True 才能用 SET NULL，超出本 change scope。
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "pipeline_cache_output_commit_hash_fkey",
        "pipeline_cache",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "pipeline_cache_output_commit_hash_fkey",
        "pipeline_cache",
        "commits",
        ["output_commit_hash"],
        ["hash"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "pipeline_cache_output_commit_hash_fkey",
        "pipeline_cache",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "pipeline_cache_output_commit_hash_fkey",
        "pipeline_cache",
        "commits",
        ["output_commit_hash"],
        ["hash"],
        ondelete="RESTRICT",
    )
