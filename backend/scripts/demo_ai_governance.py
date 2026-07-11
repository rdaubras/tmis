"""Demonstrates the AI Governance & Explainability Platform end to end
on a single fictional case, producing a complete explainability chain
from the initial question to the final, governed decision.

Run from `backend/`: `python -m scripts.demo_ai_governance`

Uses the same fictional cabinet as `demo_cabinet_knowledge.py`
(`firm-demo` / "Cabinet Démo Lefèvre & Associés") but composes only
`tmis.ai_governance` (Sprint 15) — no data from other modules is
touched. Every store is the in-memory reference implementation, so
this is safe to re-run freely and writes nothing to a real database.
"""

from tmis.ai_governance.audit.engine import AIAuditEngine
from tmis.ai_governance.bias_detection.engine import BiasDetectionEngine
from tmis.ai_governance.bootstrap import (
    get_ai_audit_engine,
    get_ai_governance_platform,
    get_bias_detection_engine,
    get_compliance_engine,
    get_confidence_engine,
    get_ethics_engine,
    get_hallucination_detection_engine,
    get_policy_engine,
    get_quality_engine,
    get_report_generator,
    get_risk_engine,
)
from tmis.ai_governance.compliance.engine import ComplianceEngine
from tmis.ai_governance.confidence.engine import GovernanceConfidenceEngine
from tmis.ai_governance.ethics.engine import EthicsEngine
from tmis.ai_governance.hallucination_detection.engine import HallucinationDetectionEngine
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.ai_governance.policy_engine.schemas import GovernancePolicyType, PolicyEvaluationContext
from tmis.ai_governance.provenance.schemas import ProvenanceGranularity, SourceType
from tmis.ai_governance.quality.engine import GovernanceQualityEngine
from tmis.ai_governance.reasoning_chain.schemas import ChainStageType
from tmis.ai_governance.reporting.schemas import ReportType
from tmis.ai_governance.risk_engine.engine import RiskEngine

FIRM_ID = "firm-demo"
FIRM_NAME = "Cabinet Démo Lefèvre & Associés"
ASSOCIATE = "Julien Moreau"
PARTNER = "Camille Lefèvre"
PRODUCTION_ID = "prod-bail-commercial-2026-01"

QUESTION = "Le bailleur peut-il résilier le bail commercial pour défaut de paiement des loyers ?"
DRAFT_EXCERPT = (
    "Le bailleur est fondé à demander la résiliation du bail commercial sur le fondement de "
    "la clause résolutoire expresse prévue à l'article 12 du contrat, dès lors que le "
    "commandement de payer visant cette clause est resté sans effet pendant plus d'un mois. "
    "Art. 1103 du Code civil impose par ailleurs la force obligatoire des conventions "
    "légalement formées."
)


def _print_section(title: str) -> None:
    print(f"\n--- {title} ---")


