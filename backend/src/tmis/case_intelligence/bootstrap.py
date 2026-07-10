from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.summaries.generator import CaseSummaryGenerator
from tmis.case_intelligence.workflow.case_workflow import CaseIntelligenceWorkflow
from tmis.document_intelligence.bootstrap import get_document_pipeline


@lru_cache
def get_case_intelligence_workflow() -> CaseIntelligenceWorkflow:
    """Process-wide `CaseIntelligenceWorkflow` singleton, subscribed to
    the shared `EventBus` so every document processed through
    `get_document_pipeline()` automatically re-enriches its case (see
    docs/19-case-intelligence.md)."""
    kernel = get_kernel()
    pipeline = get_document_pipeline()
    return CaseIntelligenceWorkflow(
        document_store=pipeline.document_store,
        event_bus=kernel.event_bus,
        summary_generator=CaseSummaryGenerator(kernel),
    )
