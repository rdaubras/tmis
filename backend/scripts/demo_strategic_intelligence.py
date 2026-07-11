"""Demonstrates the Strategic Litigation & Advisory Intelligence (SLAI)
engine on several fictional cases, showing that each case produces a
different set of strategies, risks, and recommended next actions.

Run from `backend/`: `python -m scripts.demo_strategic_intelligence`

Uses a separate fictional firm (`firm-demo-si` / "Cabinet Démo Lefèvre
& Associés — Contentieux") so it never touches data from other demo
scripts. Every store is the in-memory reference implementation, so
this is safe to re-run freely.
"""

from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.strategic_intelligence.bootstrap import (
    get_action_planner_engine,
    get_decision_support_engine,
    get_evidence_gap_engine,
    get_hypothesis_lab_engine,
    get_opportunity_engine,
    get_probability_engine,
    get_risk_matrix_engine,
    get_simulation_engine,
    get_strategy_engine,
    get_strategy_review_adapter,
    get_timeline_engine,
    get_tradeoff_engine,
)
from tmis.strategic_intelligence.decision_support.schemas import StrategyMetrics
from tmis.strategic_intelligence.strategy_engine.schemas import Strategy
from tmis.strategic_intelligence.timeline.schemas import StrategicTimelineEntry, TimelineEntryKind

FIRM_ID = "firm-demo-si"
FIRM_NAME = "Cabinet Démo Lefèvre & Associés — Contentieux"


def _print_section(title: str) -> None:
    print(f"\n--- {title} ---")


def _demo_strategy(strategy: Strategy) -> None:
    print(f"  [{strategy.strategy_type}] confiance={strategy.confidence}")
    for limitation in strategy.limitations:
        print(f"    limite: {limitation}")


def run_dossier_licenciement() -> list[Strategy]:
    _print_section("Dossier 1 — Licenciement contesté (question de la Vision du sprint)")
    print('Question : "Comment défendre ce salarié ?"')

    hypothesis_lab = get_hypothesis_lab_engine()
    h1 = hypothesis_lab.create(
        FIRM_ID, "dossier-licenciement-2026-03", "Licenciement sans cause réelle et sérieuse"
    )
    h2 = hypothesis_lab.create(
        FIRM_ID, "dossier-licenciement-2026-03", "Discrimination syndicale sous-jacente"
    )
    comparison = hypothesis_lab.compare(FIRM_ID, h1.id, h2.id)
    print(f"Comparaison des hypothèses : similarité={comparison.similarity}")

    strategies = get_strategy_engine().generate(
        case_id="dossier-licenciement-2026-03",
        question="Comment défendre ce salarié ?",
        hypotheses=(h1.description, h2.description),
        main_arguments=("Absence de motif valable", "Contexte syndical du salarié"),
        counter_arguments=("Faute grave alléguée par l'employeur",),
        available_evidence=("Bulletins de salaire", "Échanges emails"),
        missing_evidence=("Témoignage d'un collègue",),
    )
    for strategy in strategies:
        _demo_strategy(strategy)

    top = strategies[0]
    risk = get_risk_matrix_engine().evaluate(
        top.id,
        documentary_solidity=0.6,
        reasoning_coherence=0.7,
        evidence_dependency=0.5,
        uncertainty=0.4,
        requires_human_validation=True,
    )
    print(f"Risque de « {top.strategy_type} » : {risk.score} — {risk.explanation}")

    opportunities = get_opportunity_engine().find(
        top.id,
        main_arguments=top.main_arguments,
        unused_hypotheses=(h2.description,),
        missing_evidence=top.missing_evidence,
    )
    print(f"{len(opportunities)} opportunité(s) identifiée(s), toutes justifiées.")

    gaps = get_evidence_gap_engine().identify(top.id, top.missing_evidence)
    for gap in gaps:
        print(f"  Élément manquant : {gap.missing_evidence} — {gap.potential_impact}")

    planner = get_action_planner_engine()
    planner.add_step(FIRM_ID, top.id, "Envoyer une mise en demeure", "procédure")
    planner.add_step(FIRM_ID, top.id, "Recueillir le témoignage du collègue", "preuve")
    print(f"Plan d'action : {len(planner.list_for_strategy(FIRM_ID, top.id))} étape(s).")

    return strategies


