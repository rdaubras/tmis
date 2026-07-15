from tmis.agents.citations import research_citation_to_citation
from tmis.agents.contracts import AgentInput, AgentOutput, ConfidenceLevel
from tmis.ai.kernel.kernel import TMISKernel
from tmis.ai_fabric.fabric import AIIntelligenceFabric
from tmis.ai_fabric.router.schemas import RoutingRequest
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.legal_research.bootstrap import get_research_orchestrator
from tmis.legal_research.citations.schemas import ResearchCitation
from tmis.legal_research.search.orchestrator import ResearchOrchestrator
from tmis.legal_research.search.schemas import ResearchResponse, ResearchResult

_EXCERPT_LENGTH = 400

_ResultCitationPair = tuple[ResearchResult, ResearchCitation]


class WatchAgent:
    """Veille juridique et alertes ciblées depuis des sources configurées
    (docs/05-strategie-multi-agents.md, docs/164-architecture-agent-veille.md).

    Remplace le placeholder Sprint 1 en combinant les deux patrons déjà
    établis, comme `JurisprudenceAgent`/`ContractAgent` avant lui :

    - la recherche elle-même n'est pas un nouveau moteur : une
      « configuration de veille » (`query` + `connectors` surveillés +
      `case_id` optionnel, lus depuis `agent_input.context`) est traduite
      en un seul appel `ResearchOrchestrator.search(query,
      connector_names=connectors, case_id=...)` — le même LRE que
      `ResearchAgent`/`JurisprudenceAgent`, jamais un second moteur de
      recherche ni un second registre de connecteurs (les connecteurs
      « surveillés » sont un sous-ensemble de ceux déjà enregistrés sur le
      `ConnectorManager` partagé du Kernel, exactement comme
      `JurisprudenceAgent` filtre sur `["jurisprudence"]`). Chaque
      `ResearchCitation` est convertie en `Citation` par le même adaptateur
      partagé, `tmis.agents.citations.research_citation_to_citation` ;
    - la détection de ce qui est nouveau depuis la dernière exécution
      (Question Ouverte n°1, tranchée en Phase 0 — voir
      docs/164-architecture-agent-veille.md) reste entièrement stateless :
      l'appelant fournit dans `agent_input.context["known_result_ids"]`
      les identifiants de résultats déjà connus d'une exécution
      précédente de la même veille, et cet agent ne renvoie comme
      `new_results`/alerte que ceux qui n'y figurent pas. Aucun nouveau
      store n'est introduit : `result["result_ids"]` renvoie l'ensemble
      des identifiants de cette exécution pour que l'appelant les
      fusionne avec `known_result_ids` avant la prochaine exécution
      (union, pas remplacement) ;
    - la synthèse d'alerte, quand des résultats nouveaux existent, suit le
      même patron générique que les trois agents précédents :
      `AIIntelligenceFabric.route()` puis `TMISKernel.complete()` — jamais
      un second client LLM. Elle n'est produite que s'il y a au moins un
      résultat nouveau : une veille sans nouveauté n'a rien à synthétiser
      (même logique que `JurisprudenceAgent` sautant sa comparaison sur
      zéro résultat), et le contenu structuré (`new_results`, avec
      `id`/`title`/`excerpt`/`reference`/`connector`) reste la source de
      vérité de l'alerte : le message généré est une couche de lisibilité
      en langage naturel, jamais le seul support des faits (décision
      documentée dans docs/164-architecture-agent-veille.md).
    """

    name = "watch"

    def __init__(
        self,
        *,
        orchestrator: ResearchOrchestrator | None = None,
        kernel: TMISKernel | None = None,
        fabric: AIIntelligenceFabric | None = None,
        governance: AIGovernancePlatform | None = None,
        firm_id: str = "default",
    ) -> None:
        self._orchestrator = orchestrator or get_research_orchestrator()
        self._kernel = kernel or TMISKernel()
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
                    "connectors_used": [],
                    "result_ids": [],
                    "new_results": [],
                    "alert_message": None,
                    "model": None,
                },
                confidence=ConfidenceLevel.LOW,
                warnings=["No query provided in context: nothing to watch for this task."],
            )

        connector_names = self._resolve_connectors(agent_input.context.get("connectors"))
        known_result_ids = self._resolve_known_ids(agent_input.context.get("known_result_ids"))
        case_id = agent_input.case_id

        response = await self._orchestrator.search(
            query, connector_names=connector_names, case_id=case_id
        )
        research_citations = self._orchestrator.get_citations(response.search_id) or ()
        new_pairs: list[_ResultCitationPair] = [
            (result, citation)
            for result, citation in zip(response.results, research_citations, strict=True)
            if result.id not in known_result_ids
        ]
        citations = [
            research_citation_to_citation(result, citation) for result, citation in new_pairs
        ]

        warnings: list[str] = []
        if not response.results:
            warnings.append(f"No result found for watch query {query!r}.")
        elif not new_pairs:
            warnings.append(
                f"No new result since the last watch run for query {query!r}: "
                f"{len(response.results)} already-known result(s)."
            )

        model_name: str | None = None
        alert_message: str | None = None
        if new_pairs:
            model_name, alert_message = await self._generate_alert(query, new_pairs, case_id)

        confidence = self._confidence_for(response)

        self._record_explainability(
            agent_input, query, connector_names, response, new_pairs, model_name
        )

        return AgentOutput(
            result={
                "search_id": response.search_id,
                "query": response.query,
                "connectors_used": list(response.connectors_used),
                "result_ids": [result.id for result in response.results],
                "new_results": [self._result_to_dict(result) for result, _ in new_pairs],
                "alert_message": alert_message,
                "model": model_name,
            },
            citations=citations,
            confidence=confidence,
            warnings=warnings,
        )

    @staticmethod
    def _resolve_connectors(raw: object) -> list[str] | None:
        if isinstance(raw, list) and all(isinstance(item, str) for item in raw):
            return list(raw)
        return None

    @staticmethod
    def _resolve_known_ids(raw: object) -> set[str]:
        if isinstance(raw, list):
            return {item for item in raw if isinstance(item, str)}
        return set()

    async def _generate_alert(
        self, query: str, new_pairs: list[_ResultCitationPair], case_id: str | None
    ) -> tuple[str, str]:
        prompt = self._build_prompt(query, new_pairs, case_id)
        model_name, provider_name = self._route_model(prompt)
        completion = await self._kernel.complete(prompt, provider=provider_name)
        return model_name, completion.text

    @staticmethod
    def _build_prompt(
        query: str, new_pairs: list[_ResultCitationPair], case_id: str | None
    ) -> str:
        lines = [
            f"Rédige une alerte de veille juridique pour la requête {query!r} : "
            f"{len(new_pairs)} nouveau(x) résultat(s) depuis la dernière exécution de "
            "cette veille.",
        ]
        for result, _citation in new_pairs:
            lines.append(
                f"- {result.title} ({result.connector}, {result.reference}) : "
                f"{result.excerpt[:_EXCERPT_LENGTH]}"
            )
        if case_id is not None:
            lines.append(f"Dossier concerné : {case_id}")
        return "\n".join(lines)

    def _route_model(self, prompt: str) -> tuple[str, str | None]:
        """Routes through the Fabric (Sprint 14), like `AnalysisAgent`/
        `JurisprudenceAgent`/`ContractAgent`: `RoutingDecision.model` already
        carries both the model name and its `provider`, so one `route()`
        call is enough."""
        if self._fabric is None:
            return "default", None

        decision = self._fabric.route(
            RoutingRequest(firm_id=self._firm_id, task_type="watch_alert_synthesis", prompt=prompt)
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
        connector_names: list[str] | None,
        response: ResearchResponse,
        new_pairs: list[_ResultCitationPair],
        model_name: str | None,
    ) -> None:
        if self._governance is None:
            return

        if connector_names is not None:
            search_step = (
                "Requête envoyée à ResearchOrchestrator.search() filtrée sur les connecteurs "
                f"{connector_names!r} ({query!r})."
            )
        else:
            search_step = (
                f"Requête envoyée à ResearchOrchestrator.search() ({query!r}), "
                "tous connecteurs enregistrés."
            )
        steps = [
            search_step,
            f"{len(response.results)} résultat(s) reçu(s), {len(new_pairs)} nouveau(x) "
            f"depuis known_result_ids (cache_hit={response.cache_hit}).",
        ]
        if model_name is not None:
            steps.append(f"Alerte générée via TMISKernel.complete() ({model_name}).")

        self._governance.explainability.generate(
            self._firm_id,
            str(agent_input.task_id),
            summary=(
                f"Veille pour {query!r} : {len(new_pairs)} nouveau(x) résultat(s) sur "
                f"{len(response.results)} suivi(s)."
            ),
            steps_followed=tuple(steps),
            agents_involved=(self.name,),
            models_used=(model_name,) if model_name is not None else (),
            documents_consulted=tuple(result.id for result, _citation in new_pairs),
        )
