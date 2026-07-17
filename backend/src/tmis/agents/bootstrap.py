import uuid
from functools import lru_cache

from fastapi import Depends

from tmis.agents.analysis_agent import AnalysisAgent
from tmis.agents.contract_agent import ContractAgent
from tmis.agents.jurisprudence_agent import JurisprudenceAgent
from tmis.agents.orchestrator import Orchestrator
from tmis.agents.research_agent import ResearchAgent
from tmis.agents.synthesis_agent import SynthesisAgent
from tmis.agents.verifier_agent import VerifierAgent
from tmis.agents.watch_agent import WatchAgent
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.ai_fabric.bootstrap import get_ai_intelligence_fabric
from tmis.ai_governance.bootstrap import get_ai_governance_platform
from tmis.api.deps import get_current_firm_id
from tmis.cabinet_knowledge.bootstrap import get_clause_engine
from tmis.case_intelligence.bootstrap import (
    get_case_intelligence_workflow,
    get_shared_case_intelligence_workflow,
)
from tmis.document_intelligence.bootstrap import get_document_store
from tmis.legal_research.bootstrap import get_shared_research_orchestrator


@lru_cache
def get_research_agent() -> ResearchAgent:
    """Process-wide `ResearchAgent` singleton, wired on top of the shared
    `ResearchOrchestrator` (Sprint 5) and `AIGovernancePlatform`
    (Sprint 15) — same `lru_cache` composition-root pattern as
    `tmis.legal_research.bootstrap.get_shared_research_orchestrator` (the
    non-firm-scoped composition path, since this accessor has no request
    to derive a `firm_id` from — see that function's own docstring) and
    `tmis.ai_governance.bootstrap.get_ai_governance_platform`.
    """
    return ResearchAgent(
        orchestrator=get_shared_research_orchestrator(),
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
    explainability. `CaseStorePort` is
    `get_shared_case_intelligence_workflow().case_store` (ADR-CASEINT-01,
    docs/19-case-intelligence.md) — this accessor, like `get_research_
    agent()`, has no request to derive a `firm_id` from, so it composes
    the same non-firm-scoped, documented-debt case store the legacy
    `CaseIntelligenceWorkflow` singleton always used, not the firm-scoped
    persistent one `/api/v1/cases/*` now reads and writes.
    """
    return JurisprudenceAgent(
        orchestrator=get_shared_research_orchestrator(),
        kernel=get_kernel(),
        case_store=get_shared_case_intelligence_workflow().case_store,
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
    clause risk/coverage detection. `document_store` is the shared
    `DocumentStorePort` singleton (Sprint 37,
    `tmis.document_intelligence.bootstrap.get_document_store()`) — the
    same instance `get_document_pipeline()` and `Orchestrator`'s
    `AnalysisAgent` use, rather than each composition root instantiating
    its own `SQLAlchemyDocumentStore()`. `case_store` is
    `get_shared_case_intelligence_workflow().case_store` for the same
    reason as `get_jurisprudence_agent()` above (ADR-CASEINT-01,
    docs/19-case-intelligence.md): no request, no `firm_id`.
    """
    return ContractAgent(
        kernel=get_kernel(),
        document_store=get_document_store(),
        case_store=get_shared_case_intelligence_workflow().case_store,
        clause_engine=get_clause_engine(),
        fabric=get_ai_intelligence_fabric(),
        governance=get_ai_governance_platform(),
    )


@lru_cache
def get_watch_agent() -> WatchAgent:
    """Process-wide `WatchAgent` singleton (Sprint 36), the last of the
    six `tmis.agents` agents made real by this roadmap: shares the same
    `ResearchOrchestrator` singleton as `get_research_agent()`/
    `get_jurisprudence_agent()` (filtered, per watch configuration, to the
    connectors that configuration surveils) and, like `AnalysisAgent`/
    `JurisprudenceAgent`/`ContractAgent`, the shared `TMISKernel`/
    `AIIntelligenceFabric` for its optional alert synthesis plus
    `AIGovernancePlatform` for explainability. No new store is wired here:
    novelty detection is stateless (see `WatchAgent`'s own docstring and
    docs/164-architecture-agent-veille.md).
    """
    return WatchAgent(
        orchestrator=get_shared_research_orchestrator(),
        kernel=get_kernel(),
        fabric=get_ai_intelligence_fabric(),
        governance=get_ai_governance_platform(),
    )


def get_orchestrator(
    firm_id: uuid.UUID = Depends(get_current_firm_id),
) -> Orchestrator:
    """Assembled fresh on every call, scoped to the caller's `firm_id`
    (ADR-CASEINT-01, docs/19-case-intelligence.md) — no longer the Sprint
    41 `lru_cache` singleton. `get_orchestrator` backs exactly one route,
    case_intelligence's own `GET /{case_id}/analysis`
    (`tmis.api.v1.case_intelligence.routes`), so unlike
    `get_jurisprudence_agent()`/`get_contract_agent()` above it *is*
    firm-scoped: that route's `_get_profile_or_404` check and this
    orchestrator's `AnalysisAgent`/`VerifierAgent`/`SynthesisAgent` must
    all read and write the exact same `CaseProfile` for the same
    `case_id`, or the analysis silently stops seeing what the rest of
    the resource just wrote (see docs/19-case-intelligence.md — non-
    régression composition). Built on the same four collaborators as
    before: `get_kernel()`, `get_case_intelligence_workflow(firm_id).
    case_store`, `get_ai_intelligence_fabric()`, `get_ai_governance_
    platform()` — plus `get_document_store()` for `AnalysisAgent`.
    `Orchestrator()` built with no arguments keeps its private, unshared
    default construction unchanged; only callers that go through
    `get_orchestrator()` see the fully wired, firm-scoped version.
    """
    kernel = get_kernel()
    case_store = get_case_intelligence_workflow(firm_id).case_store
    fabric = get_ai_intelligence_fabric()
    governance = get_ai_governance_platform()

    analysis_agent = AnalysisAgent(
        kernel=kernel,
        document_store=get_document_store(),
        case_store=case_store,
        fabric=fabric,
        governance=governance,
    )
    verifier_agent = VerifierAgent(case_store=case_store)
    synthesis_agent = SynthesisAgent(
        kernel=kernel,
        case_store=case_store,
        fabric=fabric,
        governance=governance,
    )
    return Orchestrator(
        analysis_agent=analysis_agent,
        verifier_agent=verifier_agent,
        synthesis_agent=synthesis_agent,
    )
