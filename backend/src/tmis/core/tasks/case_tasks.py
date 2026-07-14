"""Asynchronous (Celery) triggering of `CaseIntelligenceWorkflow` (Sprint
4) when a document is attached to a case (Sprint 26 Phase 4).

Runs outside the FastAPI process, so it cannot share the app's in-process
`TMISKernel`/`EventBus` singleton — instead it builds a throwaway
`CaseIntelligenceWorkflow` (`auto_subscribe=False`, since there is nothing
long-lived to subscribe to here) and calls `ingest_document()` directly,
against the same `SQLAlchemyDocumentStore`/`SQLAlchemyCaseStore` the API
and `process_document_task` use — never a second storage mechanism.
"""

import asyncio

from tmis.case_intelligence.cases.adapters.sqlalchemy_store import SQLAlchemyCaseStore
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
        case_store=SQLAlchemyCaseStore(),
        document_store=document_store,
        auto_subscribe=False,
    )
    profile = asyncio.run(workflow.ingest_document(case_id, record))
    logger.info("case_workflow_triggered", case_id=case_id, document_id=document_id)
    return profile.case_id
