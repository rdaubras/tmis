from datetime import UTC, datetime, timedelta

import pytest

from tmis.workflow_automation.scheduler import InMemorySchedulerStore, SchedulerEngine
from tmis.workflow_automation.workflow_engine import (
    InMemoryWorkflowStore,
    WorkflowEngine,
    WorkflowStatus,
)


def test_workflow_engine_create_starts_at_version_one_draft() -> None:
    engine = WorkflowEngine(InMemoryWorkflowStore())

    workflow = engine.create("firm-1", "Ouverture", owner="avocat-1")

    assert workflow.version == 1
    assert workflow.status is WorkflowStatus.DRAFT


def test_workflow_engine_new_version_increments_and_inherits() -> None:
    engine = WorkflowEngine(InMemoryWorkflowStore())
    v1 = engine.create("firm-1", "Ouverture", owner="avocat-1", description="v1")

    v2 = engine.new_version("firm-1", v1.workflow_key, owner="avocat-1")

    assert v2.version == 2
    assert v2.description == "v1"
    assert v2.workflow_key == v1.workflow_key


def test_workflow_engine_activate_archives_previous_active_version() -> None:
    engine = WorkflowEngine(InMemoryWorkflowStore())
    v1 = engine.create("firm-1", "Ouverture", owner="avocat-1")
    engine.activate("firm-1", v1.id)
    v2 = engine.new_version("firm-1", v1.workflow_key, owner="avocat-1")

    engine.activate("firm-1", v2.id)

    assert engine.get("firm-1", v1.id).status is WorkflowStatus.ARCHIVED
    assert engine.get("firm-1", v2.id).status is WorkflowStatus.ACTIVE
    assert engine.get_active("firm-1", v1.workflow_key).id == v2.id


def test_workflow_engine_new_version_unknown_key_raises() -> None:
    engine = WorkflowEngine(InMemoryWorkflowStore())

    with pytest.raises(KeyError):
        engine.new_version("firm-1", "unknown-key", owner="avocat-1")


def test_scheduler_due_returns_only_past_due_triggers() -> None:
    engine = SchedulerEngine(InMemorySchedulerStore())
    now = datetime.now(UTC)
    past = engine.schedule("firm-1", "wf-1", "trigger-1", now - timedelta(minutes=5))
    engine.schedule("firm-1", "wf-1", "trigger-2", now + timedelta(hours=1))

    due = engine.due("firm-1", now)

    assert due == [past]


def test_scheduler_mark_fired_advances_recurring_trigger() -> None:
    engine = SchedulerEngine(InMemorySchedulerStore())
    now = datetime.now(UTC)
    scheduled = engine.schedule(
        "firm-1", "wf-1", "trigger-1", now - timedelta(minutes=5), interval=timedelta(days=1)
    )

    engine.mark_fired(scheduled, now)

    assert scheduled.next_fire_at > now


def test_scheduler_mark_fired_one_shot_does_not_advance() -> None:
    engine = SchedulerEngine(InMemorySchedulerStore())
    now = datetime.now(UTC)
    scheduled = engine.schedule("firm-1", "wf-1", "trigger-1", now - timedelta(minutes=5))

    engine.mark_fired(scheduled, now)

    assert scheduled.next_fire_at < now
