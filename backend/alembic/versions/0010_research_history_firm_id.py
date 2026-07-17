"""research_history_firm_id

ADR-RESEARCH-02 ("legal_research" persistent & isolated slice, see
docs/21-legal-research.md): adds the `firm_id` column
`research_history_entries` was missing, so
`tmis.legal_research.history.adapters.sqlalchemy_store.
SQLAlchemyResearchHistory` can scope every read/write through
`core.tenancy.scoped_query` — the same pattern `drafting_documents`
gained in migration `0008` for the `cases -> drafting` slice.

Revision ID: 0010_research_history_firm_id
Revises: 0009_drafting_document_versions
Create Date: 2026-07-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_research_history_firm_id"
down_revision: str | None = "0009_drafting_document_versions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "research_history_entries",
        sa.Column("firm_id", sa.String(), nullable=False),
    )
    op.create_index(
        op.f("ix_research_history_entries_firm_id"),
        "research_history_entries",
        ["firm_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_research_history_entries_firm_id"), table_name="research_history_entries"
    )
    op.drop_column("research_history_entries", "firm_id")
