from collections.abc import Callable
from typing import Any

from sqlalchemy import JSON, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.db.session import SessionLocal


class CaseProfileModel(Base):
    __tablename__ = "case_profiles"

    case_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class SQLAlchemyCaseStore:
    """Postgres-backed implementation of `CaseStorePort`.

    Persists the whole `CaseProfile` as one JSON payload, except
    `case_id` (primary key) and `title`, which get dedicated columns.
    """

    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory

    def get(self, case_id: str) -> CaseProfile | None:
        with self._session_factory() as session:
            row = session.execute(
                select(CaseProfileModel).where(CaseProfileModel.case_id == case_id)
            ).scalar_one_or_none()
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
            row = CaseProfileModel(case_id=profile.case_id, title=profile.title, payload=payload)
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
            rows = session.execute(select(CaseProfileModel.case_id)).scalars().all()
            return list(rows)
