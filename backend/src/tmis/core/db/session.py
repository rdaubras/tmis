"""Session factories shared by every domain's persistence adapter.

Two engines exist, on purpose, both built from the same settings and the
same `Base` (see `base.py`) — not two connection *mechanisms* per module,
but two access modes for the one mechanism:

- The **sync** engine/session (re-exported from `tmis.core.database`, which
  already existed before this sprint) is what every `SQLAlchemy*Store`
  added in Sprint 26 uses. All seven ports this sprint persists
  (`DocumentStorePort`, `CaseStorePort`, `ResearchHistoryPort`,
  `SessionStorePort`, the drafting `DocumentStorePort`, `WorkspaceStorePort`,
  `KnowledgeStorePort`) declare plain synchronous methods — a port's
  signature cannot change, so an adapter implementing it cannot be
  `async def` either. Using the sync session there is not a compromise, it
  is the only way to implement those Protocols at all.
- The **async** engine (`asyncpg`) is for call sites that sit outside those
  seven ports' contracts entirely, e.g. the document version-history read
  used by the upload API (Sprint 26 Phase 4), which has no equivalent on
  `DocumentStorePort` (that port only ever returns the latest version).
"""

from collections.abc import AsyncGenerator, Generator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session

from tmis.core.config import get_settings
from tmis.core.database import SessionLocal, engine, get_db_session

__all__ = [
    "SessionLocal",
    "engine",
    "get_db_session",
    "get_async_db_session",
    "make_async_engine",
    "AsyncSessionLocal",
    "async_engine",
]


def _asyncpg_url(database_url: str) -> str:
    """Swaps whatever sync driver is configured (`psycopg`, ...) for
    `asyncpg`, keeping host/user/db unchanged — one settings source, two
    drivers."""
    return make_url(database_url).set(drivername="postgresql+asyncpg").render_as_string(
        hide_password=False
    )


def make_async_engine(database_url: str | None = None) -> AsyncEngine:
    url = _asyncpg_url(database_url or get_settings().database_url)
    return create_async_engine(url, pool_pre_ping=True)


async_engine: AsyncEngine = make_async_engine()
AsyncSessionLocal = async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_sync_db_session() -> Generator[Session, None, None]:
    """Alias of `tmis.core.database.get_db_session`, kept here so every
    domain adapter can import its session dependency from one place
    (`tmis.core.db.session`) regardless of whether it needs the sync or
    the async engine."""
    yield from get_db_session()
