import time
from dataclasses import dataclass

from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.cabinet_knowledge.validation.schemas import ValidationDecision
from tmis.legal_copilot_framework.context_engine.schemas import CopilotContext
from tmis.legal_knowledge_graph.copilot_bridge.bridge import attach_graph_context
from tmis.legal_knowledge_graph.demo.deps import LkgDemoDeps
from tmis.legal_knowledge_graph.entity_resolution.schemas import ResolutionMatch
from tmis.legal_knowledge_graph.graph_core.schemas import GraphNodeType
from tmis.legal_knowledge_graph.human_validation.schemas import FeedbackAction
from tmis.legal_knowledge_graph.ingestion.schemas import IngestionResult, IngestionSourceType
from tmis.legal_knowledge_graph.quality.schemas import GraphQualityBreakdown
from tmis.legal_knowledge_graph.semantic_engine.schemas import SemanticMatch

FIRM_ID = "firm-demo"
FIRM_NAME = "Cabinet Démo Lefèvre & Associés"
PARTNER = "Camille Lefèvre"
ASSOCIATE = "Julien Moreau"

_CONTRACT_TEXT = (
    "Contrat de prestation de services conclu entre ACME Corp SARL et le "
    "cabinet, régi par l'article 1134 du Code civil imposant la bonne foi "
    "contractuelle. La clause de confidentialité de l'article 8 protège les "
    "informations échangées pendant la durée du contrat."
)
_CONTRACT_VARIANT_TEXT = (
    "Avenant au contrat de prestation conclu avec ACME CORP SARL, rappelant "
    "l'obligation de bonne foi contractuelle posée par l'article 1134 du "
    "Code civil et complétant la clause de confidentialité initiale."
)
_JURISPRUDENCE_TEXT = (
    "Cass. civ. 3e, 12 mars 2024 : la Cour de cassation juge que "
    "l'article 1134 du Code civil impose aux parties, dont Société Beta "
    "SAS, une obligation de bonne foi contractuelle dans l'exécution du "
    "contrat de prestation."
)
_TEMPLATE_TEXT = (
    "Modèle de mise en demeure pour manquement à l'obligation de bonne foi "
    "contractuelle, fondée sur l'article 1134 du Code civil, à adresser à "
    "ACME Corp SARL avant toute action en résiliation."
)
_SEARCH_QUERY = "clause de confidentialité et bonne foi contractuelle"


@dataclass(frozen=True, slots=True)
class DemoScenarioResult:
    """Every artefact the Phase 11 demo produces, captured once so the
    demo script (real console output) and the test suite (assertions)
    read from the same run rather than two divergent code paths."""

    contract_result: IngestionResult
    contract_variant_result: IngestionResult
    jurisprudence_result: IngestionResult
    template_result: IngestionResult
    argument_node_id: str
    influence_explanation: str
    applies_to_explanation: str
    same_name_match: ResolutionMatch
    override_match: ResolutionMatch
    rejected_match: ResolutionMatch
    semantic_matches: tuple[SemanticMatch, ...]
    feedback_acceptance_rate: float
    quality_breakdown: GraphQualityBreakdown
    duplicate_quality_breakdown: GraphQualityBreakdown
    copilot_context: CopilotContext


async def _ingest_and_publish(
    deps: LkgDemoDeps, source_type: IngestionSourceType, title: str, text: str
) -> IngestionResult:
    result = await deps.ingestion.ingest(FIRM_ID, source_type, title, text, ASSOCIATE)
    deps.validation.decide(
        FIRM_ID, result.validation_request_id, ValidationDecision.APPROVE, reviewer=PARTNER
    )
    deps.ingestion.publish(FIRM_ID, result.knowledge_object_id, approver=PARTNER)
    return result


def _concept_node_id(deps: LkgDemoDeps, graph_node_id: str, label: str) -> str:
    for node in deps.graph.neighbors(FIRM_ID, graph_node_id):
        if node.label == label:
            return node.id
    raise KeyError(label)


