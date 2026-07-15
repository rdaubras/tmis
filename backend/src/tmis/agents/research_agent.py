from tmis.agents.citations import research_citation_to_citation
from tmis.agents.contracts import AgentInput, AgentOutput, ConfidenceLevel
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.legal_research.bootstrap import get_research_orchestrator
from tmis.legal_research.search.orchestrator import ResearchOrchestrator
from tmis.legal_research.search.schemas import ResearchResponse, ResearchResult


class ResearchAgent:
    """Recherche documentaire via connecteurs configurables (docs/05-strategie-multi-agents.md).

    Remplace le placeholder Sprint 1 par un appel réel à
    `ResearchOrchestrator.search()` (Sprint 5, voir
    docs/21-legal-research.md) : requête, préparation, exécution multi-
    connecteurs, dédoublonnage/normalisation, classement, citations,
    historique et métriques d'évaluation restent entièrement la
    responsabilité du LRE — cet agent ne réimplémente ni ne contourne
    aucune de ces étapes, il expose la réponse déjà produite sous le
    contrat `AgentPort`.

    Câblage (voir aussi docs/161-architecture-agent-recherche.md) :
    - `ResearchOrchestrator.search(raw_text, case_id=...)` est le seul
      point d'appel à la recherche documentaire (jamais un second
      chemin vers un connecteur ou un moteur de classement) ;
    - chaque `ResearchCitation` de la réponse (`get_citations()`) est
      convertie en `Citation` (le contrat agents, `tmis.ai.schemas.
      citation`) par l'adaptateur explicite `tmis.agents.citations.
      research_citation_to_citation` — `tmis.legal_research.citations`
      n'a pas à connaître ce contrat ; ce même adaptateur est réutilisé
      tel quel par `JurisprudenceAgent` (Sprint 34) pour éviter un
      second chemin de conversion ;
    - `AIGovernancePlatform.explainability` enregistre, pour chaque
      exécution, un rapport consultable (combien de résultats, quels
      connecteurs, cache atteint ou non).

    Contrairement à `AnalysisAgent`/`SynthesisAgent`, cet agent ne câble
    pas `AIIntelligenceFabric` : il n'appelle jamais `TMISKernel.
    complete()` lui-même — le travail génératif éventuel (embeddings,
    routage de connecteurs) est entièrement interne à `ResearchOrchestrator`
    et à son pipeline (`HybridResearchSearch`, etc.), qui restent hors
    périmètre de ce sprint. Câbler `AIIntelligenceFabric` ici n'aurait
    rien à router : confirmé en Phase 0, voir
    docs/reports/sprint-33-rapport-architecture.md.
    """

    name = "research"

    def __init__(
        self,
        *,
        orchestrator: ResearchOrchestrator | None = None,
        governance: AIGovernancePlatform | None = None,
        firm_id: str = "default",
    ) -> None:
        self._orchestrator = orchestrator or get_research_orchestrator()
        self._governance = governance
        self._firm_id = firm_id

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        query = agent_input.context.get("query")
        if not isinstance(query, str) or not query.strip():
            return AgentOutput(
                result={"search_id": None, "query": None, "results": [], "connectors_used": []},
                confidence=ConfidenceLevel.LOW,
                warnings=["No query provided in context: nothing to research for this task."],
            )

        case_id = agent_input.case_id
        response = await self._orchestrator.search(query, case_id=case_id)
        research_citations = self._orchestrator.get_citations(response.search_id) or ()
        citations = [
            research_citation_to_citation(result, citation)
            for result, citation in zip(response.results, research_citations, strict=True)
        ]

        warnings: list[str] = []
        if not response.results:
            warnings.append(f"No result found for query {query!r}.")

        confidence = self._confidence_for(response)

        self._record_explainability(agent_input, query, response)

        return AgentOutput(
            result={
                "search_id": response.search_id,
                "query": response.query,
                "results": [self._result_to_dict(result) for result in response.results],
                "connectors_used": list(response.connectors_used),
                "duration_ms": response.duration_ms,
                "cache_hit": response.cache_hit,
            },
            citations=citations,
            confidence=confidence,
            warnings=warnings,
        )

    @staticmethod
    def _result_to_dict(result: ResearchResult) -> dict[str, object]:
        return {
            "id": result.id,
            "title": result.title,
            "excerpt": result.excerpt,
            "connector": result.connector,
            "document_type": result.document_type,
            "reference": result.reference,
            "date": result.date,
            "score": result.final_score,
        }

    @staticmethod
    def _confidence_for(response: ResearchResponse) -> ConfidenceLevel:
        if not response.results:
            return ConfidenceLevel.LOW
        if response.cache_hit:
            return ConfidenceLevel.HIGH
        return ConfidenceLevel.MEDIUM

    def _record_explainability(
        self, agent_input: AgentInput, query: str, response: ResearchResponse
    ) -> None:
        if self._governance is None:
            return
        steps = [
            f"Requête envoyée à ResearchOrchestrator.search() ({query!r}).",
            f"{len(response.results)} résultat(s) classé(s) et normalisé(s) reçu(s) via "
            f"{len(response.connectors_used)} connecteur(s) (cache_hit={response.cache_hit}).",
        ]
        self._governance.explainability.generate(
            self._firm_id,
            str(agent_input.task_id),
            summary=(
                f"Recherche juridique pour {query!r} : {len(response.results)} résultat(s), "
                f"{len(response.connectors_used)} connecteur(s) utilisé(s)."
            ),
            steps_followed=tuple(steps),
            agents_involved=(self.name,),
            documents_consulted=tuple(result.id for result in response.results),
        )
