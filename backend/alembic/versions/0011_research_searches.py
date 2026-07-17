"""research_searches

ADR-RESEARCH-02 ("legal_research" persistent & isolated slice, see
docs/21-legal-research.md): persists what `ResearchOrchestrator` used to
keep in the `_responses`/`_citations` dicts of its own now-removed
process-wide singleton — a later `GET /searches/{search_id}` (a fresh
request, a fresh per-request orchestrator) can only find a past search
again if it survives somewhere other than the object that produced it.
One row per search, keyed by `search_id`, scoped `firm_id` exactly like
`drafting_documents`/`research_history_entries`.

Revision ID: 0011_research_searches
Revises: 0010_research_history_firm_id
Create Date: 2026-07-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_research_searches"
down_revision: str | None = "0010_research_history_firm_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_searches",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("firm_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("case_id", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_research_searches_firm_id"), "research_searches", ["firm_id"], unique=False
    )
    op.create_index(
        op.f("ix_research_searches_user_id"), "research_searches", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_research_searches_case_id"), "research_searches", ["case_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_research_searches_case_id"), table_name="research_searches")
    op.drop_index(op.f("ix_research_searches_user_id"), table_name="research_searches")
    op.drop_index(op.f("ix_research_searches_firm_id"), table_name="research_searches")
    op.drop_table("research_searches")
