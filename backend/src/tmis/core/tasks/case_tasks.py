"""Asynchronous (Celery) triggering of `CaseIntelligenceWorkflow` (Sprint
4) when a document is attached to a case (Sprint 26 Phase 4), firm-scoped
since ADR-CASEINT-01 (docs/19-case-intelligence.md, "case_intelligence"
persistent & isolated slice).

Runs outside the FastAPI process, so it cannot share the app's in-process
`TMISKernel`/`EventBus` singleton — instead it builds a throwaway
`CaseIntelligenceWorkflow` (`auto_subscribe=False`, since there is nothing
long-lived to subscribe to here) and calls `ingest_document()` directly,
against the same `SQLAlchemyDocumentStore`/`SQLAlchemyCaseStore` the API
and `process_document_task` use — never a second storage mechanism.

`firm_id` is now a required first argument (ADR-CASEINT-01: "no enqueue
without firm_id" — the one invariant this slice adds to every future job
this module or any other schedules against a case). Before touching
anything, the task verifies `case_id` actually names a `cases` row owned
by `firm_id` (ADR-CASEINT-02) via the same firm-scoped
`SqlAlchemyCaseRepository` the HTTP routes use — a malformed id, an
unknown case, or a case owned by another firm is rejected and logged, not
silently ignored, and no `CaseProfile` is ever created or touched for it.
"""

import asyncio
import uuid

from tmis.case_intelligence.bootstrap import (
    get_case_graph,
    get_case_search_engine,
    get_case_store,
)
from tmis.case_intelligence.workflow.case_workflow import CaseIntelligenceWorkflow
from tmis.core.database import SessionLocal
from tmis.core.logging import get_logger
from tmis.core.tasks.celery_app import celery_app
from tmis.document_intelligence.bootstrap import get_document_store
from tmis.infrastructure.persistence.repositories import SqlAlchemyCaseRepository

_LOGGER_NAME = "tmis.core.tasks.case_tasks"


@celery_app.task(name="tmis.case_intelligence.ingest_document")  # type: ignore[untyped-decorator]
def trigger_case_workflow_task(firm_id: str, case_id: str, document_id: str) -> str | None:
    logger = get_logger(_LOGGER_NAME)

    try:
        firm_uuid = uuid.UUID(firm_id)
        case_uuid = uuid.UUID(case_id)
    except ValueError:
        logger.warning(
            "case_workflow_task_rejected_malformed_id",
            firm_id=firm_id,
            case_id=case_id,
            document_id=document_id,
        )
        return None

    with SessionLocal() as session:
        case = SqlAlchemyCaseRepository(session).get_by_id(case_uuid, firm_uuid)
    if case is None:
        logger.warning(
            "case_workflow_task_rejected_case_not_owned",
            firm_id=firm_id,
            case_id=case_id,
            document_id=document_id,
        )
        return None

    document_store = get_document_store(firm_uuid)
    record = document_store.get(document_id)
    if record is None:
        raise ValueError(f"No document record for {document_id!r}")

    workflow = CaseIntelligenceWorkflow(
        case_store=get_case_store(firm_uuid),
        knowledge_graph=get_case_graph(firm_uuid),
        search_engine=get_case_search_engine(firm_uuid),
        document_store=document_store,
        auto_subscribe=False,
    )
    profile = asyncio.run(workflow.ingest_document(case_id, record))
    logger.info(
        "case_workflow_triggered", firm_id=firm_id, case_id=case_id, document_id=document_id
    )
    return profile.case_id
