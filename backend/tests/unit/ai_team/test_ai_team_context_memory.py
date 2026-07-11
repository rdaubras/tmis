from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.context.engine import ContextEngine
from tmis.ai_team.memory.store import InMemoryAgentMemoryStore


def test_document_analyst_only_sees_case_summary() -> None:
    engine = ContextEngine()
    mission_context = {
        "case_summary": "Litige commercial",
        "legal_research_result": "Art. 1103",
    }

    slice_ = engine.build_context_for("m1", AgentRole.DOCUMENT_ANALYST, mission_context)

    assert list(slice_.content) == ["case_summary"]


def test_quality_controller_sees_everything() -> None:
    engine = ContextEngine()
    mission_context = {"case_summary": "x", "drafting_result": "y", "reasoning_result": "z"}

    slice_ = engine.build_context_for("m1", AgentRole.QUALITY_CONTROLLER, mission_context)

    assert set(slice_.content) == set(mission_context)


def test_token_estimate_is_positive_for_non_empty_content() -> None:
    engine = ContextEngine()

    slice_ = engine.build_context_for(
        "m1", AgentRole.QUALITY_CONTROLLER, {"case_summary": "a reasonably long piece of text"}
    )

    assert slice_.token_estimate > 0


def test_trace_is_recorded_and_scoped_per_mission() -> None:
    engine = ContextEngine()
    engine.build_context_for("m1", AgentRole.DOCUMENT_ANALYST, {"case_summary": "a"})
    engine.build_context_for("m2", AgentRole.DOCUMENT_ANALYST, {"case_summary": "b"})

    trace_m1 = engine.trace_for_mission("m1")

    assert len(trace_m1) == 1
    assert trace_m1[0].mission_id == "m1"
    assert trace_m1[0].keys_included == ("case_summary",)


def test_short_term_memory_is_bounded() -> None:
    store = InMemoryAgentMemoryStore()
    for i in range(30):
        store.remember_short_term("agent-1", "m1", f"entry-{i}")

    recent = store.recent_short_term("agent-1", limit=100)

    assert len(recent) == 20
    assert recent[-1].content == "entry-29"


def test_long_term_memory_search_filters_by_tag() -> None:
    store = InMemoryAgentMemoryStore()
    store.remember_long_term("agent-1", "commercial lease insight", tags=frozenset({"commercial"}))
    store.remember_long_term("agent-1", "labor law insight", tags=frozenset({"social"}))

    results = store.search_long_term("agent-1", "commercial")

    assert len(results) == 1
    assert results[0].summary == "commercial lease insight"


def test_preferences_default_to_empty_and_are_settable() -> None:
    store = InMemoryAgentMemoryStore()

    assert store.get_preferences("agent-1").values == {}

    store.set_preference("agent-1", "tone", "formal")

    assert store.get_preferences("agent-1").values == {"tone": "formal"}


def test_memory_is_isolated_per_agent() -> None:
    store = InMemoryAgentMemoryStore()
    store.remember_short_term("agent-1", "m1", "for agent 1")
    store.remember_short_term("agent-2", "m1", "for agent 2")

    assert [e.content for e in store.recent_short_term("agent-1")] == ["for agent 1"]
    assert [e.content for e in store.recent_short_term("agent-2")] == ["for agent 2"]
