from fastapi import APIRouter, Depends, HTTPException, Query

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
    orchestrator: ResearchOrchestrator = Depends(get_research_orchestrator),
) -> ResearchSearchResponse:
    response = await orchestrator.search(
        payload.query,
        filters=dict(payload.filters) if payload.filters else None,
        connector_names=payload.connector_names,
        user_id=payload.user_id,
        case_id=payload.case_id,
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
    user_id: str | None = Query(default=None),
    case_id: str | None = Query(default=None),
    orchestrator: ResearchOrchestrator = Depends(get_research_orchestrator),
) -> list[ResearchHistoryEntryResponse]:
    history = orchestrator.history
    if user_id is not None:
        entries = history.list_for_user(user_id)
    elif case_id is not None:
        entries = history.list_for_case(case_id)
    else:
        entries = history.list_all()
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
