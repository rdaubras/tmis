"""document_record

Persists tmis.document_intelligence.schemas.record.DocumentRecord behind
DocumentStorePort (Sprint 26). One row per document version — see
tmis.document_intelligence.adapters.sqlalchemy_store for the versioning
rationale (save() always inserts, never updates in place).

Revision ID: 0001_document_record
Revises: 0000_base_identity
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_document_record"
down_revision: str | None = "0000_base_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("previous_version_id", sa.Uuid(), nullable=True),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("raw_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["previous_version_id"], ["document_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_document_records_document_id"),
        "document_records",
        ["document_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_document_records_document_id"), table_name="document_records")
    op.drop_table("document_records")
