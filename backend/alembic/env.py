from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from tmis.cabinet_knowledge.knowledge.adapters import (
    sqlalchemy_store as cabinet_knowledge_store,  # noqa: E501,F401
)
from tmis.case_intelligence.cases.adapters import sqlalchemy_store as case_store  # noqa: F401
from tmis.collaboration.workspace.adapters import sqlalchemy_store as workspace_store  # noqa: F401
from tmis.core.config import get_settings
from tmis.core.database import Base
from tmis.document_intelligence.adapters import sqlalchemy_store as document_store  # noqa: F401
from tmis.infrastructure.persistence import models  # noqa: F401  (registers models on Base)
from tmis.legal_drafting.documents import sqlalchemy_store as drafting_store  # noqa: F401
from tmis.legal_reasoning.reasoner import sqlalchemy_store as reasoning_store  # noqa: F401
from tmis.legal_research.history.adapters import (
    sqlalchemy_store as research_history_store,  # noqa: E501,F401
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
