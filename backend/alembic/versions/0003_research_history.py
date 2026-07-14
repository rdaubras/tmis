"""research_history

Persists tmis.legal_research.history.schemas.ResearchHistoryEntry behind
ResearchHistoryPort (Sprint 26). Append-only audit log — one row per
`record()` call, never overwritten, matching InMemoryResearchHistory's
`list.append` semantics.

Revision ID: 0003_research_history
Revises: 0002_case_profile
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_research_history"
down_revision: str | None = "0002_case_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_history_entries",
        sa.Column("row_id", sa.Uuid(), nullable=False),
        sa.Column("entry_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("case_id", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("row_id"),
    )
    op.create_index(
        op.f("ix_research_history_entries_entry_id"),
        "research_history_entries",
        ["entry_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_research_history_entries_user_id"),
        "research_history_entries",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_research_history_entries_case_id"),
        "research_history_entries",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_research_history_entries_timestamp"),
        "research_history_entries",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_research_history_entries_timestamp"), table_name="research_history_entries"
    )
    op.drop_index(
        op.f("ix_research_history_entries_case_id"), table_name="research_history_entries"
    )
    op.drop_index(
        op.f("ix_research_history_entries_user_id"), table_name="research_history_entries"
    )
    op.drop_index(
        op.f("ix_research_history_entries_entry_id"), table_name="research_history_entries"
    )
    op.drop_table("research_history_entries")
