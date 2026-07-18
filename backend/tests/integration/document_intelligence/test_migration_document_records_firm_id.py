"""Runs the real Alembic migration `0013_document_records_firm_id` (T1,
docs/14-document-intelligence.md) against a sqlite database seeded with
pre-existing `document_records` rows — not just an empty schema.
`document_records` has been persistent since migration `0001` (Sprint
26/37), so this is the second migration in the repo (after `0012`) that
has to backfill a new `firm_id` column onto real data rather than adding
it to a table that happens to still be empty.

Unlike `case_profiles`, `document_records` has no dedicated `case_id`
column — the migration's only retroactive source is a `"case_id"` key
inside each row's own JSON `payload`, if present (see the migration's own
module docstring for why `DocumentRecord` never grew a persisted
`case_id` field and what that means for the backfill).

`firms`/`users`/`cases` are Alembic-managed since `0000_base_identity`
(SEC/DB-01), but this test still seeds them via `Base.metadata.
create_all` rather than by upgrading through `0000_base_identity` itself
— it only exercises the chain from `_DOWN_REVISION` (`0012_case_
profiles_firm_id`) onward, so it needs the tables `0013` reads from
present beforehand by some means, same as every other test that needs
them (see `tests/security/conftest.py`).
"""

import json
import sqlite3
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

import tmis.infrastructure.persistence.models  # noqa: F401 — registers firms/users/cases
from alembic import command
from alembic.config import Config
from tmis.core.config import get_settings
from tmis.core.database import Base
from tmis.infrastructure.persistence.models import CaseModel, FirmModel

_FIRMS_AND_CASES_TABLES = [Base.metadata.tables["firms"], Base.metadata.tables["cases"]]

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_DOWN_REVISION = "0012_case_profiles_firm_id"
_HEAD_REVISION = "0013_document_records_firm_id"


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "migration-0013.db"


