import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.db.session import SessionLocal
from tmis.core.tenancy import scoped_query


class CaseProfileModel(Base):
    __tablename__ = "case_profiles"

    # `case_id` alone is the primary key, not `(case_id, firm_id)`: a
    # case profile's `case_id` is the id of a real, single `cases` row
    # (ADR-CASEINT-02) and that table's own primary key already
    # guarantees `case_id` is globally unique across every firm — no
    # two firms can ever legitimately hold a profile for the same
    # `case_id`. `firm_id` is still stored (and every query still
    # scoped through it) purely so `scoped_query`/`SqlAlchemyCase
    # Repository` never have to trust an unverified caller.
    case_id: Mapped[str] = mapped_column(String, primary_key=True)
    firm_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SQLAlchemyCaseStore:
    """Postgres-backed implementation of `CaseStorePort`, scoped to
    exactly one firm for its whole lifetime (ADR-CASEINT-01, "case_
    intelligence" persistent & isolated slice, see
    docs/19-case-intelligence.md) — mirrors
    `tmis.legal_research.history.adapters.sqlalchemy_store.
    SQLAlchemyResearchHistory`'s "bind `firm_id` once, at construction"
    shape, not a per-call parameter.

    Deliberately keeps the Sprint 43 `session_factory` constructor
    argument instead of switching to a request-bound `Session`
    (ADR-CASEINT-03): unlike `research`/`drafting`, this store is read
    and written from a Celery task and a domain-event handler that have
    no HTTP request to borrow a `Session` from, only ever their own
    firm_id. Every method still opens and closes its own session per
    call, exactly as before this slice.

    Persists the whole `CaseProfile` as one JSON payload, except
    `case_id`/`firm_id` (columns) and `title`, which get dedicated
    columns.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session] = SessionLocal,
        *,
        firm_id: uuid.UUID | str,
    ) -> None:
        self._session_factory = session_factory
        self._firm_id = str(firm_id)

    def get(self, case_id: str) -> CaseProfile | None:
        with self._session_factory() as session:
            stmt = scoped_query(CaseProfileModel, self._firm_id).where(
                CaseProfileModel.case_id == case_id
            )
            row = session.execute(stmt).scalar_one_or_none()
            if row is None:
                return None
            combined: dict[str, Any] = dict(row.payload)
            combined["case_id"] = row.case_id
            combined["title"] = row.title
            result: CaseProfile = from_json(combined, CaseProfile)
            return result

    def save(self, profile: CaseProfile) -> None:
        with self._session_factory() as session:
            full = to_json(profile)
            payload = {k: v for k, v in full.items() if k not in ("case_id", "title")}
            row = CaseProfileModel(
                case_id=profile.case_id,
                firm_id=self._firm_id,
                title=profile.title,
                payload=payload,
            )
            session.merge(row)
            session.commit()

    def get_or_create(self, case_id: str, title: str) -> CaseProfile:
        existing = self.get(case_id)
        if existing is not None:
            return existing
        profile = CaseProfile(case_id=case_id, title=title)
        self.save(profile)
        return profile

    def list_ids(self) -> list[str]:
        with self._session_factory() as session:
            stmt = scoped_query(CaseProfileModel, self._firm_id)
            rows = session.scalars(stmt).all()
            return [row.case_id for row in rows]