def demo() -> None:
    print(f"=== AI Governance & Explainability Platform — démonstration pour {FIRM_NAME} ===")
    print(f"Dossier fictif : {PRODUCTION_ID} — {QUESTION}\n")

    platform: AIGovernancePlatform = get_ai_governance_platform()

    _print_section("1. Reasoning Chain — chaîne logique complète")
    chain = platform.reasoning_chain
    chain.record_step(FIRM_ID, PRODUCTION_ID, ChainStageType.QUESTION, QUESTION)
    chain.record_step(
        FIRM_ID,
        PRODUCTION_ID,
        ChainStageType.ANALYSIS,
        "Analyse de la clause résolutoire et du commandement de payer.",
    )
    chain.record_step(
        FIRM_ID,
        PRODUCTION_ID,
        ChainStageType.RESEARCH,
        "Recherche jurisprudentielle sur l'effet de la clause résolutoire.",
    )
    chain.record_step(
        FIRM_ID,
        PRODUCTION_ID,
        ChainStageType.ARGUMENTS,
        "La clause résolutoire expresse est valable et son jeu automatique.",
    )
    chain.record_step(
        FIRM_ID,
        PRODUCTION_ID,
        ChainStageType.COUNTER_ARGUMENTS,
        "Le preneur pourrait invoquer un délai de grâce judiciaire.",
    )
    chain.record_step(
        FIRM_ID,
        PRODUCTION_ID,
        ChainStageType.CONSENSUS,
        "Les deux agents convergent : résiliation fondée sous réserve d'un délai de grâce.",
    )
    chain.record_step(
        FIRM_ID, PRODUCTION_ID, ChainStageType.VALIDATION, "Soumis à validation hiérarchique."
    )
    chain.record_step(FIRM_ID, PRODUCTION_ID, ChainStageType.DRAFT, DRAFT_EXCERPT)
    for step in chain.chain_for(FIRM_ID, PRODUCTION_ID).steps:
        print(f"  [{step.stage.value}] {step.summary}")

    _print_section("2. Provenance — chaque affirmation reliée à sa source")
    provenance = platform.provenance
    provenance.record(
        FIRM_ID,
        PRODUCTION_ID,
        granularity=ProvenanceGranularity.SENTENCE,
        locator="phrase-1",
        excerpt="clause résolutoire expresse prévue à l'article 12 du contrat",
        source_type=SourceType.INTERNAL_DOCUMENT,
        source_reference="Contrat de bail commercial, art. 12",
        produced_by_agent="Analyste documentaire",
        produced_by_model="gpt-4-legal",
    )
    provenance.record(
        FIRM_ID,
        PRODUCTION_ID,
        granularity=ProvenanceGranularity.SENTENCE,
        locator="phrase-2",
        excerpt="Art. 1103 du Code civil impose par ailleurs la force obligatoire",
        source_type=SourceType.STATUTE_ARTICLE,
        source_reference="Code civil, art. 1103",
        produced_by_agent="Rédacteur",
        produced_by_model="claude-legal",
    )
    for record in provenance.trace(FIRM_ID, PRODUCTION_ID):
        print(f"  [{record.granularity.value}] {record.excerpt!r} -> {record.source_reference}")

    _print_section("3. Traceability — chaîne complète, identifiants uniques")
    trace = platform.traceability
    trace.record_user(FIRM_ID, PRODUCTION_ID, ASSOCIATE)
    trace.record_case(FIRM_ID, PRODUCTION_ID, "dossier-bail-2026-01")
    trace.record_model_version(FIRM_ID, PRODUCTION_ID, "gpt-4-legal", "2024-08")
    trace.record_model_version(FIRM_ID, PRODUCTION_ID, "claude-legal", "4.5")
    trace.record_prompt(FIRM_ID, PRODUCTION_ID, "prompt-analyse-bail-v3")
    trace.record_intermediate_response(
        FIRM_ID, PRODUCTION_ID, "resp-1", "Synthèse de la clause résolutoire produite."
    )
    for entry in trace.trace(FIRM_ID, PRODUCTION_ID):
        print(f"  [{entry.kind.value}] {entry.reference} — {entry.detail}")

    _print_section("4. Decision Records — registre des décisions")
    decision = platform.decision_records.record(
        FIRM_ID,
        PRODUCTION_ID,
        context="Défaut de paiement des loyers depuis trois mois, commandement resté sans effet.",
        objective="Déterminer si le bailleur peut obtenir la résiliation du bail.",
        hypotheses_considered=(
            "La clause résolutoire produit son effet automatiquement.",
            "Le juge pourrait accorder un délai de grâce au preneur.",
        ),
        alternatives_considered=("Résiliation judiciaire pour manquement grave",),
        decision="Engager la procédure sur le fondement de la clause résolutoire expresse.",
        justification="Le commandement de payer est resté sans effet plus d'un mois, "
        "condition posée par la clause 12 du contrat.",
        impacts=("Le preneur devra quitter les lieux si le juge constate le jeu de la clause.",),
    )
    print(f"  décision enregistrée : {decision.decision}")

    _print_section("5. Confidence Engine — score décomposé")
    confidence_engine: GovernanceConfidenceEngine = get_confidence_engine()
    confidence = confidence_engine.score(
        PRODUCTION_ID,
        source_quality=0.85,
        reasoning_coherence=0.9,
        human_validation=0.0,
        multi_agent_consensus=0.8,
        model_stability=0.9,
    )
    print(f"  score global : {confidence.value:.2f} — {confidence.explanation}")

    _print_section("6. Risk Engine — risques classés par gravité")
    risk_engine: RiskEngine = get_risk_engine()
    risks = risk_engine.assess(
        citation_count=2,
        contradiction_count=0,
        source_age_days=200,
        confidence_value=confidence.value,
        human_validated=False,
    )
    for risk in risks:
        print(f"  [{risk.severity.value}] {risk.category.value} — {risk.explanation}")

    _print_section("7. Bias / Hallucination / Ethics — détection explicable")
    bias_engine: BiasDetectionEngine = get_bias_detection_engine()
    hallucination_engine: HallucinationDetectionEngine = get_hallucination_detection_engine()
    ethics_engine: EthicsEngine = get_ethics_engine()
    bias_findings = bias_engine.scan(DRAFT_EXCERPT)
    hallucination_alerts = hallucination_engine.scan(DRAFT_EXCERPT)
    ethics_findings = ethics_engine.screen(DRAFT_EXCERPT)
    print(f"  biais détectés : {len(bias_findings)}")
    print(f"  alertes d'hallucination : {len(hallucination_alerts)}")
    print(f"  alertes déontologiques : {len(ethics_findings)}")

    _print_section("8. Policy Engine — politiques du cabinet")
    policy_engine: PolicyEngine = get_policy_engine()
    policy_engine.create_policy(
        FIRM_ID,
        GovernancePolicyType.MANDATORY_VALIDATION_BEFORE_EXPORT,
        "Toute réponse concernant une résiliation doit être validée avant envoi au client.",
    )
    policy_engine.create_policy(
        FIRM_ID,
        GovernancePolicyType.MANDATORY_REVIEW_FOR_CASE_TYPE,
        "Les dossiers de baux commerciaux nécessitent une relecture associé.",
        case_type="bail_commercial",
    )
    export_evaluation = policy_engine.evaluate(
        PolicyEvaluationContext(
            firm_id=FIRM_ID,
            production_id=PRODUCTION_ID,
            is_export=True,
            case_type="bail_commercial",
            human_validated=False,
        )
    )
    print(f"  export autorisé avant validation : {export_evaluation.allowed}")
    for reason in export_evaluation.reasons:
        print(f"    - {reason}")

    _print_section("9. Human Validation — validation hiérarchique")
    validation_request = platform.human_validation.request_hierarchical(
        FIRM_ID, PRODUCTION_ID, ASSOCIATE, ((ASSOCIATE,), (PARTNER,))
    )
    platform.human_validation.decide(
        FIRM_ID, validation_request.id, ASSOCIATE, ValidationDecisionType.APPROVE
    )
    validated_request = platform.human_validation.decide(
        FIRM_ID, validation_request.id, PARTNER, ValidationDecisionType.APPROVE
    )
    print(f"  statut de validation : {validated_request.status.value}")

    _print_section("10. AI Audit — journal spécialisé")
    audit_engine: AIAuditEngine = get_ai_audit_engine()
    audit_engine.record(
        FIRM_ID,
        PRODUCTION_ID,
        ASSOCIATE,
        "draft_generated",
        prompt="prompt-analyse-bail-v3",
        model_name="claude-legal",
        cost_usd=0.03,
        duration_ms=1450,
        decision_id=decision.id,
        validation_id=validation_request.id,
    )
    print(f"  {len(audit_engine.list_for_firm(FIRM_ID))} entrée(s) d'audit enregistrée(s)")

    _print_section("11. Compliance — vérification finale avant export")
    compliance_engine: ComplianceEngine = get_compliance_engine()
    export_evaluation_after_validation = policy_engine.evaluate(
        PolicyEvaluationContext(
            firm_id=FIRM_ID,
            production_id=PRODUCTION_ID,
            is_export=True,
            case_type="bail_commercial",
            human_validated=True,
        )
    )
    verdict = compliance_engine.check(PRODUCTION_ID, export_evaluation_after_validation, risks)
    print(f"  conforme après validation : {verdict.compliant}")

    _print_section("12. Quality Engine — score global de gouvernance")
    quality_engine: GovernanceQualityEngine = get_quality_engine()
    quality = quality_engine.evaluate(
        PRODUCTION_ID,
        explainability_completeness=1.0,
        provenance_completeness=1.0,
        confidence_value=confidence.value,
        risk_absence=1.0 - min(1.0, len(risks) / 5),
        human_validation_coverage=1.0,
    )
    print(f"  score global de gouvernance : {quality.overall:.2f}")

    _print_section("13. Explainability Report — lisible par un avocat")
    explanation = platform.explainability.generate(
        FIRM_ID,
        PRODUCTION_ID,
        summary="Le bailleur peut engager la résiliation du bail commercial sur la base de la "
        "clause résolutoire expresse, sous réserve d'un possible délai de grâce judiciaire.",
        steps_followed=tuple(
            s.summary for s in chain.chain_for(FIRM_ID, PRODUCTION_ID).steps
        ),
        agents_involved=("Analyste documentaire", "Chercheur juridique", "Rédacteur"),
        models_used=("gpt-4-legal", "claude-legal"),
        legal_references=("Code civil, art. 1103", "Contrat de bail commercial, art. 12"),
        documents_consulted=("Contrat de bail commercial", "Commandement de payer"),
    )
    print(f"  résumé : {explanation.summary}")

    _print_section("14. Reporting — rapport d'explicabilité généré")
    report = get_report_generator().generate(
        ReportType.EXPLAINABILITY, FIRM_ID, PRODUCTION_ID, report=explanation
    )
    for section in report.sections:
        print(f"  [{section.title}] {section.content[:80]}")

    _print_section("15. Overview — toutes les informations consultables en une lecture")
    overview = platform.overview(
        FIRM_ID,
        PRODUCTION_ID,
        confidence=confidence,
        risks=tuple(risks),
        bias_findings=tuple(bias_findings),
        hallucination_alerts=tuple(hallucination_alerts),
        ethics_findings=tuple(ethics_findings),
    )
    print(f"  étapes de raisonnement : {len(overview.reasoning_chain.steps)}")
    print(f"  éléments de provenance : {len(overview.provenance)}")
    print(f"  entrées de traçabilité : {len(overview.trace)}")
    print(f"  décisions enregistrées : {len(overview.decisions)}")
    print(f"  demandes de validation : {len(overview.validations)}")
    print(f"  risques identifiés : {len(overview.risks)}")
    confidence_display = f"{overview.confidence.value:.2f}" if overview.confidence else "N/A"
    print(f"  confiance : {confidence_display}")

    print("\n=== Fin de la démonstration ===")


if __name__ == "__main__":
    demo()
