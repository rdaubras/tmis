from pydantic import BaseModel


class WatchRequest(BaseModel):
    query: str
    connectors: list[str] | None = None
    known_result_ids: list[str] | None = None
    case_id: str | None = None


class WatchResultItemResponse(BaseModel):
    id: str
    title: str
    excerpt: str
    connector: str
    document_type: str
    reference: str
    date: str | None
    score: float


class WatchResultResponse(BaseModel):
    search_id: str | None
    query: str | None
    connectors_used: list[str]
    result_ids: list[str]
    new_results: list[WatchResultItemResponse]
    alert_message: str | None
    model: str | None


class CitationResponse(BaseModel):
    source_id: str
    connector: str
    excerpt: str
    reference: str


class WatchResponse(BaseModel):
    result: WatchResultResponse
    citations: list[CitationResponse]
    confidence: str
    warnings: list[str]
