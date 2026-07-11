from tmis.ai_team.human_loop.engine import HumanLoopEngine
from tmis.ai_team.human_loop.schemas import HumanDecisionType
from tmis.ai_team.human_loop.store import InMemoryHumanDecisionStore


def _engine() -> HumanLoopEngine:
    return HumanLoopEngine(InMemoryHumanDecisionStore())


def test_approve_is_recorded() -> None:
    engine = _engine()

    decision = engine.approve("m1", "lawyer-1")

    assert decision.decision_type is HumanDecisionType.APPROVE
    assert decision.mission_id == "m1"
    assert decision.actor_id == "lawyer-1"


def test_exclude_agent_records_the_agent_id_in_payload() -> None:
    engine = _engine()

    decision = engine.exclude_agent("m1", "lawyer-1", "agent-verifier")

    assert decision.decision_type is HumanDecisionType.EXCLUDE_AGENT
    assert decision.payload == {"agent_id": "agent-verifier"}


def test_rerun_steps_joins_sub_task_ids() -> None:
    engine = _engine()

    decision = engine.rerun_steps("m1", "lawyer-1", ["st-1", "st-2"])

    assert decision.payload == {"sub_task_ids": "st-1,st-2"}


def test_every_decision_type_has_a_dedicated_method() -> None:
    engine = _engine()

    decisions = [
        engine.approve("m1", "u1"),
        engine.request_new_analysis("m1", "u1", "st-1"),
        engine.exclude_agent("m1", "u1", "agent-1"),
        engine.add_agent("m1", "u1", "agent-2"),
        engine.modify_plan("m1", "u1", "note"),
        engine.rerun_steps("m1", "u1", ["st-1"]),
    ]

    assert {d.decision_type for d in decisions} == set(HumanDecisionType)


def test_history_is_append_only_and_scoped_per_mission() -> None:
    engine = _engine()
    engine.approve("m1", "u1")
    engine.approve("m1", "u1")
    engine.approve("m2", "u1")

    history_m1 = engine.history_for_mission("m1")

    assert len(history_m1) == 2
    assert all(d.mission_id == "m1" for d in history_m1)


def test_history_is_empty_for_a_mission_with_no_decisions() -> None:
    engine = _engine()

    assert engine.history_for_mission("never-touched") == []
