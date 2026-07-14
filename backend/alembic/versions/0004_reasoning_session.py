"""reasoning_session

Persists tmis.legal_reasoning.reasoner.schemas.ReasoningSession behind
SessionStorePort (Sprint 26). Plain upsert-by-id table — see
tmis.legal_reasoning.reasoner.sqlalchemy_store for the rationale (mirrors
InMemorySessionStore's dict-overwrite semantics, unlike
document_intelligence's append-only versioned store).

Revision ID: 0004_reasoning_session
Revises: 0003_research_history
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_reasoning_session"
down_revision: str | None = "0003_research_history"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reasoning_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_reasoning_sessions_case_id"),
        "reasoning_sessions",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reasoning_sessions_created_at"),
        "reasoning_sessions",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_reasoning_sessions_created_at"), table_name="reasoning_sessions")
    op.drop_index(op.f("ix_reasoning_sessions_case_id"), table_name="reasoning_sessions")
    op.drop_table("reasoning_sessions")
