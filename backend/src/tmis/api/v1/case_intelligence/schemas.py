from datetime import datetime

from pydantic import BaseModel


class ActorResponse(BaseModel):
    id: str
    type: str
    name: str
    aliases: list[str]


class FactResponse(BaseModel):
    id: str
    description: str
    confidence: float
    dates: list[str]
    confirming_document_ids: list[str]
    contradicting_document_ids: list[str]


class TimelineEntryResponse(BaseModel):
    date: str
    description: str
    document_ids: list[str]
    confidence: float


class TimelineInconsistencyResponse(BaseModel):
    date: str
    reason: str
    entries: list[TimelineEntryResponse]


class LegalIssueResponse(BaseModel):
    id: str
    description: str
    confidence: float
    status: str


class CaseProfileResponse(BaseModel):
    case_id: str
    title: str
    is_deleted: bool
    document_ids: list[str]
    actors: list[ActorResponse]
    facts: list[FactResponse]
    legal_issues: list[LegalIssueResponse]
    updated_at: datetime


class CaseProfileCreateRequest(BaseModel):
    title: str


class CaseProfileUpdateRequest(BaseModel):
    title: str | None = None


class CaseSummaryResponse(BaseModel):
    executive_summary: str
    chronological_summary: str
    documentary_summary: str
    case_status: str
    open_points: list[str]


class CaseSearchResultResponse(BaseModel):
    kind: str
    id: str
    label: str
    score: float


class CitationResponse(BaseModel):
    source_id: str
    connector: str
    excerpt: str
    reference: str


class CaseAnalysisSynthesisResponse(BaseModel):
    """`SynthesisAgent.run()`'s own `result` shape (see
    `agents/synthesis_agent.py`), nested under the `"synthesis"` key that
    `Orchestrator._fuse_with_synthesis` adds to the Analysis/Verifier
    result — never flattened into it."""

    executive_summary: str
    chronological_summary: str
    documentary_summary: str
    case_status: str
    open_points: list[str]
    table: dict[str, list[dict[str, object]]]
    fact_sheet: dict[str, object]
    checklist: list[dict[str, object]]
    synthesis_note: str
    model: str


class CaseAnalysisResultResponse(BaseModel):
    """`AnalysisAgent.run()`'s own `result` keys (`entities`,
    `inconsistencies`, `timeline`) plus the `synthesis` key fused in by
    the Orchestrator. `narrative`/`model` are optional: `AnalysisAgent`
    omits both when no `document_id` was provided (see
    `agents/analysis_agent.py`)."""

    entities: dict[str, list[dict[str, object]]]
    inconsistencies: list[dict[str, object]]
    timeline: list[dict[str, object]]
    narrative: str | None = None
    model: str | None = None
    synthesis: CaseAnalysisSynthesisResponse


class CaseAnalysisResponse(BaseModel):
    case_id: str
    result: CaseAnalysisResultResponse
    citations: list[CitationResponse]
    confidence: str
    warnings: list[str]
