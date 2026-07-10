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
