from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.legal_research.cache.research_cache import ResearchCache
from tmis.legal_research.citations.engine import CitationEngine
from tmis.legal_research.connectors.registration import register_legal_research_connectors
from tmis.legal_research.evaluation.evaluator import ResearchEvaluator
from tmis.legal_research.history.in_memory_history import InMemoryResearchHistory
from tmis.legal_research.normalization.normalizer import SourceNormalizer
from tmis.legal_research.queries.engine import HeuristicQueryEngine
from tmis.legal_research.ranking.configurable_ranker import ConfigurableRanker
from tmis.legal_research.search.hybrid_search import HybridResearchSearch
from tmis.legal_research.search.orchestrator import ResearchOrchestrator
from tmis.legal_research.sources.registry import SourceRegistry


@lru_cache
def get_research_orchestrator() -> ResearchOrchestrator:
    """Process-wide `ResearchOrchestrator` singleton (see
    docs/21-legal-research.md), wired on top of the shared `TMISKernel`:
    the LRE's own mock connectors (internal documentation, private
    database) are registered onto the Kernel's existing
    `ConnectorManager` alongside the Sprint 2 codes/jurisprudence/
    doctrine connectors, so agents keep querying through one Kernel.
    """
    kernel = get_kernel()
    register_legal_research_connectors(kernel.connector_manager)
    source_registry = SourceRegistry()

    return ResearchOrchestrator(
        query_engine=HeuristicQueryEngine(),
        search=HybridResearchSearch(
            kernel, default_connectors=kernel.connector_manager.list_connectors()
        ),
        normalizer=SourceNormalizer(),
        ranker=ConfigurableRanker(source_registry),
        citation_engine=CitationEngine(),
        cache=ResearchCache(kernel.cache),
        history=InMemoryResearchHistory(),
        evaluator=ResearchEvaluator(),
    )
