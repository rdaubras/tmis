import uuid
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.api.deps import get_current_firm_id
from tmis.core.database import get_db_session
from tmis.legal_research.cache.research_cache import ResearchCache
from tmis.legal_research.citations.engine import CitationEngine
from tmis.legal_research.connectors.factory import (
    build_internal_documentation_connector,
    build_private_database_connector,
)
from tmis.legal_research.connectors.registration import register_legal_research_connectors
from tmis.legal_research.evaluation.evaluator import ResearchEvaluator
from tmis.legal_research.history.adapters.sqlalchemy_store import SQLAlchemyResearchHistory
from tmis.legal_research.history.in_memory_history import InMemoryResearchHistory
from tmis.legal_research.normalization.normalizer import SourceNormalizer
from tmis.legal_research.queries.engine import HeuristicQueryEngine
from tmis.legal_research.ranking.configurable_ranker import ConfigurableRanker
from tmis.legal_research.search.hybrid_search import HybridResearchSearch
from tmis.legal_research.search.in_memory_store import InMemoryResearchSearchStore
from tmis.legal_research.search.orchestrator import ResearchOrchestrator
from tmis.legal_research.search.sqlalchemy_store import SQLAlchemyResearchSearchStore
from tmis.legal_research.sources.registry import SourceRegistry
from tmis.runtime_platform.distributed_cache.engine import DistributedCacheEngine

# ----------------------------------------------------------------------
# Stateless collaborators — process-wide singletons (mirrors ADR-SLICE-02,
# docs/28-legal-drafting.md, and this slice's own ADR-RESEARCH-01/02, see
# docs/21-legal-research.md): none of these hold anything that varies by
# tenant or by search. Connector registration onto the shared Kernel's
# `ConnectorManager` happens exactly once, the first time
# `get_search_engine` runs.
# ----------------------------------------------------------------------


@lru_cache
def get_source_registry() -> SourceRegistry:
    return SourceRegistry()


@lru_cache
def get_query_engine() -> HeuristicQueryEngine:
    return HeuristicQueryEngine()


@lru_cache
def get_normalizer() -> SourceNormalizer:
    return SourceNormalizer()


@lru_cache
def get_ranker() -> ConfigurableRanker:
    return ConfigurableRanker(get_source_registry())


@lru_cache
def get_citation_engine() -> CitationEngine:
    return CitationEngine()


@lru_cache
def get_evaluator() -> ResearchEvaluator:
    return ResearchEvaluator()


@lru_cache
def get_distributed_cache_engine() -> DistributedCacheEngine:
    return DistributedCacheEngine(get_kernel().cache)


@lru_cache
def get_search_engine() -> HybridResearchSearch:
    """Registers the LRE's own connectors (internal documentation,
    private database — real if configured, the Sprint 5 in-memory
    fixtures otherwise, see `tmis.legal_research.connectors.factory`) on
    the Kernel's existing `ConnectorManager` alongside the codes/
    jurisprudence/doctrine connectors, then builds the hybrid search
    strategy over the resulting connector list. Cached so registration
    and the resulting default-connectors snapshot happen exactly once
    per process — matching the previous, single `get_research_
    orchestrator` `lru_cache`'s behaviour before this module split
    stateless collaborators from per-request, firm-scoped state
    (ADR-RESEARCH-02).
    """
    kernel = get_kernel()
    register_legal_research_connectors(
        kernel.connector_manager,
        internal_documentation=build_internal_documentation_connector(),
        private_database=build_private_database_connector(),
    )
    return HybridResearchSearch(
        kernel, default_connectors=kernel.connector_manager.list_connectors()
    )


