"""Postgres-backed `ResearchSearchStorePort` (ADR-RESEARCH-02,
"legal_research" persistent & isolated slice, see docs/21-legal-research.md).

Replaces the `_responses`/`_citations` dicts `ResearchOrchestrator` used
to keep on itself when it was a process-wide singleton: now that it is
assembled fresh per request (ADR-RESEARCH-02, mirroring ADR-SLICE-02 from
the `cases -> drafting` slice), a later `GET /searches/{search_id}` needs
somewhere durable to find a past search again.

Same shape as `SQLAlchemyDraftDocumentStore`: built on the request's own
`Session` plus the caller's `firm_id`, fixed for the instance's whole
lifetime, so `firm_id` is never a method parameter and every query still
goes through `core.tenancy.scoped_query` — a completed search belongs to
exactly one cabinet (the same rule the cache keys follow, ADR-RESEARCH-01).

One row per search (`save` is insert-only, matching the in-memory store's
dict-assignment semantics closely enough — a `search_id` is a freshly
minted UUID per call, so overwrites in practice never happen); `payload`
carries both the response and its citations, `firm_id`/`user_id`/
`case_id` broken out as indexed columns, never inside `payload`.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from tmis.core.db.base import Base
from tmis.core.db.dataclass_json import from_json, to_json
from tmis.core.tenancy import scoped_query
from tmis.legal_research.citations.schemas import ResearchCitation
from tmis.legal_research.search.schemas import ResearchResponse


class ResearchSearchModel(Base):
    """One row per search. `firm_id`/`user_id`/`case_id` are indexed
    columns; `payload` carries the response and its citations, never
    tenancy metadata (same rule as `DraftDocumentModel`)."""

    __tablename__ = "research_searches"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    firm_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    case_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


def _row_to_response(row: ResearchSearchModel) -> ResearchResponse:
    result: ResearchResponse = from_json(row.payload["response"], ResearchResponse)
    return result


def _row_to_citations(row: ResearchSearchModel) -> tuple[ResearchCitation, ...]:
    result: tuple[ResearchCitation, ...] = from_json(
        row.payload["citations"], tuple[ResearchCitation, ...]
    )
    return result


class SQLAlchemyResearchSearchStore:
    """Implements `ResearchSearchStorePort`. Built fresh per request by
    `tmis.legal_research.bootstrap.get_research_orchestrator` — never
    cached, never shared between tenants (ADR-RESEARCH-02)."""

    def __init__(self, session: Session, firm_id: uuid.UUID) -> None:
        self._session = session
        self._firm_id = str(firm_id)

    def save(
        self,
        response: ResearchResponse,
        citations: tuple[ResearchCitation, ...],
        *,
        user_id: str | None = None,
        case_id: str | None = None,
    ) -> None:
        row = ResearchSearchModel(
            id=response.search_id,
            firm_id=self._firm_id,
            user_id=user_id,
            case_id=case_id,
            timestamp=datetime.now(UTC),
            payload={"response": to_json(response), "citations": to_json(citations)},
        )
        self._session.merge(row)
        self._session.commit()

    def get(self, search_id: str) -> ResearchResponse | None:
        stmt = scoped_query(ResearchSearchModel, self._firm_id).where(
            ResearchSearchModel.id == search_id
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        return _row_to_response(row) if row is not None else None

    def get_citations(self, search_id: str) -> tuple[ResearchCitation, ...] | None:
        stmt = scoped_query(ResearchSearchModel, self._firm_id).where(
            ResearchSearchModel.id == search_id
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        return _row_to_citations(row) if row is not None else None


__all__ = ["ResearchSearchModel", "SQLAlchemyResearchSearchStore"]
