from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.document_intelligence.adapters.sqlalchemy_store import SQLAlchemyDocumentStore
from tmis.document_intelligence.pipeline.document_pipeline import DocumentIntelligencePipeline
from tmis.document_intelligence.storage.ports import DocumentStorePort


@lru_cache
def get_document_store() -> DocumentStorePort:
    """Process-wide `DocumentStorePort` singleton (Sprint 37). Unlike the
    LRE connectors (real HTTP vs. fixture, a configuration choice),
    `SQLAlchemyDocumentStore` is always the production implementation of
    this port — it reads `Settings.database_url` directly, there is no
    real/fixture branch to choose between. Every entry point that used
    to construct its own store (this module's own pipeline default,
    `Orchestrator`'s `AnalysisAgent`, `agents.bootstrap.
    get_contract_agent()`) now shares this one instance instead — see
    docs/151-architecture-persistance.md."""
    return SQLAlchemyDocumentStore()


@lru_cache
def get_document_pipeline() -> DocumentIntelligencePipeline:
    """Process-wide `DocumentIntelligencePipeline` singleton, sharing the
    Kernel's `EventBus` so `CaseIntelligenceWorkflow` can react to
    `DocumentProcessed` events (see docs/19-case-intelligence.md), and
    the shared `DocumentStorePort` singleton (Sprint 37) rather than the
    pipeline's own in-memory default."""
    return DocumentIntelligencePipeline(
        event_bus=get_kernel().event_bus, document_store=get_document_store()
    )
