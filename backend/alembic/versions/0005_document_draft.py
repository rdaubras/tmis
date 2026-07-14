"""document_draft

Persists tmis.legal_drafting.documents.schemas.Document behind
DocumentStorePort (Sprint 26). Plain upsert-by-id table — see
tmis.legal_drafting.documents.sqlalchemy_store for the rationale (mirrors
InMemoryDocumentStore's dict-overwrite semantics, unlike
document_intelligence's append-only versioned store).

Revision ID: 0005_document_draft
Revises: 0004_reasoning_session
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_document_draft"
down_revision: str | None = "0004_reasoning_session"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "drafting_documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("case_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_drafting_documents_case_id"),
        "drafting_documents",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_drafting_documents_status"),
        "drafting_documents",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_drafting_documents_status"), table_name="drafting_documents")
    op.drop_index(op.f("ix_drafting_documents_case_id"), table_name="drafting_documents")
    op.drop_table("drafting_documents")
