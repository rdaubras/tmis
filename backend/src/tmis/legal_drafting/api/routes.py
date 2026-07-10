from fastapi import APIRouter, Depends, HTTPException, Response

from tmis.legal_drafting.api.schemas import (
    CreateDraftRequest,
    DraftCitationResponse,
    DraftResponse,
    HistoryEntryResponse,
    ParagraphResponse,
    ReviewFindingResponse,
    SectionResponse,
    ValidateDraftRequest,
    ValidationRecordResponse,
    VersionDiffResponse,
    VersionResponse,
)
from tmis.legal_drafting.bootstrap import get_document_orchestrator
from tmis.legal_drafting.documents.orchestrator import DocumentOrchestrator
from tmis.legal_drafting.documents.schemas import Document
from tmis.legal_drafting.export.schemas import ExportFormat
from tmis.legal_drafting.templates.schemas import DocumentType
from tmis.legal_drafting.validation.schemas import DraftDecision

router = APIRouter(prefix="/legal-drafting", tags=["legal-drafting"])


def _to_draft_response(document: Document) -> DraftResponse:
    return DraftResponse(
        id=document.id,
        template_id=document.template_id,
        document_type=document.document_type.value,
        case_id=document.case_id,
        title=document.title,
        is_draft=document.is_draft,
        status=document.status.value,
        sections=[
            SectionResponse(
                id=section.id,
                key=section.key,
                title=section.title,
                order=section.order,
                depends_on=list(section.depends_on),
                paragraphs=[
                    ParagraphResponse(
                        id=p.id,
                        section_key=p.section_key,
                        order=p.order,
                        text=p.text,
                        origin=p.origin,
                        fact_ids=list(p.fact_ids),
                        reference_ids=list(p.reference_ids),
                        evidence_ids=list(p.evidence_ids),
                        hypothesis_ids=list(p.hypothesis_ids),
                    )
                    for p in section.paragraphs
                ],
            )
            for section in document.sections
        ],
        citations=[
            DraftCitationResponse(
                id=c.id,
                document_id=c.document_id,
                section_id=c.section_id,
                paragraph_id=c.paragraph_id,
                source_type=c.source_type,
                source_id=c.source_id,
                reference=c.reference,
                excerpt=c.excerpt,
            )
            for c in document.citations
        ],
        review_findings=[
            ReviewFindingResponse(
                id=f.id,
                type=f.type.value,
                description=f.description,
                section_id=f.section_id,
                paragraph_id=f.paragraph_id,
            )
            for f in document.review_findings
        ],
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def _parse_document_type(raw: str) -> DocumentType:
    try:
        return DocumentType(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown document type: {raw!r}") from exc


@router.post("/drafts", response_model=DraftResponse)
async def create_draft(
    payload: CreateDraftRequest,
    orchestrator: DocumentOrchestrator = Depends(get_document_orchestrator),
) -> DraftResponse:
    document_type = _parse_document_type(payload.document_type)
    document = await orchestrator.create_draft(
        document_type,
        case_id=payload.case_id,
        question=payload.question,
        reasoning_session_id=payload.reasoning_session_id,
        style_profile_id=payload.style_profile_id,
        variables=payload.variables,
    )
    return _to_draft_response(document)


@router.get("/drafts/{document_id}", response_model=DraftResponse)
def get_draft(
    document_id: str,
    orchestrator: DocumentOrchestrator = Depends(get_document_orchestrator),
) -> DraftResponse:
    document = orchestrator.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"No draft found for {document_id!r}")
    return _to_draft_response(document)


@router.post(
    "/drafts/{document_id}/sections/{section_key}/regenerate", response_model=DraftResponse
)
async def regenerate_section(
    document_id: str,
    section_key: str,
    orchestrator: DocumentOrchestrator = Depends(get_document_orchestrator),
) -> DraftResponse:
    try:
        document = await orchestrator.regenerate_section(document_id, section_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_draft_response(document)


@router.post(
    "/drafts/{document_id}/sections/{section_key}/paragraphs/{paragraph_id}/regenerate",
    response_model=DraftResponse,
)
async def regenerate_paragraph(
    document_id: str,
    section_key: str,
    paragraph_id: str,
    orchestrator: DocumentOrchestrator = Depends(get_document_orchestrator),
) -> DraftResponse:
    try:
        document = await orchestrator.regenerate_paragraph(document_id, section_key, paragraph_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_draft_response(document)


@router.get("/drafts/{document_id}/versions", response_model=list[VersionResponse])
def list_versions(
    document_id: str,
    orchestrator: DocumentOrchestrator = Depends(get_document_orchestrator),
) -> list[VersionResponse]:
    return [
        VersionResponse(
            id=v.id,
            document_id=v.document_id,
            version_number=v.version_number,
            author=v.author,
            created_at=v.created_at,
            paragraph_count=sum(len(s.paragraphs) for s in v.sections),
        )
        for v in orchestrator.list_versions(document_id)
    ]


@router.get("/drafts/{document_id}/versions/compare", response_model=VersionDiffResponse)
def compare_versions(
    document_id: str,
    version_a: int,
    version_b: int,
    orchestrator: DocumentOrchestrator = Depends(get_document_orchestrator),
) -> VersionDiffResponse:
    try:
        diff = orchestrator.compare_versions(document_id, version_a, version_b)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return VersionDiffResponse(
        version_a=diff.version_a,
        version_b=diff.version_b,
        added_paragraph_ids=list(diff.added_paragraph_ids),
        removed_paragraph_ids=list(diff.removed_paragraph_ids),
        changed_paragraph_ids=list(diff.changed_paragraph_ids),
    )


@router.post(
    "/drafts/{document_id}/versions/{version_number}/restore", response_model=DraftResponse
)
def restore_version(
    document_id: str,
    version_number: int,
    author: str = "avocat",
    orchestrator: DocumentOrchestrator = Depends(get_document_orchestrator),
) -> DraftResponse:
    try:
        document = orchestrator.restore_version(document_id, version_number, author)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_draft_response(document)


@router.post("/drafts/{document_id}/validate", response_model=ValidationRecordResponse)
def validate_draft(
    document_id: str,
    payload: ValidateDraftRequest,
    orchestrator: DocumentOrchestrator = Depends(get_document_orchestrator),
) -> ValidationRecordResponse:
    try:
        decision = DraftDecision(payload.decision)
    except ValueError as exc:
        detail = f"Unknown decision: {payload.decision!r}"
        raise HTTPException(status_code=400, detail=detail) from exc
    try:
        record = orchestrator.validate(document_id, decision, payload.author, payload.comment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ValidationRecordResponse(
        id=record.id,
        document_id=record.document_id,
        decision=record.decision.value,
        author=record.author,
        comment=record.comment,
        created_at=record.created_at,
    )


@router.get("/drafts/{document_id}/review", response_model=list[ReviewFindingResponse])
def get_review(
    document_id: str,
    orchestrator: DocumentOrchestrator = Depends(get_document_orchestrator),
) -> list[ReviewFindingResponse]:
    try:
        findings = orchestrator.review(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        ReviewFindingResponse(
            id=f.id, type=f.type.value, description=f.description,
            section_id=f.section_id, paragraph_id=f.paragraph_id,
        )
        for f in findings
    ]


@router.get("/drafts/{document_id}/history", response_model=list[HistoryEntryResponse])
def get_history(
    document_id: str,
    orchestrator: DocumentOrchestrator = Depends(get_document_orchestrator),
) -> list[HistoryEntryResponse]:
    return [
        HistoryEntryResponse(
            id=e.id, document_id=e.document_id, action=e.action.value,
            author=e.author, timestamp=e.timestamp, details=e.details,
        )
        for e in orchestrator.history(document_id)
    ]


@router.get("/drafts/{document_id}/export")
def export_draft(
    document_id: str,
    format: str = "html",
    orchestrator: DocumentOrchestrator = Depends(get_document_orchestrator),
) -> Response:
    try:
        export_format = ExportFormat(format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown export format: {format!r}") from exc
    try:
        result = orchestrator.export(document_id, export_format)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=result.content,
        media_type=result.media_type,
        headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
    )
