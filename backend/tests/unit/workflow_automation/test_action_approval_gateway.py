import pytest

from tmis.ai_governance.bootstrap import get_human_validation_engine
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.workflow_automation.action_engine import (
    ACTION_CREATE_TASK,
    ACTION_NOTIFY,
    Action,
    ActionEngine,
    ActionResult,
    InMemoryActionLogStore,
    UnknownActionTypeError,
    new_action_id,
)
from tmis.workflow_automation.approval_gateway import (
    ApprovalGatewayEngine,
    InMemoryApprovalPolicyStore,
)


class _EchoHandler:
    action_type = ACTION_CREATE_TASK

    def execute(self, action: Action, context: dict[str, str]) -> ActionResult:
        return ActionResult(success=True, detail="task created", output={"task_id": "t-1"})


class _AlwaysFailsHandler:
    action_type = ACTION_NOTIFY

    def execute(self, action: Action, context: dict[str, str]) -> ActionResult:
        raise RuntimeError("boom")


def test_action_engine_executes_registered_handler_and_journals() -> None:
    engine = ActionEngine(InMemoryActionLogStore(), [_EchoHandler()])
    action = Action(id=new_action_id(), workflow_id="wf-1", action_type=ACTION_CREATE_TASK)

    result = engine.execute("firm-1", "exec-1", action, {})

    assert result.success
    assert len(engine.history_for_execution("firm-1", "exec-1")) == 1


def test_action_engine_unregistered_action_type_raises() -> None:
    engine = ActionEngine(InMemoryActionLogStore())
    action = Action(id=new_action_id(), workflow_id="wf-1", action_type="unknown")

    with pytest.raises(UnknownActionTypeError):
        engine.execute("firm-1", "exec-1", action, {})


def test_action_engine_handler_exception_is_journaled_not_raised() -> None:
    engine = ActionEngine(InMemoryActionLogStore(), [_AlwaysFailsHandler()])
    action = Action(id=new_action_id(), workflow_id="wf-1", action_type=ACTION_NOTIFY)

    result = engine.execute("firm-1", "exec-1", action, {})

    assert result.success is False
    entries = engine.history_for_execution("firm-1", "exec-1")
    assert len(entries) == 1
    assert entries[0].result.success is False


def test_approval_gateway_configurable_per_action_type() -> None:
    gateway = ApprovalGatewayEngine(get_human_validation_engine(), InMemoryApprovalPolicyStore())
    gateway.configure("firm-approval-test", ACTION_NOTIFY, True)

    assert gateway.requires_approval("firm-approval-test", ACTION_NOTIFY) is True
    assert gateway.requires_approval("firm-approval-test", ACTION_CREATE_TASK) is False


def test_approval_gateway_reuses_human_validation_engine() -> None:
    gateway = ApprovalGatewayEngine(get_human_validation_engine(), InMemoryApprovalPolicyStore())

    request = gateway.request_approval("firm-approval-2", "action-1", "avocat-1", ("associe-1",))
    assert gateway.is_approved("firm-approval-2", "action-1") is False

    gateway.decide("firm-approval-2", request.id, "associe-1", ValidationDecisionType.APPROVE)

    assert gateway.is_approved("firm-approval-2", "action-1") is True
