"""case_profiles_firm_id

ADR-CASEINT-01/02 ("case_intelligence" persistent & isolated slice, see
docs/19-case-intelligence.md): adds the `firm_id` column `case_profiles`
was missing, so `tmis.case_intelligence.cases.adapters.sqlalchemy_store.
SQLAlchemyCaseStore` can scope every read/write through
`core.tenancy.scoped_query` exactly like `drafting_documents`
(migration 0008) and `research_history_entries` (migration 0010).

Unlike those two migrations, `case_profiles` is not empty at this point
(persistent since Sprint 43, migration 0002) — a naked
`ADD COLUMN firm_id NOT NULL` would fail outright, and even if it didn't,
every existing row would need a real `firm_id`, not a fabricated one. So
this migration runs in three steps: add the column nullable, backfill it
by deriving each row's `firm_id` from the `cases` row its own `case_id`
names (`cases.firm_id` — `cases` is itself already firm-scoped, see
`tmis.domain.case.entities.Case`), then tighten the column to
`NOT NULL`.

A `case_profiles` row whose `case_id` does not resolve to any `cases`
row (malformed id, or a dossier that was since deleted) has no firm to
inherit — ADR-CASEINT-02 says a case profile's `firm_id` must equal its
owning case's `firm_id`, so there is no safe default to backfill it
with. Such orphan rows are logged and purged rather than left with a
null (or guessed) `firm_id` — this is the standard this vertical-slice
template now expects from any firm_id backfill onto an already-populated
table, not a one-off decision for this table alone.

The backfill is done in plain Python (fetch every `cases`/`case_profiles`
row, join by normalized UUID string in memory, `UPDATE ... WHERE
case_id = :case_id` one row at a time) rather than a single correlated
SQL `UPDATE`, because `case_profiles.case_id` is not guaranteed to be a
well-formed UUID (pre-slice test fixtures and any other free-form caller
could have written non-UUID ids) and `cases.id` is a native `uuid`
column on Postgres — a `CAST` inside a set-based `UPDATE` would abort the
whole statement on the first malformed row instead of letting this
migration decide, per row, that a malformed id makes the row an orphan.

Revision ID: 0012_case_profiles_firm_id
Revises: 0011_research_searches
Create Date: 2026-07-17

"""

import logging
import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_case_profiles_firm_id"
down_revision: str | None = "0011_research_searches"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

logger = logging.getLogger("alembic.runtime.migration")


def _normalize_uuid(value: object) -> str | None:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


def upgrade() -> None:
    op.add_column("case_profiles", sa.Column("firm_id", sa.String(), nullable=True))

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    firm_id_by_case_uuid: dict[str, str] = {}
    if inspector.has_table("cases"):
        for case_id_value, firm_id_value in bind.execute(
            sa.text("SELECT id, firm_id FROM cases")
        ).fetchall():
            normalized_case_id = _normalize_uuid(case_id_value)
            if normalized_case_id is not None:
                # `firm_id_value` comes back from the DBAPI as whatever
                # raw form the dialect stores a `uuid` column in (a
                # dashless hex string on SQLite, a `uuid.UUID` on
                # Postgres via psycopg) — normalize it to the same
                # canonical dashed string every other firm-scoped store
                # in this codebase uses (`str(uuid.UUID(...))`,
                # e.g. `SQLAlchemyCaseStore`), falling back to the raw
                # value only if it somehow isn't a well-formed UUID.
                firm_id_by_case_uuid[normalized_case_id] = (
                    _normalize_uuid(firm_id_value) or str(firm_id_value)
                )
    else:
        logger.warning(
            "0012_case_profiles_firm_id: no 'cases' table found — every "
            "case_profiles row will be treated as an orphan and purged."
        )

    orphan_case_ids: list[str] = []
    for (case_id,) in bind.execute(sa.text("SELECT case_id FROM case_profiles")).fetchall():
        normalized_case_id = _normalize_uuid(case_id)
        firm_id = (
            firm_id_by_case_uuid.get(normalized_case_id)
            if normalized_case_id is not None
            else None
        )
        if firm_id is not None:
            bind.execute(
                sa.text("UPDATE case_profiles SET firm_id = :firm_id WHERE case_id = :case_id"),
                {"firm_id": firm_id, "case_id": case_id},
            )
        else:
            orphan_case_ids.append(case_id)
            logger.warning(
                "0012_case_profiles_firm_id: purging orphan case_profiles row "
                "case_id=%r (no matching 'cases' row for any firm)",
                case_id,
            )

    if orphan_case_ids:
        bind.execute(
            sa.text("DELETE FROM case_profiles WHERE case_id = :case_id"),
            [{"case_id": case_id} for case_id in orphan_case_ids],
        )

    # `batch_alter_table` (not a plain `op.alter_column`): SQLite has no
    # `ALTER TABLE ... ALTER COLUMN ... SET NOT NULL` at all — batch mode
    # recreates the table under the hood there, and is a harmless no-op
    # wrapper around a plain `ALTER COLUMN` on Postgres, so this one form
    # works on both backends this repo runs on (Postgres in production,
    # SQLite in tests — see this migration's own test,
    # tests/integration/case_intelligence/test_migration_case_profiles_firm_id.py).
    with op.batch_alter_table("case_profiles") as batch_op:
        batch_op.alter_column("firm_id", existing_type=sa.String(), nullable=False)
        batch_op.create_index(
            op.f("ix_case_profiles_firm_id"), ["firm_id"], unique=False
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_case_profiles_firm_id"), table_name="case_profiles")
    op.drop_column("case_profiles", "firm_id")
