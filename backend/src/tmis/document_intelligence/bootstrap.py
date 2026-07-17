import uuid
from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.document_intelligence.adapters.sqlalchemy_store import SQLAlchemyDocumentStore
from tmis.document_intelligence.knowledge.in_memory_graph import InMemoryKnowledgeGraph
from tmis.document_intelligence.knowledge.ports import KnowledgeGraphPort
from tmis.document_intelligence.pipeline.document_pipeline import DocumentIntelligencePipeline
from tmis.document_intelligence.storage.ports import DocumentStorePort


def get_document_store(firm_id: uuid.UUID | str) -> DocumentStorePort:
    """Firm-scoped `DocumentStorePort` (ADR-DOCINT-01, "document_
    intelligence" persistent & isolated slice, see
    docs/14-document-intelligence.md) — replaces the Sprint 37
    `get_document_store()` singleton, which built one
    `SQLAlchemyDocumentStore` shared by every firm (see
    docs/151-architecture-persistance.md for that earlier state, and
    docs/14-document-intelligence.md § Points de vigilance for why that
    was the most sensitive leak in Axe A: `raw_bytes`, the uploaded file
    itself, lives on this store). There is no longer an agnostic
    `SQLAlchemyDocumentStore`: `firm_id` is mandatory, bound once here, at
    construction. Built fresh on every call — the store itself holds no
    state beyond `firm_id` (every method opens and closes its own
    `Session`), so unlike `get_document_knowledge_graph` below there is
    nothing to cache."""
    return SQLAlchemyDocumentStore(firm_id=firm_id)


@lru_cache
def get_document_knowledge_graph(firm_id: uuid.UUID | str) -> KnowledgeGraphPort:
    """One `InMemoryKnowledgeGraph` per firm, cached for the lifetime of
    the process (T5, docs/14-document-intelligence.md) — `lru_cache`
    keyed by `firm_id` is the partition, mirroring `case_intelligence.
    bootstrap.get_case_graph`: every call for the same firm returns the
    exact same graph instance, while two different firms never share
    one. Must be cached (unlike `get_document_store`): the graph's state
    lives in the Python object itself, not in a database row, so a fresh
    instance per call would silently forget everything after each
    request. Still volatile across a process restart — persisting it is
    a deferred decision, documented as debt in
    docs/14-document-intelligence.md rather than silently dropped.
    Interdit: a single graph shared by every firm, which is what
    `DocumentIntelligencePipeline`'s own `InMemoryKnowledgeGraph()`
    default would be if used directly here instead of through this
    accessor."""
    return InMemoryKnowledgeGraph()


def get_document_pipeline(firm_id: uuid.UUID | str) -> DocumentIntelligencePipeline:
    """Firm-scoped `DocumentIntelligencePipeline` (ADR-DOCINT-01) —
    assembled fresh on every call, no longer the Sprint 37 `lru_cache`
    singleton one instance shared by every firm (see
    docs/151-architecture-persistance.md for that earlier state). Shares
    the Kernel's `EventBus` so `CaseIntelligenceWorkflow` can react to
    `DocumentProcessed` events (see docs/19-case-intelligence.md) when
    called from an in-process caller; the Celery task
    (`tmis.core.tasks.document_tasks.process_document_task`) builds its
    own pipeline directly instead of going through this accessor, for the
    same reason `trigger_case_workflow_task` doesn't call
    `get_case_intelligence_workflow`: a Celery worker cannot share the
    FastAPI process's in-process `EventBus`."""
    return DocumentIntelligencePipeline(
        event_bus=get_kernel().event_bus,
        document_store=get_document_store(firm_id),
        knowledge_graph=get_document_knowledge_graph(firm_id),
    )
