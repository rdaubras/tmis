"""End-to-end integration test for the Sprint 25 demo scenario (Phase
11): runs the fictional-cabinet copilot scenario through the real
bootstrap composition root, exercising ingestion, graph creation,
entity resolution, semantic search, human validation, governance,
quality scoring, analytics, and Legal Copilot integration together —
the same path `scripts/demo_legal_knowledge_graph.py` exercises for
its captured console output."""

from tmis.cabinet_knowledge.bootstrap import get_knowledge_space
from tmis.legal_knowledge_graph.bootstrap import get_lkg_demo_deps
from tmis.legal_knowledge_graph.demo.scenario import FIRM_ID, run_demo_scenario
from tmis.legal_knowledge_graph.entity_resolution.schemas import ResolutionStatus


async def test_demo_scenario_ingests_and_publishes_all_four_sources() -> None:
    deps = get_lkg_demo_deps()
    result = await run_demo_scenario(deps)

    knowledge_space = get_knowledge_space()
    for ingestion_result in (
        result.contract_result,
        result.contract_variant_result,
        result.jurisprudence_result,
        result.template_result,
    ):
        obj = knowledge_space.get(FIRM_ID, ingestion_result.knowledge_object_id)
        assert obj is not None
        assert obj.is_published is True


async def test_demo_scenario_produces_explainable_relations() -> None:
    deps = get_lkg_demo_deps()
    result = await run_demo_scenario(deps)

    assert "influence" in result.influence_explanation
    assert "s'applique à" in result.applies_to_explanation


async def test_demo_scenario_covers_all_three_entity_resolution_outcomes() -> None:
    deps = get_lkg_demo_deps()
    result = await run_demo_scenario(deps)

    assert result.same_name_match.status is ResolutionStatus.CONFIRMED
    assert result.same_name_match.score == 1.0
    assert result.override_match.status is ResolutionStatus.CONFIRMED
    assert result.override_match.decided_by is not None
    assert result.rejected_match.status is ResolutionStatus.REJECTED


async def test_demo_scenario_copilot_snapshot_has_all_five_non_empty_dimensions() -> None:
    deps = get_lkg_demo_deps()
    result = await run_demo_scenario(deps)

    snapshot = result.copilot_context.graph_context
    assert set(snapshot.keys()) == {
        "relevant_knowledge",
        "similar_documents",
        "historical_reasonings",
        "validated_templates",
        "identified_risks",
    }
    for dimension, values in snapshot.items():
        assert values, f"{dimension} should not be empty in the demo scenario"


async def test_demo_scenario_duplicate_node_has_lower_confidence_than_well_sourced_node() -> None:
    deps = get_lkg_demo_deps()
    result = await run_demo_scenario(deps)

    assert result.duplicate_quality_breakdown.duplicate_count > 0
    assert result.duplicate_quality_breakdown.confidence < result.quality_breakdown.confidence
