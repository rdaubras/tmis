from tmis.agents.contracts import AgentInput, AgentOutput, ConfidenceLevel
from tmis.ai.kernel.kernel import TMISKernel
from tmis.ai.schemas.citation import Citation
from tmis.ai_fabric.fabric import AIIntelligenceFabric
from tmis.ai_fabric.router.schemas import RoutingRequest
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.ports import CaseStorePort
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.document_intelligence.schemas.entities import EntityType, ExtractedEntity
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.storage.in_memory_store import InMemoryDocumentStore
from tmis.document_intelligence.storage.ports import DocumentStorePort

_ENTITY_GROUPS: dict[str, tuple[EntityType, ...]] = {
    "persons": (EntityType.PERSON,),
    "companies": (EntityType.COMPANY,),
    "dates": (EntityType.DATE,),
    "amounts": (EntityType.AMOUNT,),
    "jurisdictions": (EntityType.JURISDICTION,),
    "contracts_and_references": (
        EntityType.REFERENCE,
        EntityType.LAW_ARTICLE,
        EntityType.DECISION_REFERENCE,
    ),
}

_EXCERPT_LENGTH = 400
_PROMPT_TEXT_LENGTH = 2000


class AnalysisAgent:
    """Entity/fact extraction and inconsistency detection (docs/05).

    Reconnaît personnes, sociétés, faits, dates, contrats, événements,
    juridictions et montants à partir d'un `DocumentRecord` réellement
    persisté (`DocumentStorePort`, Sprint 26) et, si un `case_id` est
    fourni, du `CaseProfile` correspondant (`CaseStorePort`, Sprint 26).
    Les entités structurées et la chronologie brute réutilisent ce que
    le Document Intelligence Engine (Sprint 3) et le Case Intelligence
    Engine (Sprint 4) ont déjà extrait et consolidé — cet agent ne
    reconstruit ni un second extracteur d'entités ni un second
    détecteur d'incohérences ; il les expose sous le contrat `AgentPort`
    et y ajoute une synthèse narrative générative.

    Câblage (voir aussi docs/157-architecture-agent-analyse.md) :
    - `TMISKernel.complete()` est le seul point d'appel à un modèle
      génératif (jamais un second client LLM) ;
    - `AIIntelligenceFabric.route()` choisit le modèle utilisé par ce
      `complete()` plutôt qu'un fournisseur fixe ;
    - `AIGovernancePlatform.explainability` enregistre, pour chaque
      exécution, un rapport d'explicabilité consultable (pourquoi cette
      réponse, quelles étapes, quel modèle, quels documents).

    Ce Sprint 29 ne câble pas `platform_sdk.agent_sdk.BaseAgentPlugin` :
    l'audit Phase 0 a confirmé que ce patron sert exclusivement les
    plugins tiers de démonstration du Marketplace (`agent_fiscal`,
    `agent_droit_social`), avec une signature `run(context, agent_input)`
    incompatible avec le contrat `AgentPort.run(agent_input)` que
    l'`Orchestrator` invoque directement — l'utiliser ici romprait la
    contrainte "zéro changement de signature". Ce n'est donc pas "déjà
    le patron utilisé par un agent existant" au sens de ce module.
    """

    name = "analysis"

    def __init__(
        self,
        *,
        kernel: TMISKernel | None = None,
        document_store: DocumentStorePort | None = None,
        case_store: CaseStorePort | None = None,
        fabric: AIIntelligenceFabric | None = None,
        governance: AIGovernancePlatform | None = None,
        firm_id: str = "default",
    ) -> None:
        self._kernel = kernel or TMISKernel()
        self._document_store: DocumentStorePort = document_store or InMemoryDocumentStore()
        self._case_store: CaseStorePort = case_store or InMemoryCaseStore()
        self._fabric = fabric
        self._governance = governance
        self._firm_id = firm_id

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        document_id = agent_input.context.get("document_id")
        if not isinstance(document_id, str) or not document_id:
            return AgentOutput(
                result={"entities": {}, "inconsistencies": [], "timeline": []},
                confidence=ConfidenceLevel.LOW,
                warnings=["No document_id provided in context: nothing to analyze for this task."],
            )

        document = self._document_store.get(document_id)
        if document is None:
            return AgentOutput(
                result={"entities": {}, "inconsistencies": [], "timeline": []},
                confidence=ConfidenceLevel.LOW,
                warnings=[f"Document {document_id!r} was not found in the document store."],
            )

        case_profile: CaseProfile | None = None
        if agent_input.case_id is not None:
            case_profile = self._case_store.get(str(agent_input.case_id))

        entities = self._group_entities(document)
        inconsistencies = self._collect_inconsistencies(case_profile)
        timeline = self._build_timeline(document, case_profile)

        model_name, narrative = await self._generate_narrative(
            document, case_profile, entities, inconsistencies
        )

        warnings: list[str] = []
        if not document.entities:
            warnings.append(f"Document {document_id!r} carries no pre-extracted entities.")
        if agent_input.case_id is not None and case_profile is None:
            warnings.append(f"Case {agent_input.case_id} was not found in the case store.")
        warnings.extend(document.warnings)

        confidence = self._confidence_for(document, case_profile, warnings)

        self._record_explainability(
            agent_input=agent_input,
            document=document,
            case_profile=case_profile,
            model_name=model_name,
            entities=entities,
            inconsistencies=inconsistencies,
        )

        citation = Citation(
            source_id=document.document_id,
            connector="document_store",
            excerpt=document.ocr_text[:_EXCERPT_LENGTH],
            reference=document.filename,
        )

        return AgentOutput(
            result={
                "entities": entities,
                "inconsistencies": inconsistencies,
                "timeline": timeline,
                "narrative": narrative,
                "model": model_name,
            },
            citations=[citation],
            confidence=confidence,
            warnings=warnings,
        )

    def _group_entities(self, document: DocumentRecord) -> dict[str, list[dict[str, object]]]:
        grouped: dict[str, list[dict[str, object]]] = {key: [] for key in _ENTITY_GROUPS}
        for entity in document.entities:
            for group_name, types in _ENTITY_GROUPS.items():
                if entity.type in types:
                    grouped[group_name].append(self._entity_to_dict(entity))
                    break
        return grouped

    @staticmethod
    def _entity_to_dict(entity: ExtractedEntity) -> dict[str, object]:
        return {
            "type": entity.type.value,
            "value": entity.value,
            "confidence": entity.confidence,
        }

    def _collect_inconsistencies(self, case_profile: CaseProfile | None) -> list[dict[str, object]]:
        if case_profile is None:
            return []
        return [
            {
                "date": inconsistency.date,
                "reason": inconsistency.reason,
                "conflicting_descriptions": [entry.description for entry in inconsistency.entries],
            }
            for inconsistency in case_profile.timeline_inconsistencies
        ]

    def _build_timeline(
        self, document: DocumentRecord, case_profile: CaseProfile | None
    ) -> list[dict[str, object]]:
        if case_profile is not None:
            return [
                {
                    "date": entry.date,
                    "description": entry.description,
                    "document_ids": list(entry.document_ids),
                    "confidence": entry.confidence,
                }
                for entry in case_profile.timeline
            ]
        return [
            {
                "date": event.date,
                "description": event.description,
                "document_ids": [event.document_id],
                "confidence": event.confidence,
            }
            for event in document.timeline_events
        ]

    async def _generate_narrative(
        self,
        document: DocumentRecord,
        case_profile: CaseProfile | None,
        entities: dict[str, list[dict[str, object]]],
        inconsistencies: list[dict[str, object]],
    ) -> tuple[str, str]:
        prompt = self._build_prompt(document, case_profile, entities, inconsistencies)
        model_name, provider_name = self._route_model(prompt)
        response = await self._kernel.complete(prompt, provider=provider_name)
        return model_name, response.text

    def _build_prompt(
        self,
        document: DocumentRecord,
        case_profile: CaseProfile | None,
        entities: dict[str, list[dict[str, object]]],
        inconsistencies: list[dict[str, object]],
    ) -> str:
        entity_counts = ", ".join(f"{name}={len(values)}" for name, values in entities.items())
        lines = [
            "Analyse juridique du document suivant : synthétise les faits, entités et "
            "incohérences pertinents pour ce dossier.",
            f"Document : {document.filename} ({document.status.value})",
            f"Entités déjà reconnues : {entity_counts}",
            f"Incohérences de chronologie détectées : {len(inconsistencies)}",
        ]
        if case_profile is not None:
            lines.append(
                f"Dossier : {case_profile.title} "
                f"({len(case_profile.actors)} acteur(s), {len(case_profile.facts)} fait(s))"
            )
        lines.append(f"Texte du document (extrait) : {document.ocr_text[:_PROMPT_TEXT_LENGTH]}")
        return "\n".join(lines)

    def _route_model(self, prompt: str) -> tuple[str, str | None]:
        """Routes through the Fabric (Sprint 14) rather than a fixed
        provider: `RoutingDecision.model` already carries both the
        model name and its `provider`, so one `route()` call is
        enough — no second lookup back into the model registry."""
        if self._fabric is None:
            return "default", None

        decision = self._fabric.route(
            RoutingRequest(firm_id=self._firm_id, task_type="document_analysis", prompt=prompt)
        )
        return decision.model.name, decision.model.provider

    def _confidence_for(
        self,
        document: DocumentRecord,
        case_profile: CaseProfile | None,
        warnings: list[str],
    ) -> ConfidenceLevel:
        if not document.entities and case_profile is None:
            return ConfidenceLevel.LOW
        if warnings:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.HIGH

    def _record_explainability(
        self,
        *,
        agent_input: AgentInput,
        document: DocumentRecord,
        case_profile: CaseProfile | None,
        model_name: str,
        entities: dict[str, list[dict[str, object]]],
        inconsistencies: list[dict[str, object]],
    ) -> None:
        if self._governance is None:
            return
        entity_count = sum(len(values) for values in entities.values())
        steps = [
            f"Lecture du document {document.document_id!r} via DocumentStorePort.",
            f"Regroupement de {entity_count} entité(s) pré-extraite(s) par type.",
        ]
        if case_profile is not None:
            steps.append(
                f"Lecture du dossier {case_profile.case_id!r} via CaseStorePort "
                f"et report de {len(inconsistencies)} incohérence(s) de chronologie."
            )
        steps.append(f"Synthèse narrative générée via TMISKernel.complete() ({model_name}).")

        self._governance.explainability.generate(
            self._firm_id,
            str(agent_input.task_id),
            summary=(
                f"Analyse du document {document.filename!r} : {entity_count} entité(s), "
                f"{len(inconsistencies)} incohérence(s) de chronologie signalée(s)."
            ),
            steps_followed=tuple(steps),
            agents_involved=(self.name,),
            models_used=(model_name,),
            documents_consulted=(document.document_id,),
        )
