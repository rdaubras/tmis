import uuid
from functools import lru_cache

from fastapi import Depends

from tmis.ai.events.events import DocumentProcessed
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.api.deps import get_current_firm_id
from tmis.case_intelligence.cases.adapters.sqlalchemy_store import SQLAlchemyCaseStore
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.ports import CaseStorePort
from tmis.case_intelligence.relationships.in_memory_graph import InMemoryCaseGraph
from tmis.case_intelligence.relationships.ports import CaseGraphPort
from tmis.case_intelligence.search.engine import CaseSearchEngine
from tmis.case_intelligence.search.ports import CaseSearchPort
from tmis.case_intelligence.summaries.generator import CaseSummaryGenerator
from tmis.case_intelligence.workflow.case_workflow import CaseIntelligenceWorkflow
from tmis.core.database import SessionLocal
from tmis.core.logging import get_logger
from tmis.document_intelligence.bootstrap import get_document_pipeline
from tmis.infrastructure.persistence.repositories import SqlAlchemyCaseRepository

_LOGGER_NAME = "tmis.case_intelligence.bootstrap"


def get_case_store(firm_id: uuid.UUID | str) -> CaseStorePort:
    """Firm-scoped `CaseStorePort` (ADR-CASEINT-01, "case_intelligence"
    persistent & isolated slice, see docs/19-case-intelligence.md) —
    replaces the Sprint 43 `get_case_store()` singleton, which built one
    `SQLAlchemyCaseStore` shared by every firm (see
    docs/151-architecture-persistance.md for that earlier state). There
    is no longer an agnostic `SQLAlchemyCaseStore`: `firm_id` is
    mandatory, bound once here, at construction. Built fresh on every
    call — the store itself holds no state beyond `firm_id` (every method
    opens and closes its own `Session`, see
    `SQLAlchemyCaseStore.__init__`'s own docstring for why it keeps a
    `session_factory` instead of a request-bound `Session`), so unlike
    `get_case_graph` below there is nothing to cache."""
    return SQLAlchemyCaseStore(firm_id=firm_id)


@lru_cache
def get_case_graph(firm_id: uuid.UUID | str) -> CaseGraphPort:
    """One `InMemoryCaseGraph` per firm, cached for the lifetime of the
    process (T3, docs/19-case-intelligence.md) — `lru_cache` keyed by
    `firm_id` is the partition: every call for the same firm returns the
    exact same graph instance (so nodes/edges added by one request are
    still there for the next), while two different firms never share
    one. Unlike `get_case_store`, this *must* be cached: the graph's
    state lives in the Python object itself, not in a database row, so a
    fresh instance per call would silently forget everything after each
    request. Still volatile across a process restart — persisting it is
    T3's own deferred decision, documented as debt in
    docs/19-case-intelligence.md rather than silently dropped. Interdit:
    a single graph shared by every firm, which is what
    `tmis.case_intelligence.workflow.case_workflow.
    CaseIntelligenceWorkflow`'s own `InMemoryCaseGraph()` default would
    be if used directly here instead of through this accessor."""
    return InMemoryCaseGraph()


@lru_cache
def get_case_search_engine(firm_id: uuid.UUID | str) -> CaseSearchPort:
    """One `CaseSearchEngine` per firm, cached for the lifetime of the
    process — same reasoning and same "must be cached" status as
    `get_case_graph` above: `CaseSearchEngine` wraps a `DocumentEmbeddingBridge`
    that owns its own in-memory vector index (`tmis.ai.rag.indexing.
    InMemoryVectorIndex` by default), so a fresh instance per call would
    reindex a case's facts/actors/timeline on `ingest_document()` and
    then immediately lose that index by the time a `/search` request (a
    different, throwaway `CaseIntelligenceWorkflow`) builds its own new
    engine. Partitioned by `firm_id` for the same reason the graph is:
    two firms' case content must never land in the same vector index."""
    return CaseSearchEngine()


