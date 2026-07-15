from tmis.agents.contracts import AgentInput, AgentOutput, ConfidenceLevel
from tmis.ai.kernel.kernel import TMISKernel
from tmis.ai.schemas.citation import Citation
from tmis.ai_fabric.fabric import AIIntelligenceFabric
from tmis.ai_fabric.router.schemas import RoutingRequest
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.writing_style.engine import WritingStyleEngine
from tmis.cabinet_knowledge.writing_style.schemas import WritingStyleProfile
from tmis.case_intelligence.actors.schemas import Actor
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.ports import CaseStorePort
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.issues.schemas import IssueStatus
from tmis.case_intelligence.summaries.generator import CaseSummaryGenerator
from tmis.case_intelligence.summaries.ports import SummaryGeneratorPort
from tmis.case_intelligence.summaries.schemas import CaseSummary

_STYLE_AUTHOR = "synthesis-agent"
_EXCERPT_LENGTH = 400


class SynthesisAgent:
    """Chronologies, résumés, tableaux, fiches, checklists (docs/05).

    Pour un dossier réellement persisté (`CaseProfile`, `CaseStorePort`,
    Sprint 26), produit le résumé exécutif/chronologique/documentaire en
    réutilisant `CaseSummaryGenerator.generate()` (Sprint 4) — jamais un
    second appel de modèle pour ce que ce générateur produit déjà — puis
    ajoute les livrables propres à cet agent que `CaseSummaryGenerator`
    ne couvre pas : un tableau structuré acteurs/faits/échéances, une
    fiche de synthèse et une checklist des points ouverts, tous agrégés
    de façon déterministe à partir du `CaseProfile`. La seule valeur
    ajoutée générative de cet agent est une note de synthèse narrative
    qui met ces livrables en forme selon le style rédactionnel du
    cabinet (`WritingStyleProfile`, lu via `WritingStyleEngine` —
    injecté dans le prompt, jamais réécrit par `apply_style()`, qui n'a
    pas ce rôle).

    Câblage (voir aussi docs/158-architecture-agent-synthese.md, patron
    établi par `tmis.agents.analysis_agent.AnalysisAgent` au Sprint 29) :
    - `TMISKernel.complete()` est le seul point d'appel à un modèle
      génératif (jamais un second client LLM) ;
    - `AIIntelligenceFabric.route()` choisit le modèle utilisé par ce
      `complete()` plutôt qu'un fournisseur fixe ;
    - `AIGovernancePlatform.explainability` enregistre, pour chaque
      exécution, un rapport d'explicabilité consultable.
    """

    name = "synthesis"

    def __init__(
        self,
        *,
        kernel: TMISKernel | None = None,
        case_store: CaseStorePort | None = None,
        summary_generator: SummaryGeneratorPort | None = None,
        writing_style_engine: WritingStyleEngine | None = None,
        fabric: AIIntelligenceFabric | None = None,
        governance: AIGovernancePlatform | None = None,
        firm_id: str = "default",
    ) -> None:
        self._kernel = kernel or TMISKernel()
        self._case_store: CaseStorePort = case_store or InMemoryCaseStore()
        self._summary_generator: SummaryGeneratorPort = summary_generator or CaseSummaryGenerator(
            self._kernel
        )
        self._writing_style_engine = writing_style_engine or WritingStyleEngine(
            KnowledgeSpace(InMemoryKnowledgeStore())
        )
        self._fabric = fabric
        self._governance = governance
        self._firm_id = firm_id

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        if agent_input.case_id is None:
            return AgentOutput(
                result=self._empty_result(),
                confidence=ConfidenceLevel.LOW,
                warnings=["No case_id provided in context: nothing to synthesize for this task."],
            )

        case_id = agent_input.case_id
        case_profile = self._case_store.get(case_id)
        if case_profile is None:
            return AgentOutput(
                result=self._empty_result(),
                confidence=ConfidenceLevel.LOW,
                warnings=[f"Case {case_id!r} was not found in the case store."],
            )

        case_summary = await self._summary_generator.generate(case_profile)

        table = self._build_table(case_profile)
        fact_sheet = self._build_fact_sheet(case_profile, case_summary)
        checklist = self._build_checklist(case_profile, case_summary)

        style_profile = self._writing_style_engine.get_or_create_profile(
            self._firm_id, _STYLE_AUTHOR
        )

        model_name, synthesis_note = await self._generate_synthesis_note(
            case_profile, case_summary, table, checklist, style_profile
        )

        warnings: list[str] = []
        if not case_profile.actors and not case_profile.facts and not case_profile.timeline:
            warnings.append(f"Case {case_id!r} carries no actors, facts, or timeline entries yet.")
        if case_profile.timeline_inconsistencies:
            warnings.append(
                f"{len(case_profile.timeline_inconsistencies)} timeline inconsistency(ies) "
                "reported for this case."
            )

        confidence = self._confidence_for(case_profile, warnings)

        self._record_explainability(
            agent_input=agent_input,
            case_profile=case_profile,
            model_name=model_name,
            table=table,
            checklist=checklist,
        )

        citation = Citation(
            source_id=case_profile.case_id,
            connector="case_store",
            excerpt=case_summary.executive_summary[:_EXCERPT_LENGTH],
            reference=case_profile.title,
        )

        return AgentOutput(
            result={
                "executive_summary": case_summary.executive_summary,
                "chronological_summary": case_summary.chronological_summary,
                "documentary_summary": case_summary.documentary_summary,
                "case_status": case_summary.case_status,
                "open_points": list(case_summary.open_points),
                "table": table,
                "fact_sheet": fact_sheet,
                "checklist": checklist,
                "synthesis_note": synthesis_note,
                "model": model_name,
            },
            citations=[citation],
            confidence=confidence,
            warnings=warnings,
        )

    @staticmethod
    def _empty_result() -> dict[str, object]:
        return {
            "executive_summary": "",
            "chronological_summary": "",
            "documentary_summary": "",
            "case_status": "",
            "open_points": [],
            "table": {"actors": [], "facts": [], "deadlines": []},
            "fact_sheet": {},
            "checklist": [],
            "synthesis_note": "",
            "model": "default",
        }

    def _build_table(self, case_profile: CaseProfile) -> dict[str, list[dict[str, object]]]:
        actors: list[dict[str, object]] = [
            {
                "id": actor.id,
                "name": actor.name,
                "type": actor.type.value,
                "role": self._actor_role(case_profile, actor),
            }
            for actor in case_profile.actors
        ]
        facts: list[dict[str, object]] = [
            {
                "id": fact.id,
                "description": fact.description,
                "confidence": fact.confidence,
                "dates": list(fact.dates),
            }
            for fact in case_profile.facts
        ]
        deadlines: list[dict[str, object]] = [
            {"id": task.id, "description": task.description, "done": task.done}
            for task in case_profile.tasks
            if not task.done
        ]
        return {"actors": actors, "facts": facts, "deadlines": deadlines}

    @staticmethod
    def _actor_role(case_profile: CaseProfile, actor: Actor) -> str | None:
        role = case_profile.actor_roles.get(actor.id)
        return role.value if role is not None else None

    def _build_fact_sheet(
        self, case_profile: CaseProfile, case_summary: CaseSummary
    ) -> dict[str, object]:
        open_issues = [
            issue for issue in case_profile.legal_issues if issue.status == IssueStatus.OPEN
        ]
        return {
            "title": case_profile.title,
            "case_status": case_summary.case_status,
            "clients": [actor.name for actor in case_profile.clients],
            "opposing_parties": [actor.name for actor in case_profile.opposing_parties],
            "lawyers": [actor.name for actor in case_profile.lawyers],
            "jurisdictions": [actor.name for actor in case_profile.jurisdictions],
            "document_count": len(case_profile.document_ids),
            "fact_count": len(case_profile.facts),
            "open_issue_count": len(open_issues),
        }

    def _build_checklist(
        self, case_profile: CaseProfile, case_summary: CaseSummary
    ) -> list[dict[str, object]]:
        checklist = [
            {"item": point, "done": False, "source": "case_summary"}
            for point in case_summary.open_points
        ]
        checklist.extend(
            {"item": task.description, "done": task.done, "source": "task"}
            for task in case_profile.tasks
        )
        return checklist

    async def _generate_synthesis_note(
        self,
        case_profile: CaseProfile,
        case_summary: CaseSummary,
        table: dict[str, list[dict[str, object]]],
        checklist: list[dict[str, object]],
        style_profile: WritingStyleProfile,
    ) -> tuple[str, str]:
        prompt = self._build_prompt(case_profile, case_summary, table, checklist, style_profile)
        model_name, provider_name = self._route_model(prompt)
        response = await self._kernel.complete(prompt, provider=provider_name)
        return model_name, response.text

    def _build_prompt(
        self,
        case_profile: CaseProfile,
        case_summary: CaseSummary,
        table: dict[str, list[dict[str, object]]],
        checklist: list[dict[str, object]],
        style_profile: WritingStyleProfile,
    ) -> str:
        open_items = [entry["item"] for entry in checklist if not entry["done"]]
        lines = [
            "Rédige une note de synthèse pour le dossier suivant, en te fondant "
            "uniquement sur les éléments déjà consolidés ci-dessous — ne réinvente "
            "aucun fait.",
            f"Dossier : {case_profile.title} ({case_summary.case_status})",
            f"Résumé exécutif déjà rédigé : {case_summary.executive_summary}",
            f"Acteurs : {len(table['actors'])}, faits : {len(table['facts'])}, "
            f"échéances ouvertes : {len(table['deadlines'])}",
            f"Points ouverts à traiter : {'; '.join(str(item) for item in open_items) or 'aucun'}",
        ]
        if style_profile.vocabulary:
            lines.append(f"Vocabulaire à privilégier : {', '.join(style_profile.vocabulary)}")
        if style_profile.favorite_expressions:
            expressions = ", ".join(style_profile.favorite_expressions)
            lines.append(f"Expressions favorites du cabinet : {expressions}")
        if style_profile.structure_preferences:
            lines.append(
                f"Préférences de structure : {', '.join(style_profile.structure_preferences)}"
            )
        return "\n".join(lines)

    def _route_model(self, prompt: str) -> tuple[str, str | None]:
        """Routes through the Fabric (Sprint 14) rather than a fixed
        provider — same pattern as `AnalysisAgent._route_model`."""
        if self._fabric is None:
            return "default", None

        decision = self._fabric.route(
            RoutingRequest(firm_id=self._firm_id, task_type="case_synthesis", prompt=prompt)
        )
        return decision.model.name, decision.model.provider

    def _confidence_for(
        self, case_profile: CaseProfile, warnings: list[str]
    ) -> ConfidenceLevel:
        if not case_profile.actors and not case_profile.facts and not case_profile.timeline:
            return ConfidenceLevel.LOW
        if warnings:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.HIGH

    def _record_explainability(
        self,
        *,
        agent_input: AgentInput,
        case_profile: CaseProfile,
        model_name: str,
        table: dict[str, list[dict[str, object]]],
        checklist: list[dict[str, object]],
    ) -> None:
        if self._governance is None:
            return
        steps = [
            f"Lecture du dossier {case_profile.case_id!r} via CaseStorePort.",
            "Résumé exécutif/chronologique/documentaire généré via "
            "CaseSummaryGenerator.generate().",
            f"Agrégation déterministe du tableau ({len(table['actors'])} acteur(s), "
            f"{len(table['facts'])} fait(s), {len(table['deadlines'])} échéance(s) ouverte(s)) "
            f"et de la checklist ({len(checklist)} point(s)) depuis le CaseProfile.",
            f"Note de synthèse narrative générée via TMISKernel.complete() ({model_name}), "
            "mise en forme selon le profil de style rédactionnel du cabinet.",
        ]

        self._governance.explainability.generate(
            self._firm_id,
            str(agent_input.task_id),
            summary=(
                f"Synthèse du dossier {case_profile.title!r} : {len(table['actors'])} acteur(s), "
                f"{len(table['facts'])} fait(s), {len(checklist)} point(s) de checklist."
            ),
            steps_followed=tuple(steps),
            agents_involved=(self.name,),
            models_used=(model_name,),
            documents_consulted=tuple(case_profile.document_ids),
        )
