from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from tmis.api.v1.case_intelligence.schemas import (
    ActorResponse,
    CaseProfileCreateRequest,
    CaseProfileResponse,
    CaseProfileUpdateRequest,
    CaseSearchResultResponse,
    CaseSummaryResponse,
    FactResponse,
    LegalIssueResponse,
    TimelineEntryResponse,
)
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.workflow.case_workflow import CaseIntelligenceWorkflow

router = APIRouter(prefix="/cases", tags=["case-intelligence"])


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


@router.post("/{case_id}/profile", response_model=CaseProfileResponse, status_code=201)
def create_profile(
    case_id: str,
    payload: CaseProfileCreateRequest,
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
) -> CaseProfileResponse:
    profile = workflow.case_store.get_or_create(case_id, title=payload.title)
    return _to_response(profile)


@router.get("/{case_id}/profile", response_model=CaseProfileResponse)
def get_profile(
    case_id: str, workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow)
) -> CaseProfileResponse:
    return _to_response(_get_profile_or_404(case_id, workflow))


@router.patch("/{case_id}/profile", response_model=CaseProfileResponse)
def update_profile(
    case_id: str,
    payload: CaseProfileUpdateRequest,
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
) -> CaseProfileResponse:
    profile = _get_profile_or_404(case_id, workflow)
    if payload.title is not None:
        profile.title = payload.title
    profile.updated_at = datetime.now(UTC)
    workflow.case_store.save(profile)
    return _to_response(profile)


@router.delete("/{case_id}/profile", status_code=204)
def soft_delete_profile(
    case_id: str, workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow)
) -> None:
    profile = _get_profile_or_404(case_id, workflow)
    profile.is_deleted = True
    profile.updated_at = datetime.now(UTC)
    workflow.case_store.save(profile)


@router.get("/{case_id}/timeline", response_model=list[TimelineEntryResponse])
def get_timeline(
    case_id: str, workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow)
) -> list[TimelineEntryResponse]:
    profile = _get_profile_or_404(case_id, workflow)
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
    case_id: str, workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow)
) -> CaseSummaryResponse:
    _get_profile_or_404(case_id, workflow)
    summary = await workflow.summarize(case_id)
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
    workflow: CaseIntelligenceWorkflow = Depends(get_case_intelligence_workflow),
) -> list[CaseSearchResultResponse]:
    _get_profile_or_404(case_id, workflow)
    results = await workflow.search_engine.search(q)
    return [
        CaseSearchResultResponse(kind=r.kind.value, id=r.id, label=r.label, score=r.score)
        for r in results
    ]