@pytest.fixture
def alembic_config(db_path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    monkeypatch.setenv("TMIS_DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()

    cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
    return cfg


@pytest.fixture
def session_factory(db_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    yield sessionmaker(bind=engine)
    engine.dispose()


def _insert_document_record(
    session: Session,
    *,
    document_id: str,
    filename: str,
    case_id: str | None,
) -> None:
    payload = {"case_id": case_id} if case_id is not None else {}
    session.execute(
        text(
            "INSERT INTO document_records "
            "(id, document_id, version, filename, status, raw_bytes, payload) "
            "VALUES (:id, :document_id, 1, :filename, 'processed', :raw_bytes, :payload)"
        ),
        {
            "id": str(uuid.uuid4()),
            "document_id": document_id,
            "filename": filename,
            "raw_bytes": b"raw bytes",
            "payload": json.dumps(payload),
        },
    )


def _seed_firms_cases_and_documents(session_factory: sessionmaker[Session]) -> dict[str, object]:
    """Creates `firms`/`cases` directly (they predate Alembic in this
    repo) and pre-existing `document_records` rows via raw SQL matching
    migration `0001`'s original schema (no `firm_id` yet) — exactly what
    a database that has been running since Sprint 26/37 would already
    contain."""
    engine = session_factory.kw["bind"]
    Base.metadata.create_all(engine, tables=_FIRMS_AND_CASES_TABLES)

    firm_a = uuid.uuid4()
    firm_b = uuid.uuid4()
    case_owned_by_a = uuid.uuid4()
    case_owned_by_b = uuid.uuid4()
    orphan_uuid_case = uuid.uuid4()

    with session_factory() as session:
        session.add(FirmModel(id=firm_a, name="Cabinet A"))
        session.add(FirmModel(id=firm_b, name="Cabinet B"))
        session.add(CaseModel(id=case_owned_by_a, firm_id=firm_a, title="Dossier A"))
        session.add(CaseModel(id=case_owned_by_b, firm_id=firm_b, title="Dossier B"))
        session.commit()

        _insert_document_record(
            session, document_id="doc-a", filename="bail-a.pdf", case_id=str(case_owned_by_a)
        )
        _insert_document_record(
            session, document_id="doc-b", filename="bail-b.pdf", case_id=str(case_owned_by_b)
        )
        _insert_document_record(
            session, document_id="doc-no-case", filename="sans-dossier.pdf", case_id=None
        )
        _insert_document_record(
            session,
            document_id="doc-malformed-case",
            filename="dossier-invalide.pdf",
            case_id="not-a-uuid",
        )
        _insert_document_record(
            session,
            document_id="doc-orphan-case",
            filename="dossier-disparu.pdf",
            case_id=str(orphan_uuid_case),
        )
        session.commit()

    return {
        "firm_a": firm_a,
        "firm_b": firm_b,
        "case_owned_by_a": case_owned_by_a,
        "case_owned_by_b": case_owned_by_b,
    }


def test_upgrade_backfills_firm_id_from_owning_case_and_purges_unresolvable_rows(
    alembic_config: Config, session_factory: sessionmaker[Session], db_path: Path
) -> None:
    command.upgrade(alembic_config, _DOWN_REVISION)
    ids = _seed_firms_cases_and_documents(session_factory)

    command.upgrade(alembic_config, _HEAD_REVISION)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT document_id, firm_id FROM document_records").fetchall()
    finally:
        conn.close()

    by_document_id = dict(rows)

    # Rows whose payload names a case this migration can resolve: backfilled
    # with the *owning case's* firm_id.
    assert by_document_id["doc-a"] == str(ids["firm_a"])
    assert by_document_id["doc-b"] == str(ids["firm_b"])

    # Unresolvable rows (no case_id at all, malformed case_id, and
    # well-formed but unowned case_id): purged, not left with a null or
    # fabricated firm_id.
    assert "doc-no-case" not in by_document_id
    assert "doc-malformed-case" not in by_document_id
    assert "doc-orphan-case" not in by_document_id
    assert len(rows) == 2


def test_firm_id_column_is_not_null_after_upgrade(
    alembic_config: Config, session_factory: sessionmaker[Session], db_path: Path
) -> None:
    command.upgrade(alembic_config, _DOWN_REVISION)
    _seed_firms_cases_and_documents(session_factory)
    command.upgrade(alembic_config, _HEAD_REVISION)

    conn = sqlite3.connect(db_path)
    try:
        columns = conn.execute("PRAGMA table_info(document_records)").fetchall()
    finally:
        conn.close()

    firm_id_column = next(col for col in columns if col[1] == "firm_id")
    # sqlite PRAGMA table_info: column[3] is `notnull` (1 = NOT NULL).
    assert firm_id_column[3] == 1


def test_downgrade_drops_the_firm_id_column_and_keeps_remaining_rows(
    alembic_config: Config, session_factory: sessionmaker[Session], db_path: Path
) -> None:
    command.upgrade(alembic_config, _DOWN_REVISION)
    _seed_firms_cases_and_documents(session_factory)
    command.upgrade(alembic_config, _HEAD_REVISION)

    command.downgrade(alembic_config, _DOWN_REVISION)

    conn = sqlite3.connect(db_path)
    try:
        columns = {col[1] for col in conn.execute("PRAGMA table_info(document_records)").fetchall()}
        rows = conn.execute("SELECT document_id FROM document_records").fetchall()
    finally:
        conn.close()

    assert "firm_id" not in columns
    assert {row[0] for row in rows} == {"doc-a", "doc-b"}


def test_upgrade_on_a_database_with_no_orphans_keeps_every_row(
    alembic_config: Config, session_factory: sessionmaker[Session], db_path: Path
) -> None:
    command.upgrade(alembic_config, _DOWN_REVISION)
    engine = session_factory.kw["bind"]
    Base.metadata.create_all(engine, tables=_FIRMS_AND_CASES_TABLES)

    firm_id = uuid.uuid4()
    case_id = uuid.uuid4()
    with session_factory() as session:
        session.add(FirmModel(id=firm_id, name="Cabinet Seul"))
        session.add(CaseModel(id=case_id, firm_id=firm_id, title="Dossier Unique"))
        session.commit()
        _insert_document_record(
            session, document_id="doc-unique", filename="unique.pdf", case_id=str(case_id)
        )
        session.commit()

    command.upgrade(alembic_config, _HEAD_REVISION)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT document_id, firm_id FROM document_records").fetchall()
    finally:
        conn.close()

    assert rows == [("doc-unique", str(firm_id))]


def test_upgrade_preserves_multiple_versions_of_the_same_document(
    alembic_config: Config, session_factory: sessionmaker[Session], db_path: Path
) -> None:
    """Each `document_records` row is one *version* (see the adapter's
    own module docstring) — this migration must backfill/purge per row,
    never collapse or otherwise disturb a document's version history."""
    command.upgrade(alembic_config, _DOWN_REVISION)
    ids = _seed_firms_cases_and_documents(session_factory)

    with session_factory() as session:
        session.execute(
            text(
                "INSERT INTO document_records "
                "(id, document_id, version, filename, status, raw_bytes, payload) "
                "VALUES (:id, 'doc-a', 2, 'bail-a-v2.pdf', 'processed', :raw_bytes, :payload)"
            ),
            {
                "id": str(uuid.uuid4()),
                "raw_bytes": b"raw bytes v2",
                "payload": json.dumps({"case_id": str(ids["case_owned_by_a"])}),
            },
        )
        session.commit()

    command.upgrade(alembic_config, _HEAD_REVISION)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT version, firm_id FROM document_records WHERE document_id = 'doc-a' "
            "ORDER BY version ASC"
        ).fetchall()
    finally:
        conn.close()

    assert rows == [(1, str(ids["firm_a"])), (2, str(ids["firm_a"]))]
