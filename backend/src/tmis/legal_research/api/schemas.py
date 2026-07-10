from datetime import datetime

from pydantic import BaseModel


class ResearchSearchRequest(BaseModel):
    query: str
    connector_names: list[str] | None = None
    filters: dict[str, str] | None = None
    user_id: str | None = None
    case_id: str | None = None


class ResearchResultResponse(BaseModel):
    id: str
    title: str
    excerpt: str
    connector: str
    document_type: str
    reference: str
    date: str | None
    lexical_score: float
    vector_score: float
    authority_score: float
    freshness_score: float
    final_score: float


class ResearchCitationResponse(BaseModel):
    source_id: str
    title: str
    date: str | None
    document_type: str
    reference: str
    excerpt: str


class ResearchSearchResponse(BaseModel):
    search_id: str
    query: str
    results: list[ResearchResultResponse]
    citations: list[ResearchCitationResponse]
    connectors_used: list[str]
    duration_ms: float
    cache_hit: bool


class ResearchHistoryEntryResponse(BaseModel):
    id: str
    query_text: str
    timestamp: datetime
    connectors_used: list[str]
    duration_ms: float
    result_count: int
    user_id: str | None
    case_id: str | None
