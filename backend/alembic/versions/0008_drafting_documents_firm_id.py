"""drafting_documents_firm_id

ADR-SLICE-01 (docs/28-legal-drafting.md, "cases -> drafting" persistent &
isolated slice): adds the `firm_id` column `drafting_documents` was
missing, so `tmis.legal_drafting.documents.sqlalchemy_store.
SQLAlchemyDraftDocumentStore` can scope every read/write through
`core.tenancy.scoped_query` exactly like the `cases` table does.

Note on "0005_document_draft": that revision's *id* suggested a second,
separate "document_draft" table diverging from `drafting_documents` — in
fact its `upgrade()` already targets `drafting_documents` (same table,
same columns) and nothing named `document_draft` was ever created. There
is therefore no stray table to `drop_table` here; this migration finishes
the reconciliation ADR-SLICE-01 asks for by adding the one column that
was actually missing, on the one table that has ever existed.

Revision ID: 0008_drafting_documents_firm_id
Revises: 0007_knowledge_object
Create Date: 2026-07-16

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_drafting_documents_firm_id"
down_revision: str | None = "0007_knowledge_object"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "drafting_documents",
        sa.Column("firm_id", sa.String(), nullable=False),
    )
    op.create_index(
        op.f("ix_drafting_documents_firm_id"),
        "drafting_documents",
        ["firm_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_drafting_documents_firm_id"), table_name="drafting_documents")
    op.drop_column("drafting_documents", "firm_id")
