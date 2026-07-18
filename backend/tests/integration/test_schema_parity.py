"""Guards against the class of bug fixed by migration `0000_base_identity`
(SEC/DB-01, docs/151-architecture-persistance.md): a model declared on
`Base` with no migration that creates its table (or the reverse — a
migration-created table with no model). Before `0000_base_identity`,
`alembic upgrade head` on a blank database never created `firms`/
`users`/`cases` at all, and nothing caught it because every other test
seeds those three tables via `Base.metadata.create_all()`, never through
the real migration chain.

Runs the real Alembic migration chain against a blank sqlite database
(same pattern as `tests/integration/case_intelligence/
test_migration_case_profiles_firm_id.py`) and compares the resulting
table set to `Base.metadata.tables` — the same source of truth `alembic
revision --autogenerate` diffs against.

`Base.metadata` is only as complete as the modules imported into this
process by the time the assertion runs: a model class registers itself
on `Base` at import time, not by mere existence in the codebase. The
imports below are `alembic/env.py`'s own list (every module env.py
imports so `target_metadata` sees it during a real `alembic upgrade`)
plus `tmis.legal_research.search.sqlalchemy_store`, which `env.py` does
not import — a real, separate gap this test surfaces (see the module's
own comment below) but does not fix, per this correctif's scope.
"""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

import tmis.cabinet_knowledge.knowledge.adapters.sqlalchemy_store  # noqa: F401
import tmis.case_intelligence.cases.adapters.sqlalchemy_store  # noqa: F401
import tmis.collaboration.workspace.adapters.sqlalchemy_store  # noqa: F401
import tmis.document_intelligence.adapters.sqlalchemy_store  # noqa: F401
import tmis.infrastructure.persistence.models  # noqa: F401
import tmis.legal_drafting.documents.sqlalchemy_store  # noqa: F401
import tmis.legal_drafting.versioning.sqlalchemy_service  # noqa: F401
import tmis.legal_reasoning.reasoner.sqlalchemy_store  # noqa: F401
import tmis.legal_research.history.adapters.sqlalchemy_store  # noqa: F401

# Not imported by `alembic/env.py` (a separate, pre-existing gap this
# test surfaces — see the module docstring above). Without this import,
# `ResearchSearchModel` never registers on `Base`, and this test would
# wrongly report `research_searches` (created by migration
# `0011_research_searches`) as a migration with no model.
import tmis.legal_research.search.sqlalchemy_store  # noqa: F401
from alembic import command
from alembic.config import Config
from tmis.core.config import get_settings
from tmis.core.database import Base

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def alembic_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    monkeypatch.setenv("TMIS_DATABASE_URL", f"sqlite:///{tmp_path / 'schema-parity.db'}")
    get_settings.cache_clear()

    cfg = Config(str(_BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
    return cfg


def test_migrated_tables_match_orm_models_exactly(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")

    engine = create_engine(get_settings().database_url)
    try:
        migrated_tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
    finally:
        engine.dispose()

    assert migrated_tables == set(Base.metadata.tables)


def test_migrated_columns_match_orm_model_columns_per_table(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")

    engine = create_engine(get_settings().database_url)
    try:
        inspector = inspect(engine)
        migrated_tables = set(inspector.get_table_names()) - {"alembic_version"}
        assert migrated_tables == set(
            Base.metadata.tables
        ), "Table-level parity must hold before column-level parity is meaningful."

        for table_name in migrated_tables:
            migrated_columns = {col["name"] for col in inspector.get_columns(table_name)}
            model_columns = {col.name for col in Base.metadata.tables[table_name].columns}
            assert migrated_columns == model_columns, f"column drift on table {table_name!r}"
    finally:
        engine.dispose()
