from tmis.ai_fabric.comparison.engine import ComparisonEngine
from tmis.ai_fabric.consensus.engine import ConsensusEngine
from tmis.ai_fabric.consensus.schemas import ModelPosition
from tmis.ai_fabric.fusion.engine import FusionEngine

TEXT_VALID = "Le contrat est valide. Art. 1103 du Code civil impose la force obligatoire."
TEXT_INVALID = "Le contrat n'est pas valide. Aucune clause ne le rend opposable."


def test_comparison_engine_ranks_models_by_overall_score() -> None:
    engine = ComparisonEngine()

    result = engine.compare(
        "Le contrat est-il valide ?", {"gpt-x": TEXT_VALID, "claude-y": TEXT_VALID}
    )

    assert len(result.entries) == 2
    assert set(result.ranked_model_names) == {"gpt-x", "claude-y"}


def test_comparison_engine_rewards_citations() -> None:
    engine = ComparisonEngine()

    result = engine.compare(
        "prompt",
        {"with-citation": "Art. 1103 s'applique.", "without": "Cela s'applique parfois."},
    )

    with_citation = next(e for e in result.entries if e.model_name == "with-citation")
    without_citation = next(e for e in result.entries if e.model_name == "without")
    assert with_citation.overall_score >= without_citation.overall_score


def test_consensus_engine_with_no_positions_returns_empty_synthesis() -> None:
    engine = ConsensusEngine()

    outcome = engine.build_consensus("topic", [])

    assert outcome.synthesis == ""
    assert outcome.agreement_ratio == 1.0


def test_consensus_engine_with_single_position_uses_it_as_synthesis() -> None:
    engine = ConsensusEngine()
    position = ModelPosition("gpt-x", TEXT_VALID)

    outcome = engine.build_consensus("topic", [position])

    assert outcome.synthesis == TEXT_VALID
    assert outcome.divergences == ()


def test_consensus_engine_preserves_divergences_when_models_disagree() -> None:
    engine = ConsensusEngine()
    positions = [
        ModelPosition("gpt-x", TEXT_VALID, quality_score=0.9),
        ModelPosition("claude-y", TEXT_INVALID, quality_score=0.9),
    ]

    outcome = engine.build_consensus("validité du contrat", positions)

    assert outcome.has_persistent_divergence is True
    assert any("claude-y" in d for d in outcome.divergences) or any(
        "gpt-x" in d for d in outcome.divergences
    )


def test_consensus_engine_agreeing_positions_have_no_divergence() -> None:
    engine = ConsensusEngine()
    positions = [
        ModelPosition("gpt-x", TEXT_VALID),
        ModelPosition("claude-y", TEXT_VALID),
    ]

    outcome = engine.build_consensus("topic", positions)

    assert outcome.divergences == ()
    assert outcome.agreement_ratio == 1.0


def test_fusion_engine_preserves_every_source_and_its_provenance() -> None:
    engine = FusionEngine()
    positions = [ModelPosition("gpt-x", TEXT_VALID), ModelPosition("claude-y", TEXT_INVALID)]

    fused = engine.fuse(positions)

    assert [s.model_name for s in fused.sources] == ["gpt-x", "claude-y"]
    assert "gpt-x" in fused.fused_text
    assert "claude-y" in fused.fused_text
    assert fused.provenance == {"segment-1": "gpt-x", "segment-2": "claude-y"}


def test_fusion_engine_counts_citations_per_source() -> None:
    engine = FusionEngine()
    positions = [ModelPosition("gpt-x", TEXT_VALID)]

    fused = engine.fuse(positions)

    assert fused.sources[0].citation_count >= 1
