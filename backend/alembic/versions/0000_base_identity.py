"""base_identity

SEC/DB-01 (correctif): `alembic upgrade head` on a fresh database never
created `firms`/`users`/`cases` — the migration chain started at `0001`
assuming those tables already existed (they were only ever created via
`Base.metadata.create_all()`, which every test uses instead of the real
migration chain, so no test ever exercised a fresh `alembic upgrade
head`). On a genuinely clean deployment, `0012_case_profiles_firm_id`/
`0013_document_records_firm_id` would then find no `cases` table and
purge every row as an orphan — correct logic, applied to foundations
that were never poured — and the very first write to `firms` would fail
with `UndefinedTable`. This migration is that missing foundation,
inserted as the new root of the chain (`0001`'s `down_revision` now
points here instead of `None` — see that migration's own diff).

Creates exactly the three tables `infrastructure.persistence.models`
already declares (`FirmModel`, `UserModel`, `CaseModel`) — the source of
truth for their shape — and nothing else (every other table already has
its own migration). Column types were read directly off the mapped
`Table` objects via `sqlalchemy.schema.CreateTable(...).compile(dialect=
postgresql.dialect())` rather than transcribed by hand, specifically to
avoid the ENUM-type drift risk called out in the correctif brief: a
hand-written `sa.Enum("solo", "cabinet", ...)` would not match what
`Mapped[SubscriptionPlan]` actually produces, which stores each member's
*name* (`'SOLO'`, `'CABINET'`, `'ENTERPRISE'`), not its `.value`
(`'solo'`, `'cabinet'`, `'enterprise'`) — `Enum(SubscriptionPlan)`'s
default `values_callable` is `[e.name for e in cls]`, not `[e.value for
e in cls]`. Compiling the real mapped columns for the postgresql dialect
was the reliable way to get this right without a live database to run
`alembic revision --autogenerate` against in this environment; the
resulting DDL was verified to match `CreateTable(model.__table__)`
exactly for all three tables. Plain `sa.Enum(...)` (not
`postgresql.ENUM(...)`) is used here for the same reason the ORM models
use the bare `Mapped[SomeEnum]` annotation: it degrades to an emulated
CHECK constraint on backends without a native enum (sqlite, used by
every test in this repo), while still compiling to a real Postgres
`CREATE TYPE ... AS ENUM` in production — one column declaration, both
backends, matching `Base.metadata.create_all()`'s own behavior exactly.

`op.create_table()` auto-creates each `sa.Enum`'s Postgres type before
the table that references it (the same mechanism `Base.metadata.
create_all()` uses) — no separate `CREATE TYPE` step needed here.
Dropping a table does **not** drop a Postgres enum type it referenced,
so `downgrade()` explicitly drops all three enum types after the tables
that used them are gone.

See `tests/integration/test_schema_parity.py` (added alongside this
migration) for the guard this correctif adds against a repeat of this
bug: it fails if `alembic upgrade head`'s resulting tables and
`Base.metadata.tables` ever diverge again, in either direction.

Revision ID: 0000_base_identity
Revises:
Create Date: 2026-07-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0000_base_identity"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SUBSCRIPTION_PLAN = sa.Enum("SOLO", "CABINET", "ENTERPRISE", name="subscriptionplan")
_ROLE = sa.Enum("LAWYER", "COLLABORATOR", "FIRM_ADMIN", "PLATFORM_ADMIN", name="role")
_CASE_STATUS = sa.Enum(
    "OPEN",
    "ANALYSIS_IN_PROGRESS",
    "DRAFTING_IN_PROGRESS",
    "PENDING_VALIDATION",
    "CLOSED",
    "ARCHIVED",
    name="casestatus",
)


def upgrade() -> None:
    op.create_table(
        "firms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("plan", _SUBSCRIPTION_PLAN, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("firm_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", _ROLE, nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["firm_id"], ["firms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("firm_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("status", _CASE_STATUS, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["firm_id"], ["firms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cases_firm_id"), "cases", ["firm_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_cases_firm_id"), table_name="cases")
    op.drop_table("cases")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_table("firms")

    bind = op.get_bind()
    _CASE_STATUS.drop(bind, checkfirst=True)
    _ROLE.drop(bind, checkfirst=True)
    _SUBSCRIPTION_PLAN.drop(bind, checkfirst=True)
