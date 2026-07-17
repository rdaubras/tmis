"""Asynchronous (Celery) execution of `DocumentIntelligencePipeline`
(Sprint 3) for a document already persisted by the upload API (Sprint 26
Phase 4), firm-scoped since ADR-DOCINT-01 (docs/14-document-intelligence.md,
"document_intelligence" persistent & isolated slice).

The API endpoint persists the initial (pre-pipeline) `DocumentRecord` via
a firm-scoped `SQLAlchemyDocumentStore` synchronously (so the upload
response can return a real `document_id` immediately), then enqueues this
task. The task re-fetches the raw bytes from that same row, runs the
pipeline (which is itself `async def`; a Celery task is a plain sync
callable, so it drives the coroutine with `asyncio.run`), and — because
`document_store.save()` never overwrites in place (see
`tmis.document_intelligence.adapters.sqlalchemy_store`) — the pipeline's
own final save produces the next version of the same document, not a
second document.

`firm_id` is now a required argument (ADR-DOCINT-01: "no processing
without firm_id" — the document store cannot be built at all otherwise).
It is always available at the upload route, since every request already
passes through the auth boundary; a caller invoking this task without one
is a programming error, not a legitimate anonymous-tenant path, so it is
rejected loudly (`ValueError`) rather than silently guessed. The same
`firm_id` also reaches `trigger_case_workflow_task` (ADR-CASEINT-01) so
the case_intelligence side of this async path is never entered without
tenant context either.

Builds its own `DocumentIntelligencePipeline` directly (via `tmis.
document_intelligence.bootstrap.get_document_store`/`get_document_
knowledge_graph`, not `get_document_pipeline`) rather than through the
bootstrap's own pipeline accessor: a Celery worker runs outside the
FastAPI process, so it cannot share the app's in-process `TMISKernel`/
`EventBus` singleton `get_document_pipeline()` wires in — same reasoning
as `trigger_case_workflow_task` building its own throwaway
`CaseIntelligenceWorkflow` instead of calling
`get_case_intelligence_workflow`.
"""

import asyncio
import uuid

from tmis.core.logging import get_logger
from tmis.core.tasks.celery_app import celery_app
from tmis.document_intelligence.bootstrap import get_document_knowledge_graph, get_document_store
from tmis.document_intelligence.pipeline.document_pipeline import DocumentIntelligencePipeline

_LOGGER_NAME = "tmis.core.tasks.document_tasks"


@celery_app.task(name="tmis.document_intelligence.process_document")  # type: ignore[untyped-decorator]
def process_document_task(
    document_id: str,
    filename: str,
    content_type: str,
    case_id: str | None = None,
    firm_id: str | None = None,
) -> str:
    logger = get_logger(_LOGGER_NAME)
    if firm_id is None:
        logger.warning("document_pipeline_task_rejected_no_firm_id", document_id=document_id)
        raise ValueError(
            f"process_document_task requires firm_id (ADR-DOCINT-01): document "
            f"{document_id!r} cannot be processed without a tenant."
        )
    # Normalized to `uuid.UUID` once, here — `get_document_knowledge_graph`
    # is `lru_cache`d and keyed on this exact argument, so a caller
    # passing the string form of the same firm and a caller passing the
    # `uuid.UUID` form (as every in-process accessor call does, e.g.
    # `agents.bootstrap`) would otherwise land two different cache
    # entries for the same firm.
    firm_uuid = uuid.UUID(firm_id)

    document_store = get_document_store(firm_uuid)
    initial = document_store.get(document_id)
    if initial is None:
        raise ValueError(f"No document record for {document_id!r}")

    pipeline = DocumentIntelligencePipeline(
        document_store=document_store,
        knowledge_graph=get_document_knowledge_graph(firm_uuid),
    )
    processed = asyncio.run(
        pipeline.process(
            filename,
            content_type,
            initial.raw_bytes,
            document_id=document_id,
            case_id=case_id,
            firm_id=firm_id,
        )
    )
    logger.info("document_pipeline_completed", document_id=processed.document_id)

    if case_id is not None:
        from tmis.core.tasks.case_tasks import trigger_case_workflow_task

        trigger_case_workflow_task.delay(firm_id, case_id, processed.document_id)

    return processed.document_id
