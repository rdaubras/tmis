"""case_profile

Persists tmis.case_intelligence.cases.schemas.CaseProfile behind
CaseStorePort (Sprint 26). One row per case, upserted on save() to match
InMemoryCaseStore's overwrite semantics.

Revision ID: 0002_case_profile
Revises: 0001_document_record
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_case_profile"
down_revision: str | None = "0001_document_record"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "case_profiles",
        sa.Column("case_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("case_id"),
    )


def downgrade() -> None:
    op.drop_table("case_profiles")
