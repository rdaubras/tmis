from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.cases.adapters.sqlalchemy_store import SQLAlchemyCaseStore
from tmis.case_intelligence.cases.ports import CaseStorePort
from tmis.case_intelligence.summaries.generator import CaseSummaryGenerator
from tmis.case_intelligence.workflow.case_workflow import CaseIntelligenceWorkflow
from tmis.document_intelligence.bootstrap import get_document_pipeline


@lru_cache
def get_case_store() -> CaseStorePort:
    """Process-wide `CaseStorePort` singleton (Sprint 43), replacing the
    `InMemoryCaseStore` that `get_case_intelligence_workflow()` used to build
    implicitly by not passing a `case_store` — see
    docs/151-architecture-persistance.md. Mirrors the Sprint 37 pattern
    established by `document_intelligence.bootstrap.get_document_store()`:
    every composition root shares the exact same `SQLAlchemyCaseStore`
    instance, so the synchronous `/api/v1/cases/*` endpoints and the Celery
    async path (`core.tasks.case_tasks.trigger_case_workflow_task`) read and
    write the same rows instead of two divergent views of the same case."""
    return SQLAlchemyCaseStore()


@lru_cache
def get_case_intelligence_workflow() -> CaseIntelligenceWorkflow:
    """Process-wide `CaseIntelligenceWorkflow` singleton, subscribed to
    the shared `EventBus` so every document processed through
    `get_document_pipeline()` automatically re-enriches its case (see
    docs/19-case-intelligence.md)."""
    kernel = get_kernel()
    pipeline = get_document_pipeline()
    return CaseIntelligenceWorkflow(
        case_store=get_case_store(),
        document_store=pipeline.document_store,
        event_bus=kernel.event_bus,
        summary_generator=CaseSummaryGenerator(kernel),
    )
