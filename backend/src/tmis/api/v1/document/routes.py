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
"""

import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import select

from tmis.api.v1.document.schemas import (
    DocumentSummaryResponse,
    DocumentUploadResponse,
    DocumentVersionResponse,
)
from tmis.core.db.session import AsyncSessionLocal
from tmis.core.tasks.document_tasks import process_document_task
from tmis.document_intelligence.adapters.sqlalchemy_store import DocumentRecordModel
from tmis.document_intelligence.bootstrap import get_document_store
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.record import DocumentRecord

router = APIRouter(prefix="/documents", tags=["document"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    case_id: str | None = Form(default=None),
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
        document_id, filename, file.content_type or "application/octet-stream", case_id
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