async def run_demo_scenario(deps: LkgDemoDeps) -> DemoScenarioResult:
    """One fictional cabinet, several documents, one contract dispute:
    ingestion → graph creation → entity resolution → semantic search →
    human validation → governance → quality → Copilot usage — every
    step exercised with data traceable back to this function, per the
    sprint's "chaque connaissance doit être traçable" constraint."""

    # Phase 5 — Knowledge Ingestion Pipeline (three fictional sources)
    contract_result = await _ingest_and_publish(
        deps, IngestionSourceType.CONTRACT, "Contrat de prestation ACME", _CONTRACT_TEXT
    )
    contract_variant_result = await _ingest_and_publish(
        deps,
        IngestionSourceType.CONTRACT,
        "Avenant au contrat de prestation ACME",
        _CONTRACT_VARIANT_TEXT,
    )
    jurisprudence_result = await _ingest_and_publish(
        deps,
        IngestionSourceType.IMPORTED_JURISPRUDENCE,
        "Cass. civ. 3e, 12 mars 2024",
        _JURISPRUDENCE_TEXT,
    )
    template_result = await _ingest_and_publish(
        deps, IngestionSourceType.TEMPLATE, "Modèle de mise en demeure", _TEMPLATE_TEXT
    )

    # Phase 2 — Knowledge Graph Core: an explainable ARGUMENT node,
    # linked to the article-1134 concept extracted from the contract,
    # and the jurisprudence linked as applying to the contract.
    article_node_id = _concept_node_id(deps, contract_result.graph_node_id, "article 1134")
    argument_node = deps.graph.add_node(
        FIRM_ID,
        GraphNodeType.ARGUMENT,
        f"{contract_result.knowledge_object_id}::argument-bonne-foi",
        "Argument de bonne foi contractuelle",
    )
    influence_relation = deps.graph.link(
        FIRM_ID, article_node_id, argument_node.id, RelationType.INFLUENCES
    )
    applies_to_relation = deps.graph.link(
        FIRM_ID,
        jurisprudence_result.graph_node_id,
        contract_result.graph_node_id,
        RelationType.APPLIES_TO,
    )
    deps.graph.link(
        FIRM_ID, contract_result.graph_node_id, argument_node.id, RelationType.RELATED_TO
    )
    risk_node = deps.graph.add_node(
        FIRM_ID,
        GraphNodeType.RISK,
        f"{contract_result.knowledge_object_id}::risque-resiliation",
        "Risque de résiliation anticipée pour manquement à la bonne foi contractuelle",
    )
    deps.graph.link(FIRM_ID, contract_result.graph_node_id, risk_node.id, RelationType.RELATED_TO)

    # Phase 4 — Entity Resolution: three outcomes (auto-confirmed exact
    # match, human-confirmed override, human-rejected non-match) so the
    # demo shows the full decision space, not just the happy path.
    acme_node_id = _concept_node_id(deps, contract_result.graph_node_id, "ACME Corp SARL")
    acme_variant_node_id = _concept_node_id(
        deps, contract_variant_result.graph_node_id, "ACME CORP SARL"
    )
    beta_node_id = _concept_node_id(deps, jurisprudence_result.graph_node_id, "Société Beta SAS")

    same_name_match = await deps.entity_resolution.propose_match(
        FIRM_ID, acme_node_id, acme_variant_node_id
    )

    abbreviated_node = deps.graph.add_node(
        FIRM_ID, GraphNodeType.CONCEPT, "manual::acme-sarl-abrege", "ACME SARL"
    )
    pending_override = await deps.entity_resolution.propose_match(
        FIRM_ID, acme_node_id, abbreviated_node.id
    )
    override_match = deps.entity_resolution.confirm(FIRM_ID, pending_override.id, PARTNER)

    pending_rejection = await deps.entity_resolution.propose_match(
        FIRM_ID, acme_node_id, beta_node_id
    )
    rejected_match = deps.entity_resolution.reject(FIRM_ID, pending_rejection.id, PARTNER)

    # Phase 3 — Semantic Engine: intent search over every indexed node.
    started_at = time.monotonic()
    semantic_matches = tuple(
        await deps.semantic.search_by_intent(FIRM_ID, _SEARCH_QUERY, top_k=3)
    )
    search_duration_ms = (time.monotonic() - started_at) * 1000

    # Phase 6 — Human Validation Loop: annotate the new INFLUENCES
    # relation, then measure the acceptance rate of feedback on it.
    deps.feedback.submit(
        FIRM_ID,
        influence_relation.id,
        FeedbackAction.ACCEPT,
        PARTNER,
        "Confirmé : l'article 1134 fonde bien l'argument de bonne foi.",
    )
    deps.feedback.submit(
        FIRM_ID,
        influence_relation.id,
        FeedbackAction.ANNOTATE,
        ASSOCIATE,
        "À citer dans les conclusions.",
    )
    feedback_acceptance_rate = deps.feedback.acceptance_rate(FIRM_ID, influence_relation.id)

    # Phase 8 — Knowledge Governance: the jurisprudence node is marked
    # confidential with a 10-year retention; ABAC attributes are
    # handed off to `identity_platform`, never re-decided here.
    deps.governance.set_policy(
        FIRM_ID,
        jurisprudence_result.graph_node_id,
        confidentiality_level="confidential",
        retention_days=3650,
    )

    # Phase 9 — Knowledge Quality Engine: the contract node (well
    # sourced, no duplicates) versus the ACME concept node (now
    # carrying two SAME_AS duplicates).
    quality_breakdown = deps.quality.evaluate(FIRM_ID, contract_result.graph_node_id)
    duplicate_quality_breakdown = deps.quality.evaluate(FIRM_ID, acme_node_id)

    # Phase 10 — Knowledge Analytics
    deps.analytics.record_graph_size(
        len(deps.graph.list_nodes(FIRM_ID)),
        sum(len(deps.graph.relations_for(FIRM_ID, n.id)) for n in deps.graph.list_nodes(FIRM_ID)),
        firm_id=FIRM_ID,
    )
    deps.analytics.record_search(search_duration_ms, len(semantic_matches), firm_id=FIRM_ID)
    deps.analytics.record_answer_quality(quality_breakdown.confidence, firm_id=FIRM_ID)
    deps.analytics.record_human_validation(firm_id=FIRM_ID)
    for _ in (contract_result, contract_variant_result, jurisprudence_result, template_result):
        deps.analytics.record_enrichment(firm_id=FIRM_ID)

    # Phase 7 — Copilot Integration: a copilot's ordinary
    # `ContextEngine.build()` context, enriched with the graph's own
    # snapshot for the contract node, via the bridge function only.
    base_context = deps.context_engine.build(FIRM_ID, ASSOCIATE, case_id="dossier-D-2026-042")
    snapshot = await deps.copilot_query.build_snapshot(FIRM_ID, contract_result.graph_node_id)
    copilot_context = attach_graph_context(base_context, snapshot)

    return DemoScenarioResult(
        contract_result=contract_result,
        contract_variant_result=contract_variant_result,
        jurisprudence_result=jurisprudence_result,
        template_result=template_result,
        argument_node_id=argument_node.id,
        influence_explanation=deps.graph.explain(FIRM_ID, influence_relation.id),
        applies_to_explanation=deps.graph.explain(FIRM_ID, applies_to_relation.id),
        same_name_match=same_name_match,
        override_match=override_match,
        rejected_match=rejected_match,
        semantic_matches=semantic_matches,
        feedback_acceptance_rate=feedback_acceptance_rate,
        quality_breakdown=quality_breakdown,
        duplicate_quality_breakdown=duplicate_quality_breakdown,
        copilot_context=copilot_context,
    )
