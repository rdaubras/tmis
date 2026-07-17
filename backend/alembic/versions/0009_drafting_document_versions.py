"""drafting_document_versions

T5 of the "cases -> drafting" persistent & isolated slice
(docs/28-legal-drafting.md): persists `tmis.legal_drafting.versioning.
schemas.DocumentVersion` behind `VersioningPort`, scoped by `firm_id`
exactly like `drafting_documents` (ADR-SLICE-01/02) — a version snapshot
is core drafting state (section 3, item 4), unlike history/validation/
review/style which stay in-memory this sprint (documented debt).

Revision ID: 0009_drafting_document_versions
Revises: 0008_drafting_documents_firm_id
Create Date: 2026-07-16

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_drafting_document_versions"
down_revision: str | None = "0008_drafting_documents_firm_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "drafting_document_versions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("firm_id", sa.String(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("author", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "version_number", name="uq_drafting_version_number"),
    )
    op.create_index(
        op.f("ix_drafting_document_versions_document_id"),
        "drafting_document_versions",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_drafting_document_versions_firm_id"),
        "drafting_document_versions",
        ["firm_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_drafting_document_versions_firm_id"), table_name="drafting_document_versions"
    )
    op.drop_index(
        op.f("ix_drafting_document_versions_document_id"), table_name="drafting_document_versions"
    )
    op.drop_table("drafting_document_versions")
