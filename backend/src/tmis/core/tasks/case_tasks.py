"""Asynchronous (Celery) triggering of `CaseIntelligenceWorkflow` (Sprint
4) when a document is attached to a case (Sprint 26 Phase 4).

Runs outside the FastAPI process, so it cannot share the app's in-process
`TMISKernel`/`EventBus` singleton — instead it builds a throwaway
`CaseIntelligenceWorkflow` (`auto_subscribe=False`, since there is nothing
long-lived to subscribe to here) and calls `ingest_document()` directly,
against the same `SQLAlchemyDocumentStore`/`SQLAlchemyCaseStore` the API
and `process_document_task` use — never a second storage mechanism.

`case_intelligence.bootstrap.get_case_store()` (Sprint 43) is used here
instead of a fresh `SQLAlchemyCaseStore()` so this worker-process
singleton and the FastAPI process's `get_case_intelligence_workflow()`
converge on the exact same store wiring pattern (both read/write the same
`case_profiles` table either way — the point of Sprint 43 is that neither
one falls back to `InMemoryCaseStore` any more, not that they share one
Python object across processes, which Celery workers never do).
"""

import asyncio

from tmis.case_intelligence.bootstrap import get_case_store
from tmis.case_intelligence.workflow.case_workflow import CaseIntelligenceWorkflow
from tmis.core.logging import get_logger
from tmis.core.tasks.celery_app import celery_app
from tmis.document_intelligence.adapters.sqlalchemy_store import SQLAlchemyDocumentStore

_LOGGER_NAME = "tmis.core.tasks.case_tasks"


@celery_app.task(name="tmis.case_intelligence.ingest_document")  # type: ignore[untyped-decorator]
def trigger_case_workflow_task(case_id: str, document_id: str) -> str:
    logger = get_logger(_LOGGER_NAME)
    document_store = SQLAlchemyDocumentStore()
    record = document_store.get(document_id)
    if record is None:
        raise ValueError(f"No document record for {document_id!r}")

    workflow = CaseIntelligenceWorkflow(
        case_store=get_case_store(),
        document_store=document_store,
        auto_subscribe=False,
    )
    profile = asyncio.run(workflow.ingest_document(case_id, record))
    logger.info("case_workflow_triggered", case_id=case_id, document_id=document_id)
    return profile.case_id
