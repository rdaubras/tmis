"""Demonstrates the Cabinet Knowledge Engine end to end with fictional
data for a single demo firm.

Run from `backend/`: `python -m scripts.demo_cabinet_knowledge`

Uses the same fictional cabinet as `seed_beta_pilot.py`
(`firm-demo` / "Cabinet Démo Lefèvre & Associés") but composes only
`tmis.cabinet_knowledge` (Sprint 12) — no data from other modules is
touched. Every store is the in-memory reference implementation, so
this is safe to re-run freely and writes nothing to a real database.
"""

from tmis.cabinet_knowledge.bootstrap import (
    get_approval_engine,
    get_best_practice_engine,
    get_clause_engine,
    get_evaluation_engine,
    get_feedback_engine,
    get_lesson_learned_engine,
    get_lineage_engine,
    get_playbook_engine,
    get_quality_engine,
    get_reasoning_pattern_engine,
    get_recommendation_engine,
    get_taxonomy_engine,
    get_template_engine,
    get_validation_engine,
    get_writing_style_engine,
)
from tmis.cabinet_knowledge.clauses.schemas import ClauseVariant
from tmis.cabinet_knowledge.feedback.schemas import FeedbackAction
from tmis.cabinet_knowledge.playbooks.schemas import PlaybookStep
from tmis.cabinet_knowledge.recommendations.schemas import RecommendationContext
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain
from tmis.cabinet_knowledge.validation.schemas import ValidationDecision
from tmis.legal_drafting.templates.schemas import DocumentType

FIRM_ID = "firm-demo"
FIRM_NAME = "Cabinet Démo Lefèvre & Associés"
ASSOCIATE = "Julien Moreau"
COLLABORATOR = "Sarah Nguyen"


def _validate_and_publish(object_id: str, title: str) -> None:
    validation = get_validation_engine()
    request = validation.submit_for_validation(FIRM_ID, object_id, requested_by=COLLABORATOR)
    validation.decide(FIRM_ID, request.id, ValidationDecision.APPROVE, reviewer=ASSOCIATE)
    get_approval_engine().publish(FIRM_ID, object_id, approver=ASSOCIATE)
    print(f"  -> validé par {ASSOCIATE} puis publié : {title}")


