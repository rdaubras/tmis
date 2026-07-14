"""knowledge_object

Persists tmis.cabinet_knowledge.knowledge.schemas.KnowledgeObject behind
KnowledgeStorePort (Sprint 26). Plain upsert-by-id table — see
tmis.cabinet_knowledge.knowledge.adapters.sqlalchemy_store for the
rationale (mirrors InMemoryKnowledgeStore's dict-overwrite semantics).

Revision ID: 0007_knowledge_object
Revises: 0006_workspace
Create Date: 2026-07-14

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_knowledge_object"
down_revision: str | None = "0006_workspace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_objects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("firm_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_objects_firm_id"),
        "knowledge_objects",
        ["firm_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_objects_type"),
        "knowledge_objects",
        ["type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_knowledge_objects_type"), table_name="knowledge_objects")
    op.drop_index(op.f("ix_knowledge_objects_firm_id"), table_name="knowledge_objects")
    op.drop_table("knowledge_objects")