def get_case_intelligence_workflow(
    firm_id: uuid.UUID = Depends(get_current_firm_id),
) -> CaseIntelligenceWorkflow:
    """Assembled fresh on every call, scoped to the caller's `firm_id`
    (ADR-CASEINT-01) — no longer the Sprint 43 `lru_cache` singleton one
    `CaseIntelligenceWorkflow` shared by every firm and every request
    (see docs/151-architecture-persistance.md for that earlier state,
    docs/19-case-intelligence.md for why it had to change). This is the
    accessor every case_intelligence HTTP route depends on
    (`tmis.api.v1.case_intelligence.routes`) and the one
    `tmis.legal_drafting.bootstrap.get_document_orchestrator` now calls
    with its own request's `firm_id` (a case referenced from a draft is
    isolated exactly like a direct `/cases/*` call). `auto_subscribe`
    stays `False`: this instance is thrown away at the end of the
    request/call, so it must never register a new `EventBus` subscriber
    of its own — see `_register_document_processed_handler` below for
    the one, process-wide subscription that replaces what the singleton
    used to do implicitly by existing.

    Callers outside an HTTP request — `tmis.legal_reasoning` and the
    `tmis.agents` accessors that have no request to derive a `firm_id`
    from (`get_jurisprudence_agent`, `get_contract_agent`) — use
    `get_shared_case_intelligence_workflow` instead (see its own
    docstring for why that is a deliberate, documented scope boundary,
    not an oversight). `agents.bootstrap.get_orchestrator` *is*
    firm-scoped (it backs case_intelligence's own `/analysis` route) and
    calls this accessor directly with its own `firm_id`.
    """
    _register_document_processed_handler()
    pipeline = get_document_pipeline()
    return CaseIntelligenceWorkflow(
        case_store=get_case_store(firm_id),
        knowledge_graph=get_case_graph(firm_id),
        search_engine=get_case_search_engine(firm_id),
        document_store=pipeline.document_store,
        event_bus=get_kernel().event_bus,
        summary_generator=CaseSummaryGenerator(get_kernel()),
        auto_subscribe=False,
    )


# ----------------------------------------------------------------------
# Legacy shared singleton — pre-dates ADR-CASEINT-01 and stays unscoped
# on purpose (documented debt, see docs/19-case-intelligence.md §
# Persistance & isolation multi-tenant), mirroring
# `tmis.legal_research.bootstrap.get_shared_research_orchestrator`.
# `tmis.legal_reasoning`, `tmis.agents` (`jurisprudence_agent`,
# `contract_agent`) and `tmis.api.v1.chat.routes` compose
# `CaseIntelligenceWorkflow` outside any HTTP request with a resolvable
# `firm_id` — giving them a fabricated one here would look isolated
# without actually being isolated. Uses the pre-Sprint-43
# `InMemoryCaseStore`/`InMemoryCaseGraph` (not the persistent, firm-
# scoped store), so it never reads or writes a row `get_case_
# intelligence_workflow(firm_id)` also touches — no risk of one firm's
# request populating what looks like a shared, cross-tenant cache.
# ----------------------------------------------------------------------


@lru_cache
def get_shared_case_intelligence_workflow() -> CaseIntelligenceWorkflow:
    _register_document_processed_handler()
    pipeline = get_document_pipeline()
    return CaseIntelligenceWorkflow(
        case_store=InMemoryCaseStore(),
        knowledge_graph=InMemoryCaseGraph(),
        search_engine=CaseSearchEngine(),
        document_store=pipeline.document_store,
        event_bus=get_kernel().event_bus,
        summary_generator=CaseSummaryGenerator(get_kernel()),
        auto_subscribe=False,
    )


