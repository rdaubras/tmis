from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.document_intelligence.pipeline.document_pipeline import DocumentIntelligencePipeline


@lru_cache
def get_document_pipeline() -> DocumentIntelligencePipeline:
    """Process-wide `DocumentIntelligencePipeline` singleton, sharing the
    Kernel's `EventBus` so `CaseIntelligenceWorkflow` can react to
    `DocumentProcessed` events (see docs/19-case-intelligence.md)."""
    return DocumentIntelligencePipeline(event_bus=get_kernel().event_bus)
