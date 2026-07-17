"""`GET /{case_id}/analysis` (Sprint 41) exposes the fully wired
`Orchestrator` (`agents.bootstrap.get_orchestrator()`) as a sixth route on
this same resource — a computed read triggered on demand, following the
precedent already set by `GET /{case_id}/summary` (Sprint 19), not a new
router — see docs/168-architecture-exposition-orchestrator.md.

Every route is firm-scoped since ADR-CASEINT-01/02 (docs/19-case-
intelligence.md, "case_intelligence" persistent & isolated slice):
`case_id` is no longer a free-form string a caller can invent — it must
name a `cases` row the caller's own firm owns (mirrors
`tmis.legal_drafting.api.routes._resolve_owned_case_id` and
`tmis.legal_research.api.routes._resolve_owned_case_id`), and every read
or write of the resulting `CaseProfile` goes through
`get_case_intelligence_workflow(firm_id)`, never a store shared across
tenants.
"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tmis.agents.bootstrap import get_orchestrator
from tmis.agents.contracts import AgentInput
from tmis.agents.orchestrator import Orchestrator
from tmis.ai.schemas.agent import AgentOutput
from tmis.api.deps import get_current_firm_id
from tmis.api.v1.case_intelligence.schemas import (
    ActorResponse,
    CaseAnalysisResponse,
    CaseAnalysisResultResponse,
    CaseProfileCreateRequest,
    CaseProfileResponse,
    CaseProfileUpdateRequest,
    CaseSearchResultResponse,
    CaseSummaryResponse,
    CitationResponse,
    FactResponse,
    LegalIssueResponse,
    TimelineEntryResponse,
)
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.workflow.case_workflow import CaseIntelligenceWorkflow
from tmis.core.database import get_db_session
from tmis.infrastructure.persistence.repositories import SqlAlchemyCaseRepository

router = APIRouter(prefix="/cases", tags=["case-intelligence"])

# Same 404 whether the case belongs to another firm, doesn't exist, or
# isn't even a well-formed id — never confirms a cross-tenant case's
# existence (mirrors `tmis.legal_drafting.api.routes._resolve_owned_
# case_id` and `tmis.api.v1.case.routes.get_case`).
_CASE_NOT_FOUND_DETAIL = "Dossier introuvable."


def _resolve_owned_case_id(case_id: str, firm_id: uuid.UUID, session: Session) -> str:
    """ADR-CASEINT-02: a case intelligence profile may only be attached
    to a case the caller's firm actually owns — `case_id` in this router
    is no longer a free-form string, it must resolve to a `cases` row via
    the firm-scoped `SqlAlchemyCaseRepository`. Returns the canonical
    string form of the owned case's id, or raises 404."""
    try:
        case_uuid = uuid.UUID(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=_CASE_NOT_FOUND_DETAIL) from exc
    case = SqlAlchemyCaseRepository(session).get_by_id(case_uuid, firm_id)
    if case is None:
        raise HTTPException(status_code=404, detail=_CASE_NOT_FOUND_DETAIL)
    return str(case_uuid)


def _get_profile_or_404(case_id: str, workflow: CaseIntelligenceWorkflow) -> CaseProfile:
    profile = workflow.case_store.get(case_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"No case intelligence profile for {case_id!r}")
    return profile


def _to_response(profile: CaseProfile) -> CaseProfileResponse:
    return CaseProfileResponse(
        case_id=profile.case_id,
        title=profile.title,
        is_deleted=profile.is_deleted,
        document_ids=list(profile.document_ids),
        actors=[
            ActorResponse(id=a.id, type=a.type.value, name=a.name, aliases=list(a.aliases))
            for a in profile.actors
        ],
        facts=[
            FactResponse(
                id=f.id,
                description=f.description,
                confidence=f.confidence,
                dates=list(f.dates),
                confirming_document_ids=list(f.confirming_document_ids),
                contradicting_document_ids=list(f.contradicting_document_ids),
            )
            for f in profile.facts
        ],
        legal_issues=[
            LegalIssueResponse(
                id=i.id, description=i.description, confidence=i.confidence, status=i.status.value
            )
            for i in profile.legal_issues
        ],
        updated_at=profile.updated_at,
    )


def _to_analysis_response(case_id: str, output: AgentOutput) -> CaseAnalysisResponse:
    """`output.result` is `dict[str, object]` (the common `AgentOutput`
    contract), but its actual shape after the four-node graph
    (analysis -> verifier -> synthesis -> verifier_final) is exactly
    `CaseAnalysisResultResponse`'s fields, including the nested
    `"synthesis"` key `Orchestrator._fuse_with_synthesis` adds — `model_
    validate` maps it without re-declaring each field name here, same
    pattern as `document/routes.py._to_analysis_response` (Sprint 39)."""
    return CaseAnalysisResponse(
        case_id=case_id,
        result=CaseAnalysisResultResponse.model_validate(output.result),
        citations=[
            CitationResponse(
                source_id=c.source_id,
                connector=c.connector,
                excerpt=c.excerpt,
                reference=c.reference,
            )
            for c in output.citations
        ],
        confidence=output.confidence.value,
        warnings=output.warnings,
    )