def run_dossier_bail_commercial() -> list[Strategy]:
    _print_section("Dossier 2 — Résiliation de bail commercial pour impayés")
    print('Question : "Comment sécuriser la résiliation du bail ?"')

    strategies = get_strategy_engine().generate(
        case_id="dossier-bail-2026-02",
        question="Comment sécuriser la résiliation du bail commercial ?",
        candidate_types=(
            "Commandement de payer visant la clause résolutoire",
            "Assignation en référé-expulsion",
            "Négociation d'un protocole d'accord",
        ),
        main_arguments=("Clause résolutoire expresse activée", "Loyers impayés depuis 4 mois"),
        counter_arguments=("Le locataire invoque une exception d'inexécution",),
        available_evidence=("Contrat de bail", "Relevés d'impayés"),
        missing_evidence=("Preuve de la mise en demeure notifiée",),
    )
    for strategy in strategies:
        _demo_strategy(strategy)

    print(
        "Types de stratégies différents du Dossier 1 : "
        f"{sorted({s.strategy_type for s in strategies})}"
    )

    a, b = strategies[0], strategies[1]
    tradeoff = get_tradeoff_engine().compare(
        a.id,
        b.id,
        advantages_a=("Procédure rapide",),
        advantages_b=("Solution négociée, moins conflictuelle",),
        risks_a=("Contestation possible en référé",),
        risks_b=("Contestation possible en référé",),
    )
    print(f"Compromis entre « {a.strategy_type} » et « {b.strategy_type} » :")
    print(f"  risques partagés : {tradeoff.shared_risks}")

    comparison = get_decision_support_engine().compare(
        [
            StrategyMetrics(s.id, s.strategy_type, s.confidence, 0.6, 0.4, 0.5, 60)
            for s in strategies
        ]
    )
    print(f"Comparaison ({len(comparison.metrics)} stratégies) — {comparison.disclaimer}")

    timeline = get_timeline_engine().build(
        [
            StrategicTimelineEntry(
                "2026-02-01", TimelineEntryKind.FACT, "Premier impayé constaté", "ref-bail-1"
            ),
            StrategicTimelineEntry(
                "2026-03-15",
                TimelineEntryKind.DEADLINE,
                "Fin du délai d'un mois après commandement",
                "ref-bail-2",
            ),
            StrategicTimelineEntry(
                "2026-02-10",
                TimelineEntryKind.PROPOSED_ACTION,
                "Notifier le commandement de payer",
                "ref-bail-3",
            ),
        ]
    )
    print("Chronologie triée :", [e.date for e in timeline])

    probability = get_probability_engine().assess(
        "Recevabilité du commandement de payer", supporting_count=4, contradicting_count=1
    )
    print(
        f"Vraisemblance (sous-élément) : {probability.likelihood.value} — {probability.rationale}"
    )

    simulation = get_simulation_engine().run(
        "dossier-bail-2026-02",
        {s.id: " ".join(s.main_arguments) for s in strategies},
        ("impayés",),
    )
    print(f"Simulation « et si le locataire régularisait les impayés ? » : {simulation.notes}")

    return strategies


def run_dossier_consommation() -> list[Strategy]:
    _print_section("Dossier 3 — Litige de consommation (vice caché)")
    print('Question : "Quelle voie privilégier pour le consommateur lésé ?"')

    strategies = get_strategy_engine().generate(
        case_id="dossier-conso-2026-04",
        question="Quelle voie privilégier pour le consommateur lésé ?",
        candidate_types=(
            "Médiation de la consommation",
            "Action en garantie des vices cachés",
            "Résolution amiable avec le vendeur",
        ),
        main_arguments=("Défaut caché rendant le bien impropre à son usage",),
        available_evidence=("Facture d'achat", "Rapport d'expertise"),
        missing_evidence=("Preuve de l'antériorité du vice",),
    )
    for strategy in strategies:
        _demo_strategy(strategy)

    print(
        "Types de stratégies différents des Dossiers 1 et 2 : "
        f"{sorted({s.strategy_type for s in strategies})}"
    )

    review = get_strategy_review_adapter()
    request = review.request_review(FIRM_ID, strategies[0].id, "avocat-3", ("associe-2",))
    print(
        f"Revue demandée pour « {strategies[0].strategy_type} » — statut : "
        f"{request.status.value}"
    )
    review.decide(FIRM_ID, request.id, "associe-2", ValidationDecisionType.APPROVE)
    print(f"Après décision : validée = {review.is_validated(FIRM_ID, strategies[0].id)}")

    return strategies


def main() -> None:
    print(f"=== Démonstration SLAI — {FIRM_NAME} ===")

    licenciement = run_dossier_licenciement()
    bail = run_dossier_bail_commercial()
    conso = run_dossier_consommation()

    _print_section("Synthèse")
    all_types = {
        "licenciement": {s.strategy_type for s in licenciement},
        "bail_commercial": {s.strategy_type for s in bail},
        "consommation": {s.strategy_type for s in conso},
    }
    for dossier, types in all_types.items():
        print(f"  {dossier}: {sorted(types)}")
    print(
        "\nAucune stratégie n'a été présentée comme une décision définitive ; "
        "chacune reste une proposition soumise à validation humaine."
    )


if __name__ == "__main__":
    main()
