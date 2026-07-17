import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from tmis.api.deps import Principal, get_current_principal
from tmis.core.database import get_db_session
from tmis.infrastructure.persistence.repositories import SqlAlchemyCaseRepository
from tmis.legal_research.api.schemas import (
    ResearchCitationResponse,
    ResearchHistoryEntryResponse,
    ResearchResultResponse,
    ResearchSearchRequest,
    ResearchSearchResponse,
)
from tmis.legal_research.bootstrap import get_research_orchestrator
from tmis.legal_research.citations.schemas import ResearchCitation
from tmis.legal_research.search.orchestrator import ResearchOrchestrator
from tmis.legal_research.search.schemas import ResearchResponse, ResearchResult

router = APIRouter(prefix="/legal-research", tags=["legal-research"])

# Same 404 whether the case belongs to another firm, doesn't exist, or
# isn't even a well-formed id — never confirms a cross-tenant case's
# existence (mirrors `tmis.legal_drafting.api.routes._resolve_owned_case_id`
# and `tmis.api.v1.case.routes.get_case`).
_CASE_NOT_FOUND_DETAIL = "Dossier introuvable."


def _resolve_owned_case_id(
    case_id: str | None, firm_id: uuid.UUID, session: Session
) -> str | None:
    """ADR-RESEARCH-02 (docs/21-legal-research.md), mirroring ADR-SLICE-03
    from the `cases -> drafting` slice (docs/28-legal-drafting.md): a
    search or a history lookup may only be attached to a case the
    caller's firm actually owns. `case_id` here is a plain string (shared
    with the unrelated, string-keyed identifiers used elsewhere in the
    research pipeline), while the persistent, firm-scoped `cases` table
    keys on a `uuid.UUID` — the explicit cast is done once, here, with a
    `404` (never a `500`) if the format is invalid. Returns the canonical
    string form of the owned case's id, or `None` if `case_id` was `None`
    to begin with.
    """
    if case_id is None:
        return None
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=_CASE_NOT_FOUND_DETAIL) from exc
    case = SqlAlchemyCaseRepository(session).get_by_id(case_uuid, firm_id)
    if case is None:
        raise HTTPException(status_code=404, detail=_CASE_NOT_FOUND_DETAIL)
    return str(case_uuid)


def _to_result_response(result: ResearchResult) -> ResearchResultResponse:
    return ResearchResultResponse(
        id=result.id,
        title=result.title,
        excerpt=result.excerpt,
        connector=result.connector,
        document_type=result.document_type,
        reference=result.reference,
        date=result.date,
        lexical_score=result.lexical_score,
        vector_score=result.vector_score,
        authority_score=result.authority_score,
        freshness_score=result.freshness_score,
        final_score=result.final_score,
    )


def _to_citation_response(citation: ResearchCitation) -> ResearchCitationResponse:
    return ResearchCitationResponse(
        source_id=citation.source_id,
        title=citation.title,
        date=citation.date,
        document_type=citation.document_type,
        reference=citation.reference,
        excerpt=citation.excerpt,
    )


def _to_search_response(
    response: ResearchResponse, citations: tuple[ResearchCitation, ...]
) -> ResearchSearchResponse:
    return ResearchSearchResponse(
        search_id=response.search_id,
        query=response.query,
        results=[_to_result_response(r) for r in response.results],
        citations=[_to_citation_response(c) for c in citations],
        connectors_used=list(response.connectors_used),
        duration_ms=response.duration_ms,
        cache_hit=response.cache_hit,
    )


@router.post("/search", response_model=ResearchSearchResponse)
async def launch_search(
    payload: ResearchSearchRequest,
    principal: Principal = Depends(get_current_principal),
    session: Session = Depends(get_db_session),
    orchestrator: ResearchOrchestrator = Depends(get_research_orchestrator),
) -> ResearchSearchResponse:
    case_id = _resolve_owned_case_id(payload.case_id, principal.firm_id, session)
    response = await orchestrator.search(
        payload.query,
        filters=dict(payload.filters) if payload.filters else None,
        connector_names=payload.connector_names,
        user_id=str(principal.user_id),
        case_id=case_id,
    )
    citations = orchestrator.get_citations(response.search_id) or ()
    return _to_search_response(response, citations)


@router.get("/searches/{search_id}", response_model=ResearchSearchResponse)
def get_search(
    search_id: str,
    orchestrator: ResearchOrchestrator = Depends(get_research_orchestrator),
) -> ResearchSearchResponse:
    response = orchestrator.get_response(search_id)
    if response is None:
        raise HTTPException(status_code=404, detail=f"No research search found for {search_id!r}")
    citations = orchestrator.get_citations(search_id) or ()
    return _to_search_response(response, citations)


@router.get("/history", response_model=list[ResearchHistoryEntryResponse])
def get_history(
    case_id: str | None = Query(default=None),
    principal: Principal = Depends(get_current_principal),
    session: Session = Depends(get_db_session),
    orchestrator: ResearchOrchestrator = Depends(get_research_orchestrator),
) -> list[ResearchHistoryEntryResponse]:
    history = orchestrator.history
    if case_id is not None:
        # `_resolve_owned_case_id` never returns `None` when `case_id` is
        # not `None` — it either resolves to the caller's own case or
        # raises 404, so the cast documents that guarantee to type
        # checkers rather than re-testing it here.
        owned_case_id = _resolve_owned_case_id(case_id, principal.firm_id, session)
        assert owned_case_id is not None  # noqa: S101 — guarded above
        entries = history.list_for_case(owned_case_id)
    else:
        entries = history.list_for_user(str(principal.user_id))
    return [
        ResearchHistoryEntryResponse(
            id=e.id,
            query_text=e.query_text,
            timestamp=e.timestamp,
            connectors_used=list(e.connectors_used),
            duration_ms=e.duration_ms,
            result_count=e.result_count,
            user_id=e.user_id,
            case_id=e.case_id,
        )
        for e in entries
    ]
