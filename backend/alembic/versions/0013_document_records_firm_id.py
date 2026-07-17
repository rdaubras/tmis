"""document_records_firm_id

ADR-DOCINT-01 ("document_intelligence" persistent & isolated slice, see
docs/14-document-intelligence.md): adds the `firm_id` column
`document_records` was missing, so `tmis.document_intelligence.adapters.
sqlalchemy_store.SQLAlchemyDocumentStore` can scope every read/write
through `core.tenancy.scoped_query` exactly like `case_profiles`
(migration 0012), `drafting_documents` (migration 0008) and
`research_history_entries` (migration 0010). `document_records` is the
most sensitive table this template has touched: it carries `raw_bytes`,
the uploaded file itself, not just derived metadata.

Like `case_profiles`, `document_records` is not empty at this point
(persistent since Sprint 26/37) — a naked `ADD COLUMN firm_id NOT NULL`
would fail outright, and even if it didn't, every existing row would need
a real `firm_id`, not a fabricated one. So this migration runs in three
steps: add the column nullable, backfill it by deriving each row's
`firm_id` from the `cases` row its own `case_id` names, then tighten the
column to `NOT NULL`.

Unlike `case_profiles` (a dedicated `case_id` column), `document_records`
has no `case_id` column at all — `DocumentRecord` never grew that field
(ADR-DOCINT-01: a document's `firm_id` is derived from the uploader's
token at write time, never from `case_id`, since an upload with no
`case_id` at all must still be attributable to a firm). The *migration's*
only retroactive source is whatever `case_id` a pre-existing row's own
JSON `payload` happens to carry under a `"case_id"` key — every
`document_records` row this migration cannot resolve a `case_id` for
(missing, malformed, or naming no `cases` row) has no firm to inherit and
is purged, logged, exactly like `case_profiles`' orphans. This is a
one-row-at-a-time Python backfill (not a set-based SQL `UPDATE`) for the
same reason 0012 uses one: `payload->>'case_id'` is not guaranteed to be
a well-formed UUID, so a per-row Python check lets this migration decide,
per row, whether it is an orphan rather than aborting the whole
statement.

Identifies rows by their `(document_id, version)` pair, not the opaque
`id` primary key: a document can have several `document_records` rows
(one per version, see the adapter's own module docstring), and this
migration treats each version row's own `payload` independently.
`(document_id, version)` is also the one identifier pair this migration
can compare reliably across both backends without a round-trip through a
`Uuid`-typed column's bind/result processors (`document_id` is a plain
`String`, `version` a plain `Integer` — unlike `id`, which a raw-SQL-seeded
row can store in a different textual form than `Uuid`'s own bind
processor would normalize it to, silently failing to match).

Revision ID: 0013_document_records_firm_id
Revises: 0012_case_profiles_firm_id
Create Date: 2026-07-17

"""

import logging
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import delete, select, update

from alembic import op

revision: str = "0013_document_records_firm_id"
down_revision: str | None = "0012_case_profiles_firm_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

logger = logging.getLogger("alembic.runtime.migration")


def _normalize_uuid(value: object) -> str | None:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


def upgrade() -> None:
    op.add_column("document_records", sa.Column("firm_id", sa.String(), nullable=True))

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    firm_id_by_case_uuid: dict[str, str] = {}
    if inspector.has_table("cases"):
        for case_id_value, firm_id_value in bind.execute(
            sa.text("SELECT id, firm_id FROM cases")
        ).fetchall():
            normalized_case_id = _normalize_uuid(case_id_value)
            if normalized_case_id is not None:
                # Same canonicalisation as migration 0012: normalize
                # whatever raw form the dialect hands back (a dashless
                # hex string on SQLite, a `uuid.UUID` on Postgres via
                # psycopg) to the canonical dashed string every
                # firm-scoped store in this codebase uses.
                firm_id_by_case_uuid[normalized_case_id] = (
                    _normalize_uuid(firm_id_value) or str(firm_id_value)
                )
    else:
        logger.warning(
            "0013_document_records_firm_id: no 'cases' table found — every "
            "document_records row will be treated as an orphan and purged."
        )

    # A local, explicitly-typed `Table` (not raw `sa.text()`) for
    # `document_records`: `payload` is a JSON column, and only a
    # Core-typed `select()`/`update()` gets consistent JSON decoding
    # across SQLite (TEXT storage, decoded in Python) and Postgres —
    # `sa.text()` would hand back a raw, backend-specific value instead.
    # Deliberately excludes `id` (see the module docstring): rows are
    # identified by `(document_id, version)`, both plain `String`/
    # `Integer` columns with no bind/result-processor round-trip to worry
    # about.
    document_records = sa.Table(
        "document_records",
        sa.MetaData(),
        sa.Column("document_id", sa.String()),
        sa.Column("version", sa.Integer()),
        sa.Column("payload", sa.JSON()),
        sa.Column("firm_id", sa.String()),
    )

    orphan_keys: list[tuple[str, int]] = []
    rows = bind.execute(
        select(
            document_records.c.document_id, document_records.c.version, document_records.c.payload
        )
    ).fetchall()
    for document_id, version, payload in rows:
        case_id = payload.get("case_id") if isinstance(payload, dict) else None
        normalized_case_id = _normalize_uuid(case_id) if case_id else None
        firm_id = (
            firm_id_by_case_uuid.get(normalized_case_id)
            if normalized_case_id is not None
            else None
        )
        if firm_id is not None:
            bind.execute(
                update(document_records)
                .where(
                    document_records.c.document_id == document_id,
                    document_records.c.version == version,
                )
                .values(firm_id=firm_id)
            )
        else:
            orphan_keys.append((document_id, version))
            logger.warning(
                "0013_document_records_firm_id: purging orphan document_records row "
                "document_id=%r version=%r (no resolvable case_id -> firm_id)",
                document_id,
                version,
            )

    for document_id, version in orphan_keys:
        bind.execute(
            delete(document_records).where(
                document_records.c.document_id == document_id,
                document_records.c.version == version,
            )
        )

    # `batch_alter_table` (not a plain `op.alter_column`): SQLite has no
    # `ALTER TABLE ... ALTER COLUMN ... SET NOT NULL` at all — batch mode
    # recreates the table under the hood there (preserving the existing
    # `previous_version_id` self-referencing foreign key and the
    # `document_id` index), and is a harmless no-op wrapper around a
    # plain `ALTER COLUMN` on Postgres.
    with op.batch_alter_table("document_records") as batch_op:
        batch_op.alter_column("firm_id", existing_type=sa.String(), nullable=False)
        batch_op.create_index(op.f("ix_document_records_firm_id"), ["firm_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_records_firm_id"), table_name="document_records")
    op.drop_column("document_records", "firm_id")
