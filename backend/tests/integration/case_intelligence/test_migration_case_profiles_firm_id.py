"""Runs the real Alembic migration `0012_case_profiles_firm_id` (T1,
docs/19-case-intelligence.md) against a sqlite database seeded with
pre-existing `case_profiles` rows — not just an empty schema. `case_
profiles` has been persistent since migration `0002` (Sprint 43), so
this is the first migration in the repo that has to backfill a new
`firm_id` column onto real data rather than adding it to a table that
happens to still be empty (see the migration's own module docstring for
why a naked `ADD COLUMN ... NOT NULL` cannot be used here).

`firms`/`users`/`cases` are not themselves Alembic-managed tables in
this repo (created via `Base.metadata.create_all`, same as every other
test that needs them — see `tests/security/conftest.py`), so this test
creates them directly rather than through more migrations.
"""

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
_DOWN_REVISION = "0011_research_searches"
_HEAD_REVISION = "0012_case_profiles_firm_id"


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "migration-0012.db"


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


def _seed_firms_and_cases(session_factory: sessionmaker[Session]) -> dict[str, object]:
    """Creates `firms`/`cases` directly (they predate Alembic in this
    repo) and pre-existing `case_profiles` rows via raw SQL matching
    migration `0002`'s original schema (`case_id`, `title`, `payload`
    only — no `firm_id` yet, exactly what a database that has been
    running since Sprint 43 would already contain)."""
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

        # Raw INSERT: at this point in migration history `case_profiles`
        # has no `firm_id` column yet (migration 0012 hasn't run), so
        # inserting through the current `CaseProfileModel` ORM class
        # (which already declares `firm_id` in the *code*) would not
        # match the *database*'s actual pre-migration shape.
        session.execute(
            text(
                "INSERT INTO case_profiles (case_id, title, payload) "
                "VALUES (:case_id, :title, :payload)"
            ),
            [
                {
                    "case_id": str(case_owned_by_a),
                    "title": "Dossier A",
                    "payload": "{}",
                },
                {
                    "case_id": str(case_owned_by_b),
                    "title": "Dossier B",
                    "payload": "{}",
                },
                {
                    # Malformed id (pre-slice free-form string, e.g. an
                    # old test fixture) — never resolves to any case.
                    "case_id": "case-legacy-not-a-uuid",
                    "title": "Ancien dossier libre",
                    "payload": "{}",
                },
                {
                    # Well-formed UUID, but no `cases` row anywhere
                    # names it (the dossier was since deleted, or never
                    # existed) — also an orphan, for a different reason.
                    "case_id": str(orphan_uuid_case),
                    "title": "Dossier disparu",
                    "payload": "{}",
                },
            ],
        )
        session.commit()

    return {
        "firm_a": firm_a,
        "firm_b": firm_b,
        "case_owned_by_a": case_owned_by_a,
        "case_owned_by_b": case_owned_by_b,
    }


def test_upgrade_backfills_firm_id_from_owning_case_and_purges_orphans(
    alembic_config: Config, session_factory: sessionmaker[Session], db_path: Path
) -> None:
    command.upgrade(alembic_config, _DOWN_REVISION)
    ids = _seed_firms_and_cases(session_factory)

    command.upgrade(alembic_config, _HEAD_REVISION)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT case_id, firm_id, title FROM case_profiles").fetchall()
    finally:
        conn.close()

    by_case_id = {case_id: (firm_id, title) for case_id, firm_id, title in rows}

    # Owned rows: backfilled with the *owning case's* firm_id.
    assert by_case_id[str(ids["case_owned_by_a"])] == (str(ids["firm_a"]), "Dossier A")
    assert by_case_id[str(ids["case_owned_by_b"])] == (str(ids["firm_b"]), "Dossier B")

    # Orphans (malformed id, and well-formed but unowned id): purged,
    # not left with a null or fabricated firm_id.
    assert "case-legacy-not-a-uuid" not in by_case_id
    assert len(rows) == 2


def test_firm_id_column_is_not_null_after_upgrade(
    alembic_config: Config, session_factory: sessionmaker[Session], db_path: Path
) -> None:
    command.upgrade(alembic_config, _DOWN_REVISION)
    _seed_firms_and_cases(session_factory)
    command.upgrade(alembic_config, _HEAD_REVISION)

    conn = sqlite3.connect(db_path)
    try:
        columns = conn.execute("PRAGMA table_info(case_profiles)").fetchall()
    finally:
        conn.close()

    firm_id_column = next(col for col in columns if col[1] == "firm_id")
    # sqlite PRAGMA table_info: column[3] is `notnull` (1 = NOT NULL).
    assert firm_id_column[3] == 1


def test_downgrade_drops_the_firm_id_column_and_keeps_remaining_rows(
    alembic_config: Config, session_factory: sessionmaker[Session], db_path: Path
) -> None:
    command.upgrade(alembic_config, _DOWN_REVISION)
    ids = _seed_firms_and_cases(session_factory)
    command.upgrade(alembic_config, _HEAD_REVISION)

    command.downgrade(alembic_config, _DOWN_REVISION)

    conn = sqlite3.connect(db_path)
    try:
        columns = {col[1] for col in conn.execute("PRAGMA table_info(case_profiles)").fetchall()}
        rows = conn.execute("SELECT case_id, title FROM case_profiles").fetchall()
    finally:
        conn.close()

    assert "firm_id" not in columns
    assert set(rows) == {
        (str(ids["case_owned_by_a"]), "Dossier A"),
        (str(ids["case_owned_by_b"]), "Dossier B"),
    }


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
        session.execute(
            text(
                "INSERT INTO case_profiles (case_id, title, payload) "
                "VALUES (:case_id, :title, :payload)"
            ),
            {"case_id": str(case_id), "title": "Dossier Unique", "payload": "{}"},
        )
        session.commit()

    command.upgrade(alembic_config, _HEAD_REVISION)

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT case_id, firm_id FROM case_profiles").fetchall()
    finally:
        conn.close()

    assert rows == [(str(case_id), str(firm_id))]
