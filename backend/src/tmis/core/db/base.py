"""Single declarative base for every SQLAlchemy model in TMIS.

`tmis.core.database.Base` already exists (Sprint "Identity & Firm") and is
registered with Alembic (`alembic/env.py` imports
`tmis.infrastructure.persistence.models`, which declares its tables on it).
This module does not declare a second `DeclarativeBase` — it re-exports the
same one, so every domain adapter added in this sprint (and beyond) shares
one schema-of-record and one migration history, per the repo's
"never a second connection mechanism" rule.
"""

from tmis.core.database import Base

__all__ = ["Base"]
