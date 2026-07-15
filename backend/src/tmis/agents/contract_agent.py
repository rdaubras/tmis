import difflib
from dataclasses import dataclass

from tmis.agents.contracts import AgentInput, AgentOutput, ConfidenceLevel
from tmis.ai.kernel.kernel import TMISKernel
from tmis.ai.schemas.citation import Citation
from tmis.ai_fabric.fabric import AIIntelligenceFabric
from tmis.ai_fabric.router.schemas import RoutingRequest
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.cabinet_knowledge.clauses.engine import ClauseEngine
from tmis.cabinet_knowledge.clauses.schemas import Clause, ClauseVariant
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.ports import CaseStorePort
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.storage.in_memory_store import InMemoryDocumentStore
from tmis.document_intelligence.storage.ports import DocumentStorePort

_DEFAULT_DOMAIN = LegalDomain.COMMERCIAL
_RISK_KEYWORDS = (
    "risque",
    "défavorable",
    "desequilibr",
    "déséquilibr",
    "abusif",
    "attention",
    "pénalisant",
    "penalisant",
)
_VARIANT_MATCH_THRESHOLD = 0.3
_EXCERPT_LENGTH = 400
_PROMPT_TEXT_LENGTH = 2000


@dataclass(frozen=True, slots=True)
class ContractVersionDiff:
    """A minimal, local diff between two `DocumentRecord.ocr_text` captures,
    at paragraph granularity — deliberately **not** `VersioningPort.compare()`.

    Phase 0 confirmed that `InMemoryVersioningService.compare()` operates on
    Legal Drafting Studio's `Section`/`Paragraph` model
    (`tmis.legal_drafting.versioning`), produced by that studio's own
    editing/snapshot flow — not on an arbitrarily uploaded `DocumentRecord`.
    Extending `VersioningPort` to a second document model it was never
    designed for would break the same "each port covers exactly what it was
    built for" boundary this codebase already enforces elsewhere (see
    docs/163-architecture-agent-contrats.md). This type exists only to carry
    the result of comparing two contract uploads' plain text — it is not a
    second versioning engine.
    """

    added_paragraphs: tuple[str, ...]
    removed_paragraphs: tuple[str, ...]
    changed_paragraphs: tuple[tuple[str, str], ...]


def _split_paragraphs(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]


def _diff_contract_paragraphs(text_a: str, text_b: str) -> ContractVersionDiff:
    paragraphs_a = _split_paragraphs(text_a)
    paragraphs_b = _split_paragraphs(text_b)
    matcher = difflib.SequenceMatcher(None, paragraphs_a, paragraphs_b)

    added: list[str] = []
    removed: list[str] = []
    changed: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            added.extend(paragraphs_b[j1:j2])
        elif tag == "delete":
            removed.extend(paragraphs_a[i1:i2])
        elif tag == "replace":
            common = min(i2 - i1, j2 - j1)
            changed.extend(
                zip(paragraphs_a[i1 : i1 + common], paragraphs_b[j1 : j1 + common], strict=True)
            )
            removed.extend(paragraphs_a[i1 + common : i2])
            added.extend(paragraphs_b[j1 + common : j2])

    return ContractVersionDiff(
        added_paragraphs=tuple(added),
        removed_paragraphs=tuple(removed),
        changed_paragraphs=tuple(changed),
    )


def _version_diff_to_dict(diff: ContractVersionDiff | None) -> dict[str, object] | None:
    if diff is None:
        return None
    return {
        "added_paragraphs": list(diff.added_paragraphs),
        "removed_paragraphs": list(diff.removed_paragraphs),
        "changed_paragraphs": [
            {"before": before, "after": after} for before, after in diff.changed_paragraphs
        ],
    }


