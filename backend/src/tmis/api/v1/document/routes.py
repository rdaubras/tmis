"""Document upload API (Sprint 26 Phase 4): persists via the shared
`DocumentStorePort` singleton (`tmis.document_intelligence.bootstrap.
get_document_store()`, always `SQLAlchemyDocumentStore` in practice —
Sprint 37), then triggers `DocumentIntelligencePipeline` asynchronously
via Celery — see `tmis.core.tasks.document_tasks`.

`GET /{document_id}/versions` is the one place in this router that reads
via `tmis.core.db.session.AsyncSessionLocal` (the async engine) directly
against `DocumentRecordModel`, instead of through `DocumentStorePort`:
that port only ever exposes the latest version (see
`tmis.document_intelligence.storage.ports.DocumentStorePort`), it has no
"list every version" method, so this read has no port to go through in
the first place — see docs/151-architecture-persistance.md.

`GET /{document_id}/analysis` (Sprint 39) exposes `ContractAgent`
(already real since Sprint 35) as a fourth route on this same resource —
a computed read triggered on demand, following the precedent set by
`GET /cases/{case_id}/summary` (Sprint 19), not a second router — see
docs/166-architecture-exposition-agent-contrats.md.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select

from tmis.agents.bootstrap import get_contract_agent
from tmis.agents.contract_agent import ContractAgent
from tmis.agents.contracts import AgentInput
from tmis.ai.schemas.agent import AgentOutput
from tmis.api.deps import get_current_firm_id
from tmis.api.v1.document.schemas import (
    CitationResponse,
    ContractAnalysisResponse,
    ContractAnalysisResultResponse,
    DocumentSummaryResponse,
    DocumentUploadResponse,
    DocumentVersionResponse,
)
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain
from tmis.core.db.session import AsyncSessionLocal
from tmis.core.tasks.document_tasks import process_document_task
from tmis.document_intelligence.adapters.sqlalchemy_store import DocumentRecordModel
from tmis.document_intelligence.bootstrap import get_document_store
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.record import DocumentRecord

router = APIRouter(prefix="/documents", tags=["document"])


def _to_analysis_response(document_id: str, output: AgentOutput) -> ContractAnalysisResponse:
    """`output.result` is `dict[str, object]` (the common `AgentOutput` contract,
    see `tmis.ai.schemas.agent`) but its actual shape is exactly
    `ContractAnalysisResultResponse`'s fields (`ContractAgent.run()`, confirmed
    in Phase 0) — `model_validate` maps it (including the nested `version_diff`
    and `clauses` dicts) without re-declaring each field name here."""
    return ContractAnalysisResponse(
        document_id=document_id,
        result=ContractAnalysisResultResponse.model_validate(output.result),
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


@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    case_id: str | None = Form(default=None),
    firm_id: uuid.UUID = Depends(get_current_firm_id),
) -> DocumentUploadResponse:
    raw_bytes = await file.read()
    filename = file.filename or "unnamed"
    document_id = str(uuid.uuid4())

    store = get_document_store()
    store.save(
        DocumentRecord(
            document_id=document_id,
            filename=filename,
            status=ProcessingStatus.RECEIVED,
            raw_bytes=raw_bytes,
        )
    )

    task = process_document_task.delay(
        document_id,
        filename,
        file.content_type or "application/octet-stream",
        case_id,
        str(firm_id),
    )

    return DocumentUploadResponse(
        document_id=document_id, task_id=task.id, status=ProcessingStatus.RECEIVED.value
    )


@router.get("/{document_id}", response_model=DocumentSummaryResponse)
def get_document(document_id: str) -> DocumentSummaryResponse:
    record = get_document_store().get(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No document {document_id!r}")
    return DocumentSummaryResponse(
        document_id=record.document_id,
        filename=record.filename,
        status=record.status.value,
        ocr_text=record.ocr_text,
        warnings=list(record.warnings),
    )


@router.get("/{document_id}/versions", response_model=list[DocumentVersionResponse])
async def list_document_versions(document_id: str) -> list[DocumentVersionResponse]:
    async with AsyncSessionLocal() as session:
        rows = (
            (
                await session.execute(
                    select(DocumentRecordModel)
                    .where(DocumentRecordModel.document_id == document_id)
                    .order_by(DocumentRecordModel.version.asc())
                )
            )
            .scalars()
            .all()
        )
        if not rows:
            raise HTTPException(status_code=404, detail=f"No document {document_id!r}")
        return [
            DocumentVersionResponse(
                version=row.version,
                filename=row.filename,
                status=row.status,
                previous_version_id=(
                    str(row.previous_version_id) if row.previous_version_id else None
                ),
            )
            for row in rows
        ]


@router.get("/{document_id}/analysis", response_model=ContractAnalysisResponse)
async def analyze_document(
    document_id: str,
    domain: LegalDomain | None = None,
    compare_document_id: str | None = None,
    case_id: str | None = None,
    contract_agent: ContractAgent = Depends(get_contract_agent),
) -> ContractAnalysisResponse:
    record = get_document_store().get(document_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No document {document_id!r}")

    if record.status is not ProcessingStatus.PROCESSED:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Document {document_id!r} has not completed processing yet "
                f"(status={record.status.value!r}): no OCR text is available to analyze."
            ),
        )

    context: dict[str, object] = {"document_id": document_id}
    if domain is not None:
        context["domain"] = domain.value
    if compare_document_id is not None:
        context["compare_document_id"] = compare_document_id

    output = await contract_agent.run(
        AgentInput(task_id=uuid.uuid4(), case_id=case_id, context=context)
    )

    return _to_analysis_response(document_id, output)
