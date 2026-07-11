from tmis.ai_governance.lineage.engine import LineageEngine
from tmis.ai_governance.lineage.store import InMemoryLineageStore
from tmis.ai_governance.traceability.engine import TraceabilityEngine
from tmis.ai_governance.traceability.schemas import TraceEntryKind
from tmis.ai_governance.traceability.store import InMemoryTraceStore

FIRM = "firm-a"
PRODUCTION = "prod-1"


def _trace_engine() -> TraceabilityEngine:
    return TraceabilityEngine(InMemoryTraceStore())


def test_convenience_methods_record_the_right_kind() -> None:
    engine = _trace_engine()

    engine.record_user(FIRM, PRODUCTION, "user-1")
    engine.record_case(FIRM, PRODUCTION, "case-1")
    engine.record_model_version(FIRM, PRODUCTION, "gpt-4-legal", "2024-08")
    engine.record_prompt(FIRM, PRODUCTION, "prompt-1")
    engine.record_intermediate_response(FIRM, PRODUCTION, "resp-1", "Réponse intermédiaire")
    engine.record_human_validation(FIRM, PRODUCTION, "val-1", "Approuvé")
    engine.record_final_decision(FIRM, PRODUCTION, "dec-1", "Décision finale")

    trace = engine.trace(FIRM, PRODUCTION)

    assert [e.kind for e in trace] == [
        TraceEntryKind.USER,
        TraceEntryKind.CASE,
        TraceEntryKind.MODEL_VERSION,
        TraceEntryKind.PROMPT,
        TraceEntryKind.INTERMEDIATE_RESPONSE,
        TraceEntryKind.HUMAN_VALIDATION,
        TraceEntryKind.FINAL_DECISION,
    ]


def test_every_trace_entry_carries_a_unique_reference() -> None:
    engine = _trace_engine()

    entry = engine.record_model_version(FIRM, PRODUCTION, "gpt-4-legal", "2024-08")

    assert entry.reference == "gpt-4-legal@2024-08"


def test_trace_is_scoped_per_production() -> None:
    engine = _trace_engine()
    engine.record_user(FIRM, "prod-a", "user-1")

    assert engine.trace(FIRM, "prod-b") == []


def _lineage_engine() -> LineageEngine:
    return LineageEngine(InMemoryLineageStore())


def test_explain_with_no_revision_returns_a_single_element_chain() -> None:
    engine = _lineage_engine()
    engine.record_origin(FIRM, PRODUCTION, ("doc-1", "doc-2"), "user-1")

    explanation = engine.explain(FIRM, PRODUCTION)

    assert explanation.revision_chain == (PRODUCTION,)
    assert len(explanation.origin_records) == 1


def test_explain_walks_the_revision_chain_from_earliest_to_latest() -> None:
    engine = _lineage_engine()
    engine.record_origin(FIRM, "prod-v1", ("doc-1",), "user-1")
    engine.record_origin(FIRM, "prod-v2", ("doc-1",), "user-1", revised_from_id="prod-v1")
    engine.record_origin(FIRM, "prod-v3", ("doc-1",), "user-1", revised_from_id="prod-v2")

    explanation = engine.explain(FIRM, "prod-v3")

    assert explanation.revision_chain == ("prod-v1", "prod-v2", "prod-v3")


def test_explain_for_unknown_production_returns_empty_records() -> None:
    engine = _lineage_engine()

    explanation = engine.explain(FIRM, "unknown")

    assert explanation.origin_records == ()
    assert explanation.revision_chain == ("unknown",)
