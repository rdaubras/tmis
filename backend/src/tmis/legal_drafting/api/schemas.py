from datetime import datetime

from pydantic import BaseModel


class CreateDraftRequest(BaseModel):
    document_type: str
    case_id: str | None = None
    question: str | None = None
    reasoning_session_id: str | None = None
    style_profile_id: str = "default"
    variables: dict[str, str] | None = None


class ParagraphResponse(BaseModel):
    id: str
    section_key: str
    order: int
    text: str
    origin: str
    fact_ids: list[str]
    reference_ids: list[str]
    evidence_ids: list[str]
    hypothesis_ids: list[str]


class SectionResponse(BaseModel):
    id: str
    key: str
    title: str
    order: int
    paragraphs: list[ParagraphResponse]
    depends_on: list[str]


class DraftCitationResponse(BaseModel):
    id: str
    document_id: str
    section_id: str
    paragraph_id: str
    source_type: str
    source_id: str
    reference: str
    excerpt: str


class ReviewFindingResponse(BaseModel):
    id: str
    type: str
    description: str
    section_id: str | None
    paragraph_id: str | None


class DraftResponse(BaseModel):
    id: str
    template_id: str
    document_type: str
    case_id: str | None
    title: str
    is_draft: bool
    status: str
    sections: list[SectionResponse]
    citations: list[DraftCitationResponse]
    review_findings: list[ReviewFindingResponse]
    created_at: datetime
    updated_at: datetime


class ValidateDraftRequest(BaseModel):
    decision: str
    author: str
    comment: str | None = None


class ValidationRecordResponse(BaseModel):
    id: str
    document_id: str
    decision: str
    author: str
    comment: str | None
    created_at: datetime


class VersionResponse(BaseModel):
    id: str
    document_id: str
    version_number: int
    author: str
    created_at: datetime
    paragraph_count: int


class VersionDiffResponse(BaseModel):
    version_a: int
    version_b: int
    added_paragraph_ids: list[str]
    removed_paragraph_ids: list[str]
    changed_paragraph_ids: list[str]


class HistoryEntryResponse(BaseModel):
    id: str
    document_id: str
    action: str
    author: str | None
    timestamp: datetime
    details: str
