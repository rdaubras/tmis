"""Demonstrates the Legal Knowledge Graph & Semantic Intelligence
Platform end to end on a single fictional cabinet: ingestion, graph
creation, entity resolution, semantic search, human validation,
governance, quality scoring, analytics, and Legal Copilot usage.

Run from `backend/`: `python -m scripts.demo_legal_knowledge_graph`

Uses the same fictional cabinet as `demo_ai_governance.py` and
`demo_cabinet_knowledge.py` (`firm-demo` / "Cabinet Démo Lefèvre &
Associés"), but composes only `tmis.legal_knowledge_graph` (Sprint 25)
plus the Sprint 12/24 engines it reuses. Every store is the in-memory
reference implementation, so this is safe to re-run freely and writes
nothing to a real database.
"""

import asyncio

from tmis.legal_knowledge_graph.bootstrap import get_lkg_demo_deps
from tmis.legal_knowledge_graph.demo.scenario import FIRM_NAME, run_demo_scenario


def _print_section(title: str) -> None:
    print(f"\n--- {title} ---")


async def demo() -> None:
    print(f"=== Legal Knowledge Graph & Semantic Intelligence Platform — {FIRM_NAME} ===")

    deps = get_lkg_demo_deps()
    result = await run_demo_scenario(deps)

    _print_section("1. Phase 5 — Knowledge Ingestion Pipeline")
    print(f"  contrat ingéré      : {result.contract_result.knowledge_object_id}")
    print(f"    entités extraites : {result.contract_result.extracted_entity_labels}")
    print(
        f"    classification    : {result.contract_result.classification_category} "
        f"(confiance {result.contract_result.classification_confidence:.2f})"
    )
    print(f"  avenant ingéré       : {result.contract_variant_result.knowledge_object_id}")
    print(f"  jurisprudence ingérée: {result.jurisprudence_result.knowledge_object_id}")
    print(f"  modèle ingéré        : {result.template_result.knowledge_object_id}")

    _print_section("2. Phase 2 — Knowledge Graph Core: relations explicables")
    print(f"  {result.influence_explanation}")
    print(f"  {result.applies_to_explanation}")

    _print_section("3. Phase 4 — Entity Resolution")
    print(
        f"  ACME Corp SARL == ACME CORP SARL : score={result.same_name_match.score:.2f} "
        f"statut={result.same_name_match.status.value} (auto)"
    )
    print(
        f"  ACME Corp SARL == ACME SARL       : score={result.override_match.score:.2f} "
        f"statut={result.override_match.status.value} décidé par {result.override_match.decided_by}"
    )
    print(
        f"  ACME Corp SARL == Société Beta SAS: score={result.rejected_match.score:.2f} "
        f"statut={result.rejected_match.status.value} décidé par {result.rejected_match.decided_by}"
    )

    _print_section("4. Phase 3 — Semantic Engine: recherche par intention")
    for match in result.semantic_matches:
        print(f"  {match.node_id} — score {match.score:.3f}")

    _print_section("5. Phase 6 — Human Validation Loop")
    print(f"  taux d'acceptation du feedback sur la relation INFLUENCES : "
          f"{result.feedback_acceptance_rate:.0%}")

    _print_section("6. Phase 9 — Knowledge Quality Engine")
    print(
        f"  contrat (bien sourcé, sans doublon)  : "
        f"confiance={result.quality_breakdown.confidence:.2f}"
    )
    print(
        f"  concept ACME (doublons détectés)     : "
        f"confiance={result.duplicate_quality_breakdown.confidence:.2f} "
        f"(doublons={result.duplicate_quality_breakdown.duplicate_count})"
    )

    _print_section("7. Phase 7 — Copilot Integration: snapshot du graphe")
    for key, values in result.copilot_context.graph_context.items():
        print(f"  {key}: {values}")

    print("\n=== Fin de la démonstration ===")


if __name__ == "__main__":
    asyncio.run(demo())
