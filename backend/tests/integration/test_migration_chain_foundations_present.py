"""T4 (SEC/DB-01, docs/151-architecture-persistance.md): with `firms`/
`users`/`cases` now created by `0000_base_identity`, the `firm_id`
backfills in `0012_case_profiles_firm_id` and
`0013_document_records_firm_id` should find their foundations already in
place on a blank database — no "no 'cases' table found" warning, and no
row purged solely because `cases` was missing (the bug this correctif
fixes; see `tests/integration/case_intelligence/
test_migration_case_profiles_firm_id.py` for the purge-on-missing-
foundation behaviour those migrations still have for genuinely orphaned
rows, which this test does not touch).
"""

import logging
import sqlite3
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config
from tmis.core.config import get_settings

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_BEFORE_BACKFILLS = "0011_research_searches"


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "migration-chain-foundations.db"


@pytest.fixture
def alembic_config(db_path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    monkeypatch.setenv("TMIS_DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()

    cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
    return cfg


def test_upgrade_head_on_blank_database_creates_no_orphan_warnings(
    alembic_config: Config, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="alembic.runtime.migration"):
        command.upgrade(alembic_config, "head")

    orphan_warnings = [
        record.message for record in caplog.records if "no 'cases' table found" in record.message
    ]
    assert orphan_warnings == []


def test_upgrade_head_keeps_case_profiles_row_seeded_before_the_backfill_migrations(
    alembic_config: Config, db_path: Path
) -> None:
    command.upgrade(alembic_config, _BEFORE_BACKFILLS)

    engine = create_engine(f"sqlite:///{db_path}")
    firm_id = uuid.uuid4()
    case_id = uuid.uuid4()
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO firms (id, name, plan, is_active, created_at) "
                    "VALUES (:id, :name, :plan, 1, CURRENT_TIMESTAMP)"
                ),
                {"id": str(firm_id), "name": "Cabinet Fondations", "plan": "SOLO"},
            )
            conn.execute(
                text(
                    "INSERT INTO cases (id, firm_id, title, status, created_at) "
                    "VALUES (:id, :firm_id, :title, :status, CURRENT_TIMESTAMP)"
                ),
                {"id": str(case_id), "firm_id": str(firm_id), "title": "Dossier", "status": "OPEN"},
            )
            conn.execute(
                text(
                    "INSERT INTO case_profiles (case_id, title, payload) "
                    "VALUES (:case_id, :title, :payload)"
                ),
                {"case_id": str(case_id), "title": "Dossier", "payload": "{}"},
            )
    finally:
        engine.dispose()

    command.upgrade(alembic_config, "head")

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT case_id, firm_id FROM case_profiles").fetchall()
    finally:
        conn.close()

    assert rows == [(str(case_id), str(firm_id))]
