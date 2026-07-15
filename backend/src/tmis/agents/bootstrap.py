from functools import lru_cache

from tmis.agents.contract_agent import ContractAgent
from tmis.agents.jurisprudence_agent import JurisprudenceAgent
from tmis.agents.research_agent import ResearchAgent
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.ai_fabric.bootstrap import get_ai_intelligence_fabric
from tmis.ai_governance.bootstrap import get_ai_governance_platform
from tmis.cabinet_knowledge.bootstrap import get_clause_engine
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.legal_research.bootstrap import get_research_orchestrator


@lru_cache
def get_research_agent() -> ResearchAgent:
    """Process-wide `ResearchAgent` singleton, wired on top of the shared
    `ResearchOrchestrator` (Sprint 5) and `AIGovernancePlatform`
    (Sprint 15) — same `lru_cache` composition-root pattern as
    `tmis.legal_research.bootstrap.get_research_orchestrator` and
    `tmis.ai_governance.bootstrap.get_ai_governance_platform`.
    """
    return ResearchAgent(
        orchestrator=get_research_orchestrator(),
        governance=get_ai_governance_platform(),
    )


@lru_cache
def get_jurisprudence_agent() -> JurisprudenceAgent:
    """Process-wide `JurisprudenceAgent` singleton (Sprint 34), combining
    both patterns already established for this composition root: it
    shares the same `ResearchOrchestrator` singleton as `get_research_
    agent()` (the LRE, filtered to the "jurisprudence" connector) and,
    like `AnalysisAgent`, the shared `TMISKernel`/`AIIntelligenceFabric`
    for its generative comparison step plus `AIGovernancePlatform` for
    explainability. `CaseStorePort` is the same store the Case
    Intelligence workflow reads/writes, so a `case_id` resolves to the
    real `CaseProfile` rather than an agent-local store.
    """
    return JurisprudenceAgent(
        orchestrator=get_research_orchestrator(),
        kernel=get_kernel(),
        case_store=get_case_intelligence_workflow().case_store,
        fabric=get_ai_intelligence_fabric(),
        governance=get_ai_governance_platform(),
    )


@lru_cache
def get_contract_agent() -> ContractAgent:
    """Process-wide `ContractAgent` singleton (Sprint 35), following the
    same `AnalysisAgent`/`JurisprudenceAgent` composition: the shared
    `TMISKernel`/`AIIntelligenceFabric` for its generative risk synthesis,
    `AIGovernancePlatform` for explainability, the same `CaseStorePort` as
    the Case Intelligence workflow, and the firm's real `ClauseEngine`
    (Sprint 12, `tmis.cabinet_knowledge.bootstrap.get_clause_engine()`) for
    clause risk/coverage detection. `document_store` is left to its own
    default `InMemoryDocumentStore()`, exactly like `AnalysisAgent()`'s own
    default when constructed with no arguments — no shared document store
    singleton exists in this composition root yet for either agent.
    """
    return ContractAgent(
        kernel=get_kernel(),
        case_store=get_case_intelligence_workflow().case_store,
        clause_engine=get_clause_engine(),
        fabric=get_ai_intelligence_fabric(),
        governance=get_ai_governance_platform(),
    )