def demo() -> None:
    print(f"=== Cabinet Knowledge Engine — démonstration pour {FIRM_NAME} ===\n")

    print("--- Playbook : ouverture d'un dossier prud'homal ---")
    playbook = get_playbook_engine().create_playbook(
        FIRM_ID,
        "Ouverture d'un dossier prud'homal",
        "prudhommes",
        steps=(
            PlaybookStep(
                1,
                "Entretien client",
                "Recueillir les faits et les pièces disponibles",
                documents=("Contrat de travail", "Bulletins de salaire"),
                risks=("Délai de prescription de 12 mois",),
            ),
            PlaybookStep(
                2,
                "Constitution du dossier",
                "Rassembler les pièces et rédiger la requête",
                documents=("Requête introductive",),
            ),
        ),
        checklist=("Vérifier le délai de prescription", "Vérifier la compétence territoriale"),
        author=COLLABORATOR,
    )
    print(f"  Créé (brouillon) : {playbook.title} — {len(playbook.steps)} étapes")
    _validate_and_publish(playbook.id, playbook.title)
    instance = get_playbook_engine().start_instance(FIRM_ID, playbook.id, "dossier-rousseau-2026")
    get_playbook_engine().complete_step(FIRM_ID, instance.id, 1)
    progress = get_playbook_engine().progress(FIRM_ID, instance.id)
    print(f"  Instancié sur le dossier 'dossier-rousseau-2026' — progression : {progress:.0%}\n")

    print("--- Clause : non-concurrence ---")
    clause = get_clause_engine().create_clause(
        FIRM_ID,
        "Clause de non-concurrence standard",
        LegalDomain.COMMERCIAL,
        "non_concurrence",
        variants=(
            ClauseVariant(id="v1", text="Interdiction de concurrence pendant 24 mois, France"),
        ),
        author=COLLABORATOR,
        jurisprudence_refs=("Cass. soc., 10 juillet 2002, n° 00-45.135",),
    )
    print(f"  Créée (brouillon) : {clause.title}")
    _validate_and_publish(clause.id, clause.title)
    print()

    print("--- Modèle cabinet : mise en demeure ---")
    template = get_template_engine().create_template(
        FIRM_ID,
        "Mise en demeure standard du cabinet",
        DocumentType.MISE_EN_DEMEURE,
        structure=("En-tête cabinet", "Rappel des faits", "Sommation", "Délai de régularisation"),
        author=COLLABORATOR,
    )
    print(f"  Créé (brouillon) : {template.title}\n")

    print("--- Pattern de raisonnement : prescription prud'homale ---")
    pattern = get_reasoning_pattern_engine().create_pattern(
        FIRM_ID,
        "Prescription en matière de contestation de licenciement",
        context="licenciement contestation délai prescription",
        strategy="Invoquer la prescription de 12 mois si le délai est dépassé",
        arguments=("Article L1471-1 du Code du travail",),
        author=ASSOCIATE,
        confidence_level=0.8,
    )
    print(f"  Créé (réutilisable par le Legal Reasoning Engine, Sprint 6) : {pattern.title}\n")

    print("--- Bonne pratique & retour d'expérience ---")
    get_best_practice_engine().create(
        FIRM_ID,
        "Vérifier systématiquement le délai de prescription à l'ouverture",
        "Éviter toute forclusion en vérifiant le délai dès le premier entretien",
        LegalDomain.SOCIAL,
        source="retour d'expérience du cabinet",
        author=ASSOCIATE,
    )
    get_lesson_learned_engine().create(
        FIRM_ID,
        "Délai de prescription manqué sur un dossier antérieur",
        context="dossier clos en 2024",
        outcome="forclusion, dossier perdu",
        recommendation="vérifier systématiquement les délais dès l'ouverture",
        author=ASSOCIATE,
        related_case_reference="dossier-2024-042",
    )
    print("  Bonne pratique et retour d'expérience enregistrés (brouillons)\n")

    print("--- Style rédactionnel du cabinet ---")
    style = get_writing_style_engine().update_profile(
        FIRM_ID,
        ASSOCIATE,
        favorite_expressions=("Nous vous prions de bien vouloir",),
        signature_block="Bien cordialement,\nCabinet Démo Lefèvre & Associés",
    )
    _validate_and_publish(style.id, "Profil de style rédactionnel du cabinet")
    styled = get_writing_style_engine().apply_style(FIRM_ID, "Cher Monsieur,")
    print(f"  Texte stylé : {styled!r}\n")

    print("--- Taxonomie ---")
    taxonomy_nodes = get_taxonomy_engine().nodes_by_domain(LegalDomain.SOCIAL)
    print(f"  {len(taxonomy_nodes)} catégorie(s) disponibles pour le domaine social\n")

    print("--- Retour utilisateur sur la clause de non-concurrence ---")
    get_feedback_engine().submit(
        FIRM_ID,
        clause.id,
        FeedbackAction.ACCEPT,
        author=COLLABORATOR,
        comment="Parfait, utilisé tel quel",
    )
    print("  Retour ACCEPT enregistré\n")

    print("--- Score de qualité ---")
    quality = get_quality_engine().evaluate_and_store(FIRM_ID, clause.id)
    print(f"  Qualité de la clause : {quality.overall:.2f} (sur 1.0)\n")

    print("--- Traçabilité (lineage) ---")
    lineage = get_lineage_engine().explain(FIRM_ID, playbook.id)
    print(
        f"  Playbook version {lineage.current_version}, "
        f"{len(lineage.governance_events)} évènement(s) de gouvernance"
    )
    for event in lineage.governance_events:
        print(f"    {event.from_status.value} -> {event.to_status.value} par {event.actor}")
    print()

    print("--- Recommandations pour un nouveau dossier social ---")
    recommendations = get_recommendation_engine().recommend(
        FIRM_ID, RecommendationContext(keywords=("prescription", "prud'homal"))
    )
    for rec in recommendations:
        print(
            f"  [{rec.object_type.value}] {rec.title} "
            f"(score {rec.score:.2f}) — {rec.explanation}"
        )
    print()

    print("--- Évaluation globale du cabinet ---")
    evaluation = get_evaluation_engine().evaluate_firm(FIRM_ID)
    print(f"  Total connaissances : {evaluation.total_objects}")
    print(f"  Répartition par statut : {evaluation.by_status}")
    print(f"  Taux de validation : {evaluation.validation_rate:.0%}")
    print(f"  Score qualité moyen : {evaluation.average_quality_score:.2f}")
    print(f"  Taux d'acceptation des retours : {evaluation.feedback_acceptance_rate:.0%}")


if __name__ == "__main__":
    demo()