def get_research_orchestrator(
    session: Session = Depends(get_db_session),
    firm_id: uuid.UUID = Depends(get_current_firm_id),
) -> ResearchOrchestrator:
    """Assembled fresh on every request (ADR-RESEARCH-02, mirrors
    ADR-SLICE-02 from the `cases -> drafting` slice) — no longer an
    `lru_cache` singleton. History, the persisted search store, and the
    cache are the only things scoped to the caller's `firm_id`: a
    research history entry, a past search, and a cached search result
    all belong to exactly one cabinet (see docs/21-legal-research.md,
    ADR-RESEARCH-01/02). Everything else composes the same process-wide,
    stateless collaborators as before.

    This is the accessor every HTTP route depends on
    (`tmis.legal_research.api.routes`) and the one
    `tmis.legal_drafting.bootstrap.get_document_orchestrator` now calls
    with its own request's `session`/`firm_id`. Callers outside an HTTP
    request — `tmis.legal_reasoning` and `tmis.agents`, neither of which
    has been given firm-scoped composition yet — use
    `get_shared_research_orchestrator` instead (see its own docstring for
    why that is a deliberate, documented scope boundary, not an
    oversight).
    """
    return ResearchOrchestrator(
        query_engine=get_query_engine(),
        search=get_search_engine(),
        normalizer=get_normalizer(),
        ranker=get_ranker(),
        citation_engine=get_citation_engine(),
        cache=ResearchCache(get_distributed_cache_engine(), firm_id),
        history=SQLAlchemyResearchHistory(session, firm_id),
        searches=SQLAlchemyResearchSearchStore(session, firm_id),
        evaluator=get_evaluator(),
    )


# ----------------------------------------------------------------------
# Legacy shared singleton — pre-dates ADR-RESEARCH-01/02 and stays
# unscoped on purpose (documented debt, see docs/21-legal-research.md
# § Persistance & isolation multi-tenant). `tmis.legal_reasoning` and
# `tmis.agents` (`research_agent`, `jurisprudence_agent`, `watch_agent`,
# `agents.bootstrap`) compose `ResearchOrchestrator` outside any HTTP
# request — there is no `Session`/`firm_id` to give them, and giving
# every one of those composition roots its own firm-scoped persistence
# pass is a separate, larger piece of work this slice does not attempt
# (see the sprint's own "Out of scope" section — legal_research's own
# isolation is the target, not a blanket generalization). This keeps
# their exact pre-existing behaviour — one process-wide orchestrator,
# in-memory history and search store, a cache keyed under one constant,
# non-tenant "firm" — rather than silently reusing the now firm-scoped
# `get_research_orchestrator` with a fabricated `firm_id`, which would
# look isolated without actually being isolated.
# ----------------------------------------------------------------------

_SHARED_ORCHESTRATOR_CACHE_NAMESPACE = "shared"


@lru_cache
def get_shared_research_orchestrator() -> ResearchOrchestrator:
    return ResearchOrchestrator(
        query_engine=get_query_engine(),
        search=get_search_engine(),
        normalizer=get_normalizer(),
        ranker=get_ranker(),
        citation_engine=get_citation_engine(),
        cache=ResearchCache(
            get_distributed_cache_engine(), _SHARED_ORCHESTRATOR_CACHE_NAMESPACE
        ),
        history=InMemoryResearchHistory(),
        searches=InMemoryResearchSearchStore(),
        evaluator=get_evaluator(),
    )


def clear_research_caches() -> None:
    """Clears every `lru_cache` this module owns — the stateless
    singletons above and `get_shared_research_orchestrator`. `get_kernel`
    is itself an `lru_cache`d singleton elsewhere
    (`tmis.ai.kernel.bootstrap`); `get_search_engine` captures a
    reference to *the* kernel instance at the time it first runs
    (connector registration happens then too), so any test/fixture that
    resets `get_kernel` must also reset the caches here — otherwise a
    freshly reset kernel and a stale `get_search_engine` (still pointing
    at the previous kernel) end up in the same orchestrator. Call this
    instead of clearing individual caches one by one.
    """
    get_source_registry.cache_clear()
    get_query_engine.cache_clear()
    get_normalizer.cache_clear()
    get_ranker.cache_clear()
    get_citation_engine.cache_clear()
    get_evaluator.cache_clear()
    get_distributed_cache_engine.cache_clear()
    get_search_engine.cache_clear()
    get_shared_research_orchestrator.cache_clear()
