"""base_identity

Foundational migration: creates `firms`, `users`, `cases` — the three
tables every later migration in this chain assumes already exist (0012
and 0013 backfill a `firm_id` derived from `cases`, 0002+ persist rows
that belong to a `firm`/`case`). Before this migration, `alembic upgrade
head` on a blank database never created these tables at all (they were
only ever produced by `Base.metadata.create_all()` in tests), so a clean
deployment could not persist anything.

Columns generated via `alembic revision --autogenerate` against a
database already at `0013_document_records_firm_id` (which has every
other table but not `firms`/`users`/`cases`), then pruned to keep only
the `firms`/`users`/`cases` operations — the ENUM types
(`subscriptionplan`, `role`, `casestatus`) are exactly what
`Base.metadata` derives from `tmis.infrastructure.persistence.models`,
not hand-written, to avoid drifting from the ORM models (see T1,
docs/151-architecture-persistance.md). One hand-edit on top of the raw
autogenerate output: `created_at`'s `server_default` is `sa.func.now()`,
not the literal `sa.text("now()")` autogenerate emitted — the model
declares `server_default=func.now()`, which SQLAlchemy compiles per
dialect (`now()` on Postgres, `CURRENT_TIMESTAMP` on SQLite);
autogenerate freezes whatever it compiled to against the Postgres
database it ran against, which breaks every SQLite-backed migration
test in this repo (the whole suite's convention, see
docs/152-guide-migrations.md).

Revision ID: 0000_base_identity
Revises:
Create Date: 2026-07-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0000_base_identity"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "firms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "plan",
            sa.Enum("SOLO", "CABINET", "ENTERPRISE", name="subscriptionplan"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("firm_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "OPEN",
                "ANALYSIS_IN_PROGRESS",
                "DRAFTING_IN_PROGRESS",
                "PENDING_VALIDATION",
                "CLOSED",
                "ARCHIVED",
                name="casestatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["firm_id"], ["firms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cases_firm_id"), "cases", ["firm_id"], unique=False)
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("firm_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("LAWYER", "COLLABORATOR", "FIRM_ADMIN", "PLATFORM_ADMIN", name="role"),
            nullable=False,
        ),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["firm_id"], ["firms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_cases_firm_id"), table_name="cases")
    op.drop_table("cases")
    op.drop_table("firms")

    # `create_table` created these native Postgres ENUM types implicitly
    # (checkfirst) as a side effect of each column's DDL — `drop_table`
    # does not reverse that, so drop them explicitly. `Enum.drop()` is a
    # no-op on backends with no native enum type (SQLite), so this is
    # safe on both backends this repo runs on.
    bind = op.get_bind()
    sa.Enum(name="role").drop(bind, checkfirst=True)
    sa.Enum(name="casestatus").drop(bind, checkfirst=True)
    sa.Enum(name="subscriptionplan").drop(bind, checkfirst=True)
