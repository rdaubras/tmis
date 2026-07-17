from tmis.agents.citations import research_citation_to_citation
from tmis.agents.contracts import AgentInput, AgentOutput, ConfidenceLevel
from tmis.ai.kernel.kernel import TMISKernel
from tmis.ai_fabric.fabric import AIIntelligenceFabric
from tmis.ai_fabric.router.schemas import RoutingRequest
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.ports import CaseStorePort
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.legal_research.bootstrap import get_shared_research_orchestrator
from tmis.legal_research.search.orchestrator import ResearchOrchestrator
from tmis.legal_research.search.schemas import ResearchResponse, ResearchResult

_JURISPRUDENCE_CONNECTORS = ["jurisprudence"]
_EXCERPT_LENGTH = 400


class JurisprudenceAgent:
    """Recherche et comparaison de jurisprudence (docs/05-strategie-multi-agents.md).

    Remplace le placeholder Sprint 1 par un câblage réel qui combine les
    deux patrons établis par les sprints précédents (voir
    docs/162-architecture-agent-jurisprudence.md) :

    - la recherche de décisions n'est pas un nouveau moteur : comme
      `ResearchAgent` (Sprint 33), cet agent appelle
      `ResearchOrchestrator.search(query, connector_names=["jurisprudence"],
      case_id=...)` — le connecteur "jurisprudence" (Judilibre réel ou
      fixture, voir `tmis.ai.connectors.factory.build_jurisprudence_
      connector`) est déjà enregistré sur le `ConnectorManager` partagé
      du Kernel (`tmis.ai.kernel.bootstrap.get_kernel`), donc déjà
      cherchable par le LRE ; cet agent ne fait que filtrer la recherche
      sur ce seul connecteur. Chaque `ResearchCitation` de la réponse est
      convertie en `Citation` par `tmis.agents.citations.
      research_citation_to_citation`, le même adaptateur que
      `ResearchAgent` (aucun second chemin de conversion) ;
    - la comparaison de solutions jurisprudentielles (convergences,
      divergences, pertinence par rapport au dossier) est, elle,
      réellement nouvelle : personne d'autre dans le dépôt ne la produit.
      Comme `AnalysisAgent` (Sprint 29), cette synthèse générative passe
      par `AIIntelligenceFabric.route()` puis `TMISKernel.complete()` —
      jamais un second client LLM ni un appel direct à un provider — et,
      si un `case_id` est fourni, lit le `CaseProfile` correspondant via
      `CaseStorePort` pour évaluer la pertinence par rapport au dossier.

    `AIGovernancePlatform.explainability` enregistre, pour chaque
    exécution, un rapport consultable (combien de décisions comparées,
    quel modèle, quel dossier).
    """

    name = "jurisprudence"

    def __init__(
        self,
        *,
        orchestrator: ResearchOrchestrator | None = None,
        kernel: TMISKernel | None = None,
        case_store: CaseStorePort | None = None,
        fabric: AIIntelligenceFabric | None = None,
        governance: AIGovernancePlatform | None = None,
        firm_id: str = "default",
    ) -> None:
        self._orchestrator = orchestrator or get_shared_research_orchestrator()
        self._kernel = kernel or TMISKernel()
        self._case_store: CaseStorePort = case_store or InMemoryCaseStore()
        self._fabric = fabric
        self._governance = governance
        self._firm_id = firm_id

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        query = agent_input.context.get("query")
        if not isinstance(query, str) or not query.strip():
            return AgentOutput(
                result={
                    "search_id": None,
                    "query": None,
                    "results": [],
                    "connectors_used": [],
                    "comparison": None,
                    "model": None,
                },
                confidence=ConfidenceLevel.LOW,
                warnings=["No query provided in context: nothing to compare for this task."],
            )

        case_id = agent_input.case_id
        response = await self._orchestrator.search(
            query, connector_names=_JURISPRUDENCE_CONNECTORS, case_id=case_id
        )
        research_citations = self._orchestrator.get_citations(response.search_id) or ()
        citations = [
            research_citation_to_citation(result, citation)
            for result, citation in zip(response.results, research_citations, strict=True)
        ]

        case_profile: CaseProfile | None = None
        if case_id is not None:
            case_profile = self._case_store.get(case_id)

        warnings: list[str] = []
        model_name: str | None = None
        comparison: str | None = None
        if not response.results:
            warnings.append(
                f"No jurisprudence result found for query {query!r}: nothing to compare."
            )
        else:
            model_name, comparison = await self._generate_comparison(query, response, case_profile)

        if case_id is not None and case_profile is None:
            warnings.append(f"Case {case_id} was not found in the case store.")

        confidence = self._confidence_for(response)

        self._record_explainability(agent_input, query, response, model_name, case_profile)

        return AgentOutput(
            result={
                "search_id": response.search_id,
                "query": response.query,
                "results": [self._result_to_dict(result) for result in response.results],
                "connectors_used": list(response.connectors_used),
                "duration_ms": response.duration_ms,
                "cache_hit": response.cache_hit,
                "comparison": comparison,
                "model": model_name,
            },
            citations=citations,
            confidence=confidence,
            warnings=warnings,
        )

    async def _generate_comparison(
        self, query: str, response: ResearchResponse, case_profile: CaseProfile | None
    ) -> tuple[str, str]:
        prompt = self._build_prompt(query, response, case_profile)
        model_name, provider_name = self._route_model(prompt)
        completion = await self._kernel.complete(prompt, provider=provider_name)
        return model_name, completion.text

    def _build_prompt(
        self, query: str, response: ResearchResponse, case_profile: CaseProfile | None
    ) -> str:
        lines = [
            f"Compare les décisions de jurisprudence trouvées pour {query!r} : "
            "dégage les convergences, les divergences, et leur pertinence par "
            "rapport au dossier.",
        ]
        for result in response.results:
            lines.append(
                f"- {result.title} ({result.reference}, {result.date}) : "
                f"{result.excerpt[:_EXCERPT_LENGTH]}"
            )
        if case_profile is not None:
            lines.append(
                f"Dossier : {case_profile.title} "
                f"({len(case_profile.actors)} acteur(s), {len(case_profile.facts)} fait(s))"
            )
        return "\n".join(lines)

    def _route_model(self, prompt: str) -> tuple[str, str | None]:
        """Routes through the Fabric (Sprint 14), like `AnalysisAgent`:
        `RoutingDecision.model` already carries both the model name and
        its `provider`, so one `route()` call is enough."""
        if self._fabric is None:
            return "default", None

        decision = self._fabric.route(
            RoutingRequest(
                firm_id=self._firm_id, task_type="jurisprudence_comparison", prompt=prompt
            )
        )
        return decision.model.name, decision.model.provider

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
        self,
        agent_input: AgentInput,
        query: str,
        response: ResearchResponse,
        model_name: str | None,
        case_profile: CaseProfile | None,
    ) -> None:
        if self._governance is None:
            return
        steps = [
            "Requête envoyée à ResearchOrchestrator.search() filtrée sur le "
            f"connecteur 'jurisprudence' ({query!r}).",
            f"{len(response.results)} décision(s) reçue(s) (cache_hit={response.cache_hit}).",
        ]
        if case_profile is not None:
            steps.append(
                f"Lecture du dossier {case_profile.case_id!r} via CaseStorePort "
                "pour évaluer la pertinence des décisions."
            )
        if model_name is not None:
            steps.append(f"Comparaison générée via TMISKernel.complete() ({model_name}).")

        self._governance.explainability.generate(
            self._firm_id,
            str(agent_input.task_id),
            summary=(
                f"Comparaison de jurisprudence pour {query!r} : "
                f"{len(response.results)} décision(s) comparée(s)."
            ),
            steps_followed=tuple(steps),
            agents_involved=(self.name,),
            models_used=(model_name,) if model_name is not None else (),
            documents_consulted=tuple(result.id for result in response.results),
        )
