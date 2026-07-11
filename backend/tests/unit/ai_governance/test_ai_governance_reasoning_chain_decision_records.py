import pytest

from tmis.ai_governance.decision_records.engine import DecisionRecordEngine
from tmis.ai_governance.decision_records.store import InMemoryDecisionRecordStore
from tmis.ai_governance.reasoning_chain.engine import ReasoningChainEngine
from tmis.ai_governance.reasoning_chain.schemas import ChainStageType, OutOfOrderStepError
from tmis.ai_governance.reasoning_chain.store import InMemoryReasoningChainStore

FIRM = "firm-a"
PRODUCTION = "prod-1"


def _chain_engine() -> ReasoningChainEngine:
    return ReasoningChainEngine(InMemoryReasoningChainStore())


def test_record_step_follows_the_sprint_default_pipeline_order() -> None:
    engine = _chain_engine()
    engine.record_step(FIRM, PRODUCTION, ChainStageType.QUESTION, "Le bail est-il résiliable ?")
    engine.record_step(FIRM, PRODUCTION, ChainStageType.ANALYSIS, "Analyse des clauses.")
    engine.record_step(FIRM, PRODUCTION, ChainStageType.DRAFT, "Brouillon rédigé.")

    chain = engine.chain_for(FIRM, PRODUCTION)

    assert [s.stage for s in chain.steps] == [
        ChainStageType.QUESTION,
        ChainStageType.ANALYSIS,
        ChainStageType.DRAFT,
    ]


def test_record_step_allows_multiple_steps_at_the_same_stage() -> None:
    engine = _chain_engine()
    engine.record_step(FIRM, PRODUCTION, ChainStageType.ARGUMENTS, "Argument 1")
    engine.record_step(FIRM, PRODUCTION, ChainStageType.ARGUMENTS, "Argument 2")

    chain = engine.chain_for(FIRM, PRODUCTION)

    assert len(chain.steps) == 2


def test_record_step_rejects_going_backward() -> None:
    engine = _chain_engine()
    engine.record_step(FIRM, PRODUCTION, ChainStageType.RESEARCH, "Recherche effectuée.")

    with pytest.raises(OutOfOrderStepError):
        engine.record_step(FIRM, PRODUCTION, ChainStageType.QUESTION, "Question posée trop tard.")


def test_to_graph_links_consecutive_steps() -> None:
    engine = _chain_engine()
    step_a = engine.record_step(FIRM, PRODUCTION, ChainStageType.QUESTION, "Question")
    step_b = engine.record_step(FIRM, PRODUCTION, ChainStageType.ANALYSIS, "Analyse")

    graph = engine.to_graph(FIRM, PRODUCTION)

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.edges[0].source_id == step_a.id
    assert graph.edges[0].target_id == step_b.id


def test_chain_for_unknown_production_returns_empty_chain() -> None:
    engine = _chain_engine()

    chain = engine.chain_for(FIRM, "unknown-production")

    assert chain.steps == []


def _decision_engine() -> DecisionRecordEngine:
    return DecisionRecordEngine(InMemoryDecisionRecordStore())


def test_decision_record_engine_records_and_lists_history() -> None:
    engine = _decision_engine()

    engine.record(
        FIRM,
        PRODUCTION,
        context="Analyse du bail",
        objective="Déterminer la résiliation",
        decision="Résiliation possible",
        justification="Clause résolutoire expresse activée",
    )

    history = engine.history(FIRM, PRODUCTION)
    assert len(history) == 1
    assert history[0].decision == "Résiliation possible"


def test_decision_record_history_is_append_only_across_calls() -> None:
    engine = _decision_engine()
    engine.record(
        FIRM, PRODUCTION, context="c1", objective="o1", decision="d1", justification="j1"
    )
    engine.record(
        FIRM, PRODUCTION, context="c2", objective="o2", decision="d2", justification="j2"
    )

    history = engine.history(FIRM, PRODUCTION)

    assert [r.decision for r in history] == ["d1", "d2"]


def test_decision_record_history_is_scoped_per_production() -> None:
    engine = _decision_engine()
    engine.record(
        FIRM, "prod-a", context="c", objective="o", decision="d", justification="j"
    )

    assert engine.history(FIRM, "prod-b") == []
