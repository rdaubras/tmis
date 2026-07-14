"""workspace

Persists tmis.collaboration.workspace.schemas.Workspace behind
WorkspaceStorePort (Sprint 26). One row per workspace, upserted on save()
to match InMemoryWorkspaceStore's overwrite semantics.

Revision ID: 0006_workspace
Revises: 0005_document_draft
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_workspace"
down_revision: str | None = "0005_document_draft"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("firm_id", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workspaces_firm_id", "workspaces", ["firm_id"])


def downgrade() -> None:
    op.drop_index("ix_workspaces_firm_id", table_name="workspaces")
    op.drop_table("workspaces")
