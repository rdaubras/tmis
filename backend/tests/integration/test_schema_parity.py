"""SEC/DB-01 (correctif): guards against the exact bug this correctif
fixes — `alembic upgrade head` on a fresh database produced a schema
missing `firms`/`users`/`cases` entirely, because the migration chain
started at `0001` assuming those tables already existed. No test ever
caught this because every other test creates tables via
`Base.metadata.create_all()`, never through the real migration chain.

`test_schema_parity_between_migrations_and_orm_models` is the durable
guard (T3, correctif brief): it runs the real migration chain end to end
on a throwaway database and compares the resulting tables to `Base.
metadata.tables` — the same "every model, table, and migration in
lockstep" principle `core.tenancy.scoped_query` enforces at the ORM
level (see docs/07-strategie-securite.md), applied here to the migration
chain itself. Any model added without a migration, or any migration
creating a table with no ORM model, now fails a test instead of being
discovered in production, on first deploy, exactly as this bug was.

`test_upgrade_head_on_a_fresh_database_emits_no_orphan_warnings` (T4)
proves the fix directly: `0012_case_profiles_firm_id`/`0013_document_
records_firm_id` used to warn "no 'cases' table found" and purge every
row as an orphan on a fresh database, because `cases` never existed yet
at that point in the chain — this asserts that warning is gone.
"""

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

import tmis.cabinet_knowledge.knowledge.adapters.sqlalchemy_store  # noqa: F401
import tmis.case_intelligence.cases.adapters.sqlalchemy_store  # noqa: F401
import tmis.collaboration.workspace.adapters.sqlalchemy_store  # noqa: F401
import tmis.document_intelligence.adapters.sqlalchemy_store  # noqa: F401
import tmis.infrastructure.persistence.models  # noqa: F401 — registers firms/users/cases
import tmis.legal_drafting.documents.sqlalchemy_store  # noqa: F401
import tmis.legal_drafting.versioning.sqlalchemy_service  # noqa: F401
import tmis.legal_reasoning.reasoner.sqlalchemy_store  # noqa: F401
import tmis.legal_research.history.adapters.sqlalchemy_store  # noqa: F401
import tmis.legal_research.search.sqlalchemy_store  # noqa: F401
from alembic import command
from alembic.config import Config
from tmis.core.config import get_settings
from tmis.core.database import Base

_BACKEND_ROOT = Path(__file__).resolve().parents[2]

# `sqlite_sequence` is SQLite's own bookkeeping table for `AUTOINCREMENT`
# columns (none of this schema's PKs use it, but the dialect can still
# create one implicitly) — not part of anyone's schema, never expected on
# either side of the comparison. `alembic_version` is alembic's own
# bookkeeping table, likewise excluded.
_INFRASTRUCTURE_TABLES = {"alembic_version", "sqlite_sequence"}


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "schema-parity.db"


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


def test_schema_parity_between_migrations_and_orm_models(
    alembic_config: Config, db_path: Path
) -> None:
    command.upgrade(alembic_config, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        migrated_tables = set(inspect(engine).get_table_names()) - _INFRASTRUCTURE_TABLES
    finally:
        engine.dispose()

    model_tables = set(Base.metadata.tables)

    assert migrated_tables == model_tables, (
        f"migrations vs. ORM models diverge: "
        f"only in migrations={migrated_tables - model_tables}, "
        f"only in models={model_tables - migrated_tables}"
    )


def test_schema_parity_columns_per_table(alembic_config: Config, db_path: Path) -> None:
    """Reinforcement (T3, "recommandé"): column-name parity per table,
    on top of the table-name parity above — this is exactly what would
    have caught this correctif's bug (missing tables), plus a class of
    bug it wouldn't (a table present on both sides with diverging
    columns, e.g. a model field added without a matching migration)."""
    command.upgrade(alembic_config, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        inspector = inspect(engine)
        migrated_columns = {
            table: {col["name"] for col in inspector.get_columns(table)}
            for table in inspector.get_table_names()
            if table not in _INFRASTRUCTURE_TABLES
        }
    finally:
        engine.dispose()

    model_columns = {
        table.name: set(table.columns.keys()) for table in Base.metadata.tables.values()
    }

    assert migrated_columns == model_columns


def test_upgrade_head_on_a_fresh_database_emits_no_orphan_warnings(
    alembic_config: Config, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="alembic.runtime.migration"):
        command.upgrade(alembic_config, "head")

    orphan_warnings = [
        record.message
        for record in caplog.records
        if "no 'cases' table found" in record.message or "purging orphan" in record.message
    ]
    assert orphan_warnings == [], (
        f"'alembic upgrade head' on a fresh database purged rows or warned about "
        f"a missing foundation table it should have created itself: {orphan_warnings}"
    )


def test_upgrade_head_foundations_support_a_real_write(
    alembic_config: Config, session_factory: sessionmaker[Session]
) -> None:
    """T4: once `firms`/`users`/`cases` exist from the very first
    migration, a realistic write through them (a firm, a case it owns,
    and a `case_profiles` row referencing that case) must round-trip
    untouched — nothing downstream purges it as an orphan when the
    foundations it depends on are actually there."""
    command.upgrade(alembic_config, "head")

    import uuid

    firm_id = uuid.uuid4()
    case_id = uuid.uuid4()

    with session_factory() as session:
        session.execute(
            text(
                "INSERT INTO firms (id, name, plan, is_active) "
                "VALUES (:id, :name, 'SOLO', 1)"
            ),
            {"id": str(firm_id), "name": "Cabinet Test"},
        )
        session.execute(
            text(
                "INSERT INTO cases (id, firm_id, title, status) "
                "VALUES (:id, :firm_id, :title, 'OPEN')"
            ),
            {"id": str(case_id), "firm_id": str(firm_id), "title": "Dossier Test"},
        )
        session.execute(
            text(
                "INSERT INTO case_profiles (case_id, firm_id, title, payload) "
                "VALUES (:case_id, :firm_id, :title, '{}')"
            ),
            {"case_id": str(case_id), "firm_id": str(firm_id), "title": "Dossier Test"},
        )
        session.commit()

    with session_factory() as session:
        firms = session.execute(text("SELECT id FROM firms")).fetchall()
        cases = session.execute(text("SELECT id, firm_id FROM cases")).fetchall()
        profiles = session.execute(text("SELECT case_id, firm_id FROM case_profiles")).fetchall()

    assert len(firms) == 1
    assert len(cases) == 1
    assert len(profiles) == 1
    assert profiles[0] == (str(case_id), str(firm_id))
