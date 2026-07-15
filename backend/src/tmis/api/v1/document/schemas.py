from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    task_id: str
    status: str


class DocumentVersionResponse(BaseModel):
    version: int
    filename: str
    status: str
    previous_version_id: str | None


class DocumentSummaryResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    ocr_text: str
    warnings: list[str]


class ClauseFindingResponse(BaseModel):
    clause_id: str
    clause_type: str
    title: str
    status: str
    matched_variant_id: str | None
    risk_notes: str | None
    jurisprudence_refs: list[str]


class ParagraphChangeResponse(BaseModel):
    before: str
    after: str


class ContractVersionDiffResponse(BaseModel):
    added_paragraphs: list[str]
    removed_paragraphs: list[str]
    changed_paragraphs: list[ParagraphChangeResponse]


class ContractAnalysisResultResponse(BaseModel):
    clauses: list[ClauseFindingResponse]
    version_diff: ContractVersionDiffResponse | None
    synthesis: str | None
    model: str | None


class CitationResponse(BaseModel):
    source_id: str
    connector: str
    excerpt: str
    reference: str


class ContractAnalysisResponse(BaseModel):
    document_id: str
    result: ContractAnalysisResultResponse
    citations: list[CitationResponse]
    confidence: str
    warnings: list[str]