@router.post("/{case_id}/profile", response_model=CaseProfileResponse, status_code=201)
def create_profile(
    case_id: str,
    payload: CaseProfileCreateRequest,
    firm_id: uuid.UUID = Depends(get_current_firm_id),
    session: Session = Depends(get_db_session),
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
) -> CaseProfileResponse:
    owned_case_id = _resolve_owned_case_id(case_id, firm_id, session)
    profile = workflow.case_store.get_or_create(owned_case_id, title=payload.title)
    return _to_response(profile)


@router.get("/{case_id}/profile", response_model=CaseProfileResponse)
def get_profile(
    case_id: str,
    firm_id: uuid.UUID = Depends(get_current_firm_id),
    session: Session = Depends(get_db_session),
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
) -> CaseProfileResponse:
    owned_case_id = _resolve_owned_case_id(case_id, firm_id, session)
    return _to_response(_get_profile_or_404(owned_case_id, workflow))


@router.patch("/{case_id}/profile", response_model=CaseProfileResponse)
def update_profile(
    case_id: str,
    payload: CaseProfileUpdateRequest,
    firm_id: uuid.UUID = Depends(get_current_firm_id),
    session: Session = Depends(get_db_session),
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
) -> CaseProfileResponse:
    owned_case_id = _resolve_owned_case_id(case_id, firm_id, session)
    profile = _get_profile_or_404(owned_case_id, workflow)
    if payload.title is not None:
        profile.title = payload.title
    profile.updated_at = datetime.now(UTC)
    workflow.case_store.save(profile)
    return _to_response(profile)


@router.delete("/{case_id}/profile", status_code=204)
def soft_delete_profile(
    case_id: str,
    firm_id: uuid.UUID = Depends(get_current_firm_id),
    session: Session = Depends(get_db_session),
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
) -> None:
    owned_case_id = _resolve_owned_case_id(case_id, firm_id, session)
    profile = _get_profile_or_404(owned_case_id, workflow)
    profile.is_deleted = True
    profile.updated_at = datetime.now(UTC)
    workflow.case_store.save(profile)


@router.get("/{case_id}/timeline", response_model=list[TimelineEntryResponse])
def get_timeline(
    case_id: str,
    firm_id: uuid.UUID = Depends(get_current_firm_id),
    session: Session = Depends(get_db_session),
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
) -> list[TimelineEntryResponse]:
    owned_case_id = _resolve_owned_case_id(case_id, firm_id, session)
    profile = _get_profile_or_404(owned_case_id, workflow)
    return [
        TimelineEntryResponse(
            date=e.date,
            description=e.description,
            document_ids=list(e.document_ids),
            confidence=e.confidence,
        )
        for e in profile.timeline
    ]


@router.get("/{case_id}/summary", response_model=CaseSummaryResponse)
async def get_summary(
    case_id: str,
    firm_id: uuid.UUID = Depends(get_current_firm_id),
    session: Session = Depends(get_db_session),
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
) -> CaseSummaryResponse:
    owned_case_id = _resolve_owned_case_id(case_id, firm_id, session)
    _get_profile_or_404(owned_case_id, workflow)
    summary = await workflow.summarize(owned_case_id)
    return CaseSummaryResponse(
        executive_summary=summary.executive_summary,
        chronological_summary=summary.chronological_summary,
        documentary_summary=summary.documentary_summary,
        case_status=summary.case_status,
        open_points=list(summary.open_points),
    )


@router.get("/{case_id}/search", response_model=list[CaseSearchResultResponse])
async def search_case(
    case_id: str,
    q: str,
    firm_id: uuid.UUID = Depends(get_current_firm_id),
    session: Session = Depends(get_db_session),
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
) -> list[CaseSearchResultResponse]:
    owned_case_id = _resolve_owned_case_id(case_id, firm_id, session)
    _get_profile_or_404(owned_case_id, workflow)
    results = await workflow.search_engine.search(q)
    return [
        CaseSearchResultResponse(kind=r.kind.value, id=r.id, label=r.label, score=r.score)
        for r in results
    ]


@router.get("/{case_id}/analysis", response_model=CaseAnalysisResponse)
async def get_analysis(
    case_id: str,
    document_id: str | None = None,
    firm_id: uuid.UUID = Depends(get_current_firm_id),
    session: Session = Depends(get_db_session),
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
    orchestrator: Orchestrator = Depends(get_orchestrator),
) -> CaseAnalysisResponse:
    owned_case_id = _resolve_owned_case_id(case_id, firm_id, session)
    _get_profile_or_404(owned_case_id, workflow)

    context: dict[str, object] = {}
    if document_id is not None:
        context["document_id"] = document_id

    output = await orchestrator.run(
        AgentInput(
            task_id=uuid.uuid4(),
            case_id=owned_case_id,
            context=context,
        )
    )
    return _to_analysis_response(owned_case_id, output)
