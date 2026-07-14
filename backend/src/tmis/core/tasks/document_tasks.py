"""Asynchronous (Celery) execution of `DocumentIntelligencePipeline`
(Sprint 3) for a document already persisted by the upload API (Sprint 26
Phase 4).

The API endpoint persists the initial (pre-pipeline) `DocumentRecord` via
`SQLAlchemyDocumentStore` synchronously (so the upload response can return
a real `document_id` immediately), then enqueues this task. The task
re-fetches the raw bytes from that same row, runs the pipeline (which is
itself `async def`; a Celery task is a plain sync callable, so it drives
the coroutine with `asyncio.run`), and — because `document_store.save()`
never overwrites in place (see
`tmis.document_intelligence.adapters.sqlalchemy_store`) — the pipeline's
own final save produces the next version of the same document, not a
second document.
"""

import asyncio

from tmis.core.logging import get_logger
from tmis.core.tasks.celery_app import celery_app
from tmis.document_intelligence.adapters.sqlalchemy_store import SQLAlchemyDocumentStore
from tmis.document_intelligence.pipeline.document_pipeline import DocumentIntelligencePipeline

_LOGGER_NAME = "tmis.core.tasks.document_tasks"


@celery_app.task(name="tmis.document_intelligence.process_document")  # type: ignore[untyped-decorator]
def process_document_task(
    document_id: str, filename: str, content_type: str, case_id: str | None = None
) -> str:
    logger = get_logger(_LOGGER_NAME)
    document_store = SQLAlchemyDocumentStore()
    initial = document_store.get(document_id)
    if initial is None:
        raise ValueError(f"No document record for {document_id!r}")

    pipeline = DocumentIntelligencePipeline(document_store=document_store)
    processed = asyncio.run(
        pipeline.process(
            filename,
            content_type,
            initial.raw_bytes,
            document_id=document_id,
            case_id=case_id,
        )
    )
    logger.info("document_pipeline_completed", document_id=processed.document_id)

    if case_id is not None:
        from tmis.core.tasks.case_tasks import trigger_case_workflow_task

        trigger_case_workflow_task.delay(case_id, processed.document_id)

    return processed.document_id