class ContractAgent:
    """Analyse et comparaison de contrats (docs/05-strategie-multi-agents.md).

    Remplace le placeholder Sprint 1 par un câblage réel qui suit le patron
    établi par `AnalysisAgent` (Sprint 29) pour la partie génération/synthèse
    (voir docs/163-architecture-agent-contrats.md) :

    - la lecture du contrat n'est pas un nouveau pipeline : comme
      `AnalysisAgent`, cet agent lit un `DocumentRecord` réellement persisté
      (`DocumentStorePort`, Sprint 26) — jamais un second parseur de
      `raw_bytes` — et, si un `case_id` est fourni, le `CaseProfile`
      correspondant (`CaseStorePort`, Sprint 26) ;
    - la détection de clauses à risque et de clauses manquantes confronte le
      texte du contrat à la bibliothèque de clauses du cabinet
      (`ClauseEngine.search(firm_id, domain)`, Sprint 12) : c'est le seul
      point d'accès à cette bibliothèque, jamais contourné ni redéveloppé ;
      une clause du domaine absente du texte est reportée comme manquante,
      une clause présente est comparée à ses variantes connues pour repérer
      une formulation non standard ou une variante explicitement notée à
      risque ;
    - la comparaison de version, quand un second document est fourni
      (`compare_document_id`), est une comparaison de texte brut au niveau
      paragraphe (`ContractVersionDiff`, ci-dessus) — pas
      `VersioningPort.compare()`, qui ne couvre pas ce modèle de document
      (voir la Question Ouverte tranchée dans docs/163) ;
    - la synthèse de risques est, elle, réellement nouvelle et générative :
      comme `AnalysisAgent`/`JurisprudenceAgent`, elle passe par
      `AIIntelligenceFabric.route()` puis `TMISKernel.complete()` — jamais un
      second client LLM ni le `PromptRegistry` indépendant de
      `legal_copilot_framework.copilots.contrats` (démonstration Sprint 24,
      non câblée ici).

    `AIGovernancePlatform.explainability` enregistre, pour chaque exécution,
    un rapport consultable (combien de clauses confrontées, combien à
    risque/manquantes, quel modèle, quel dossier).
    """

    name = "contract"

    def __init__(
        self,
        *,
        kernel: TMISKernel | None = None,
        document_store: DocumentStorePort | None = None,
        case_store: CaseStorePort | None = None,
        clause_engine: ClauseEngine | None = None,
        fabric: AIIntelligenceFabric | None = None,
        governance: AIGovernancePlatform | None = None,
        firm_id: str = "default",
    ) -> None:
        self._kernel = kernel or TMISKernel()
        self._document_store: DocumentStorePort = document_store or InMemoryDocumentStore()
        self._case_store: CaseStorePort = case_store or InMemoryCaseStore()
        self._clause_engine = clause_engine or ClauseEngine(
            KnowledgeSpace(InMemoryKnowledgeStore())
        )
        self._fabric = fabric
        self._governance = governance
        self._firm_id = firm_id

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        document_id = agent_input.context.get("document_id")
        if not isinstance(document_id, str) or not document_id:
            return AgentOutput(
                result={"clauses": [], "version_diff": None, "synthesis": None, "model": None},
                confidence=ConfidenceLevel.LOW,
                warnings=["No document_id provided in context: nothing to analyze for this task."],
            )

        document = self._document_store.get(document_id)
        if document is None:
            return AgentOutput(
                result={"clauses": [], "version_diff": None, "synthesis": None, "model": None},
                confidence=ConfidenceLevel.LOW,
                warnings=[f"Document {document_id!r} was not found in the document store."],
            )

        domain = self._resolve_domain(agent_input.context.get("domain"))

        case_profile: CaseProfile | None = None
        if agent_input.case_id is not None:
            case_profile = self._case_store.get(agent_input.case_id)

        compare_document, compare_document_id = self._resolve_compare_document(agent_input)

        clauses = self._clause_engine.search(self._firm_id, domain=domain)
        findings = self._detect_clause_risks(document, clauses)

        version_diff: ContractVersionDiff | None = None
        if compare_document is not None:
            version_diff = _diff_contract_paragraphs(document.ocr_text, compare_document.ocr_text)

        warnings: list[str] = list(document.warnings)
        if not clauses:
            warnings.append(f"No clause found in the firm's library for domain {domain.value!r}.")
        if agent_input.case_id is not None and case_profile is None:
            warnings.append(f"Case {agent_input.case_id} was not found in the case store.")
        if compare_document_id is not None and compare_document is None:
            warnings.append(
                f"Document {compare_document_id!r} was not found in the document store."
            )

        model_name, synthesis = await self._generate_synthesis(
            document, case_profile, findings, version_diff
        )

        confidence = self._confidence_for(clauses, warnings)

        self._record_explainability(
            agent_input=agent_input,
            document=document,
            domain=domain,
            findings=findings,
            case_profile=case_profile,
            compare_document=compare_document,
            version_diff=version_diff,
            model_name=model_name,
        )

        citations = [
            Citation(
                source_id=document.document_id,
                connector="document_store",
                excerpt=document.ocr_text[:_EXCERPT_LENGTH],
                reference=document.filename,
            )
        ]
        if compare_document is not None:
            citations.append(
                Citation(
                    source_id=compare_document.document_id,
                    connector="document_store",
                    excerpt=compare_document.ocr_text[:_EXCERPT_LENGTH],
                    reference=compare_document.filename,
                )
            )

        return AgentOutput(
            result={
                "clauses": findings,
                "version_diff": _version_diff_to_dict(version_diff),
                "synthesis": synthesis,
                "model": model_name,
            },
            citations=citations,
            confidence=confidence,
            warnings=warnings,
        )

    def _resolve_compare_document(
        self, agent_input: AgentInput
    ) -> tuple[DocumentRecord | None, str | None]:
        compare_document_id = agent_input.context.get("compare_document_id")
        if not isinstance(compare_document_id, str) or not compare_document_id:
            return None, None
        return self._document_store.get(compare_document_id), compare_document_id

    @staticmethod
    def _resolve_domain(raw: object) -> LegalDomain:
        if isinstance(raw, str):
            try:
                return LegalDomain(raw)
            except ValueError:
                pass
        return _DEFAULT_DOMAIN

    def _detect_clause_risks(
        self, document: DocumentRecord, clauses: list[Clause]
    ) -> list[dict[str, object]]:
        text_lower = document.ocr_text.lower()
        findings: list[dict[str, object]] = []
        for clause in clauses:
            keyword = clause.clause_type.replace("_", " ").lower()
            present = keyword in text_lower or clause.title.lower() in text_lower
            if not present:
                findings.append(
                    {
                        "clause_id": clause.id,
                        "clause_type": clause.clause_type,
                        "title": clause.title,
                        "status": "missing",
                        "matched_variant_id": None,
                        "risk_notes": None,
                        "jurisprudence_refs": list(clause.jurisprudence_refs),
                    }
                )
                continue

            variant, risk_notes = self._match_variant(clause, text_lower)
            findings.append(
                {
                    "clause_id": clause.id,
                    "clause_type": clause.clause_type,
                    "title": clause.title,
                    "status": "present",
                    "matched_variant_id": variant.id if variant is not None else None,
                    "risk_notes": risk_notes,
                    "jurisprudence_refs": list(clause.jurisprudence_refs),
                }
            )
        return findings

    def _match_variant(
        self, clause: Clause, text_lower: str
    ) -> tuple[ClauseVariant | None, str | None]:
        best_variant: ClauseVariant | None = None
        best_score = -1.0
        for variant in clause.variants:
            score = self._overlap_score(variant.text, text_lower)
            if score > best_score:
                best_score = score
                best_variant = variant

        if best_variant is None:
            return None, None

        notes_lower = best_variant.notes.lower()
        if any(keyword in notes_lower for keyword in _RISK_KEYWORDS):
            return best_variant, best_variant.notes
        if best_score < _VARIANT_MATCH_THRESHOLD:
            return (
                best_variant,
                "Formulation non standard : ne correspond à aucune variante connue du cabinet.",
            )
        return best_variant, None

    @staticmethod
    def _overlap_score(variant_text: str, text_lower: str) -> float:
        words = {word for word in variant_text.lower().split() if len(word) > 3}
        if not words:
            return 0.0
        matched = sum(1 for word in words if word in text_lower)
        return matched / len(words)

    async def _generate_synthesis(
        self,
        document: DocumentRecord,
        case_profile: CaseProfile | None,
        findings: list[dict[str, object]],
        version_diff: ContractVersionDiff | None,
    ) -> tuple[str, str]:
        prompt = self._build_prompt(document, case_profile, findings, version_diff)
        model_name, provider_name = self._route_model(prompt)
        response = await self._kernel.complete(prompt, provider=provider_name)
        return model_name, response.text

    def _build_prompt(
        self,
        document: DocumentRecord,
        case_profile: CaseProfile | None,
        findings: list[dict[str, object]],
        version_diff: ContractVersionDiff | None,
    ) -> str:
        risky = [f for f in findings if f["status"] == "present" and f["risk_notes"]]
        missing = [f for f in findings if f["status"] == "missing"]

        lines = [
            "Analyse le contrat suivant : synthétise les clauses à risque, les "
            "clauses manquantes par rapport à la bibliothèque du cabinet, et les "
            "points de vigilance pour le client.",
            f"Document : {document.filename} ({document.status.value})",
            f"Clauses confrontées à la bibliothèque du cabinet : {len(findings)} "
            f"({len(risky)} à risque, {len(missing)} manquante(s))",
        ]
        for finding in risky:
            lines.append(
                f"- Clause à risque : {finding['title']} ({finding['clause_type']}) : "
                f"{finding['risk_notes']}"
            )
        for finding in missing:
            lines.append(f"- Clause manquante : {finding['title']} ({finding['clause_type']})")
        if case_profile is not None:
            lines.append(
                f"Dossier : {case_profile.title} ({len(case_profile.actors)} acteur(s))"
            )
        if version_diff is not None:
            lines.append(
                f"Comparaison de version : {len(version_diff.added_paragraphs)} paragraphe(s) "
                f"ajouté(s), {len(version_diff.removed_paragraphs)} supprimé(s), "
                f"{len(version_diff.changed_paragraphs)} modifié(s)."
            )
        lines.append(f"Texte du contrat (extrait) : {document.ocr_text[:_PROMPT_TEXT_LENGTH]}")
        return "\n".join(lines)

    def _route_model(self, prompt: str) -> tuple[str, str | None]:
        """Routes through the Fabric (Sprint 14), like `AnalysisAgent` and
        `JurisprudenceAgent`: `RoutingDecision.model` already carries both
        the model name and its `provider`, so one `route()` call is
        enough — no second lookup back into the model registry."""
        if self._fabric is None:
            return "default", None

        decision = self._fabric.route(
            RoutingRequest(
                firm_id=self._firm_id, task_type="contract_risk_synthesis", prompt=prompt
            )
        )
        return decision.model.name, decision.model.provider

    @staticmethod
    def _confidence_for(clauses: list[Clause], warnings: list[str]) -> ConfidenceLevel:
        if not clauses:
            return ConfidenceLevel.LOW
        if warnings:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.HIGH

    def _record_explainability(
        self,
        *,
        agent_input: AgentInput,
        document: DocumentRecord,
        domain: LegalDomain,
        findings: list[dict[str, object]],
        case_profile: CaseProfile | None,
        compare_document: DocumentRecord | None,
        version_diff: ContractVersionDiff | None,
        model_name: str,
    ) -> None:
        if self._governance is None:
            return

        missing_count = sum(1 for f in findings if f["status"] == "missing")
        risky_count = sum(1 for f in findings if f["status"] == "present" and f["risk_notes"])

        steps = [
            f"Lecture du contrat {document.document_id!r} via DocumentStorePort.",
            f"Confrontation de {len(findings)} clause(s) du domaine {domain.value!r} via "
            f"ClauseEngine.search() : {risky_count} à risque, {missing_count} manquante(s).",
        ]
        if case_profile is not None:
            steps.append(f"Lecture du dossier {case_profile.case_id!r} via CaseStorePort.")
        if compare_document is not None and version_diff is not None:
            steps.append(
                f"Comparaison de version avec le document {compare_document.document_id!r} "
                f"({len(version_diff.added_paragraphs)} ajouté(s), "
                f"{len(version_diff.removed_paragraphs)} supprimé(s), "
                f"{len(version_diff.changed_paragraphs)} modifié(s))."
            )
        steps.append(f"Synthèse de risques générée via TMISKernel.complete() ({model_name}).")

        documents_consulted = [document.document_id]
        if compare_document is not None:
            documents_consulted.append(compare_document.document_id)

        self._governance.explainability.generate(
            self._firm_id,
            str(agent_input.task_id),
            summary=(
                f"Analyse du contrat {document.filename!r} : {risky_count} clause(s) à "
                f"risque, {missing_count} clause(s) manquante(s)."
            ),
            steps_followed=tuple(steps),
            agents_involved=(self.name,),
            models_used=(model_name,),
            documents_consulted=tuple(documents_consulted),
        )
