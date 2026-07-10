import pytest

from tmis.collaboration.tasks.service import TaskService
from tmis.collaboration.workflow.engine import ConfigurableWorkflowEngine
from tmis.collaboration.workflow.schemas import WorkflowStatus


def test_default_workflow_allows_the_linear_progression() -> None:
    engine = ConfigurableWorkflowEngine()

    assert engine.can_transition(WorkflowStatus.TODO, WorkflowStatus.IN_PROGRESS)
    assert engine.can_transition(WorkflowStatus.IN_PROGRESS, WorkflowStatus.IN_REVIEW)
    assert engine.can_transition(WorkflowStatus.IN_REVIEW, WorkflowStatus.TO_VALIDATE)
    assert engine.can_transition(WorkflowStatus.TO_VALIDATE, WorkflowStatus.VALIDATED)


def test_default_workflow_allows_stepping_back() -> None:
    engine = ConfigurableWorkflowEngine()

    assert engine.can_transition(WorkflowStatus.IN_REVIEW, WorkflowStatus.IN_PROGRESS)
    assert engine.can_transition(WorkflowStatus.TO_VALIDATE, WorkflowStatus.IN_REVIEW)


def test_default_workflow_allows_archiving_from_anywhere_except_archived() -> None:
    engine = ConfigurableWorkflowEngine()

    for status in WorkflowStatus:
        if status is WorkflowStatus.ARCHIVED:
            continue
        assert engine.can_transition(status, WorkflowStatus.ARCHIVED)

    assert not engine.can_transition(WorkflowStatus.ARCHIVED, WorkflowStatus.TODO)


def test_transition_raises_for_a_disallowed_move() -> None:
    engine = ConfigurableWorkflowEngine()

    with pytest.raises(ValueError, match="Cannot transition"):
        engine.transition(WorkflowStatus.TODO, WorkflowStatus.VALIDATED)


def test_workflow_engine_is_reconfigurable() -> None:
    custom = {
        WorkflowStatus.TODO: {WorkflowStatus.VALIDATED},
        WorkflowStatus.VALIDATED: set(),
    }
    engine = ConfigurableWorkflowEngine(custom)

    assert engine.can_transition(WorkflowStatus.TODO, WorkflowStatus.VALIDATED)
    assert not engine.can_transition(WorkflowStatus.TODO, WorkflowStatus.IN_PROGRESS)


def test_task_service_create_defaults_to_todo() -> None:
    service = TaskService()
    task = service.create("ws-1", "Draft the mise en demeure")

    assert task.status is WorkflowStatus.TODO
    assert task.workspace_id == "ws-1"


def test_task_service_update_status_delegates_to_workflow_engine() -> None:
    service = TaskService()
    task = service.create("ws-1", "Draft the mise en demeure")

    updated = service.update_status(task.id, WorkflowStatus.IN_PROGRESS)

    assert updated.status is WorkflowStatus.IN_PROGRESS


def test_task_service_update_status_rejects_illegal_transition() -> None:
    service = TaskService()
    task = service.create("ws-1", "Draft the mise en demeure")

    with pytest.raises(ValueError):
        service.update_status(task.id, WorkflowStatus.VALIDATED)


def test_can_start_is_true_with_no_dependencies() -> None:
    service = TaskService()
    task = service.create("ws-1", "Standalone task")

    assert service.can_start(task.id) is True


def test_can_start_is_false_until_dependency_is_done() -> None:
    service = TaskService()
    dependency = service.create("ws-1", "Research task")
    dependent = service.create("ws-1", "Drafting task", depends_on={dependency.id})

    assert service.can_start(dependent.id) is False

    service.update_status(dependency.id, WorkflowStatus.IN_PROGRESS)
    service.update_status(dependency.id, WorkflowStatus.IN_REVIEW)
    service.update_status(dependency.id, WorkflowStatus.TO_VALIDATE)
    service.update_status(dependency.id, WorkflowStatus.VALIDATED)

    assert service.can_start(dependent.id) is True


def test_can_start_does_not_block_update_status_it_is_advisory_only() -> None:
    service = TaskService()
    dependency = service.create("ws-1", "Research task")
    dependent = service.create("ws-1", "Drafting task", depends_on={dependency.id})

    assert service.can_start(dependent.id) is False
    updated = service.update_status(dependent.id, WorkflowStatus.IN_PROGRESS)
    assert updated.status is WorkflowStatus.IN_PROGRESS


def test_assign_and_link_document_and_comment() -> None:
    service = TaskService()
    task = service.create("ws-1", "Task")

    service.assign(task.id, "member-1")
    service.add_document(task.id, "doc-1")
    service.link_comment(task.id, "comment-1")

    fetched = service.get(task.id)
    assert fetched is not None
    assert fetched.assignee_id == "member-1"
    assert "doc-1" in fetched.document_ids
    assert "comment-1" in fetched.comment_ids


def test_unknown_task_raises() -> None:
    service = TaskService()

    with pytest.raises(ValueError, match="Unknown task"):
        service.assign("nope", "member-1")