async def _handle_document_processed(event: DocumentProcessed) -> None:
    """Replaces the auto-`ingest_document` subscription the Sprint 43
    singleton used to register on itself at construction
    (`CaseIntelligenceWorkflow.__init__(auto_subscribe=True)`). That
    shape no longer works once `CaseIntelligenceWorkflow` instances are
    firm-scoped and thrown away per call: there is no single instance
    left to durably hold a subscription, and a fresh instance
    subscribing on every request would leak handlers.  Registered once,
    process-wide, on the Kernel's own `EventBus` — for every
    `DocumentProcessed` event, this resolves *this* event's own
    `firm_id`/`case_id` to a scoped store, not a fixed one (ADR-CASEINT-
    01/02): every document belongs to whichever firm its own event says,
    not to whichever firm happened to build the singleton first.

    `event.firm_id` is `None` for any `DocumentIntelligencePipeline.
    process()` call that did not pass one (`document_intelligence` is
    not firm-isolated yet, see `DocumentProcessed`'s own docstring) — a
    document processed without a `firm_id` cannot be attributed to a
    cabinet, so no case is touched for it; this is the same "no enqueue
    without firm_id" invariant `trigger_case_workflow_task` enforces on
    the Celery path (T4, docs/19-case-intelligence.md), applied to the
    event path.  `event.case_id` is not trusted as-is either: it must
    resolve to a `cases` row this firm actually owns (ADR-CASEINT-02) —
    anything else is rejected and logged, never silently ignored, so a
    stray or cross-tenant `case_id` cannot create a profile.
    """
    logger = get_logger(_LOGGER_NAME)
    if not event.success or event.case_id is None:
        return
    if event.firm_id is None:
        logger.warning(
            "case_workflow_event_rejected_no_firm_id",
            document_id=event.document_id,
            case_id=event.case_id,
        )
        return

    try:
        firm_uuid = uuid.UUID(event.firm_id)
        case_uuid = uuid.UUID(event.case_id)
    except ValueError:
        logger.warning(
            "case_workflow_event_rejected_malformed_id",
            document_id=event.document_id,
            case_id=event.case_id,
            firm_id=event.firm_id,
        )
        return

    with SessionLocal() as session:
        case = SqlAlchemyCaseRepository(session).get_by_id(case_uuid, firm_uuid)
    if case is None:
        logger.warning(
            "case_workflow_event_rejected_case_not_owned",
            document_id=event.document_id,
            case_id=event.case_id,
            firm_id=event.firm_id,
        )
        return

    pipeline = get_document_pipeline()
    record = pipeline.document_store.get(event.document_id)
    if record is None:
        return

    workflow = CaseIntelligenceWorkflow(
        case_store=get_case_store(firm_uuid),
        knowledge_graph=get_case_graph(firm_uuid),
        search_engine=get_case_search_engine(firm_uuid),
        document_store=pipeline.document_store,
        event_bus=get_kernel().event_bus,
        summary_generator=CaseSummaryGenerator(get_kernel()),
        auto_subscribe=False,
    )
    await workflow.ingest_document(event.case_id, record)
    logger.info(
        "case_workflow_triggered_by_event",
        case_id=event.case_id,
        document_id=event.document_id,
        firm_id=event.firm_id,
    )


@lru_cache
def _register_document_processed_handler() -> bool:
    get_kernel().event_bus.subscribe(DocumentProcessed, _handle_document_processed)
    return True


def clear_case_intelligence_caches() -> None:
    """Clears every `lru_cache` this module owns. `get_kernel` is itself
    an `lru_cache`d singleton elsewhere (`tmis.ai.kernel.bootstrap`); a
    freshly reset kernel needs a freshly re-registered event subscriber
    and a freshly partitioned `get_case_graph`, so any test/fixture that
    resets `get_kernel` must also call this — otherwise a stale
    subscription still points at the previous kernel's `EventBus`. Call
    this instead of clearing individual caches one by one."""
    get_case_graph.cache_clear()
    get_case_search_engine.cache_clear()
    get_shared_case_intelligence_workflow.cache_clear()
    _register_document_processed_handler.cache_clear()
