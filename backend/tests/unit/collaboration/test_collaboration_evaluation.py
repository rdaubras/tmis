from datetime import UTC, datetime

from tmis.collaboration.approvals.engine import ApprovalEngine
from tmis.collaboration.approvals.schemas import ApprovalDecisionType, ApprovalMode
from tmis.collaboration.approvals.store import InMemoryApprovalStore
from tmis.collaboration.comments.schemas import CommentTargetType
from tmis.collaboration.comments.service import CommentService
from tmis.collaboration.comments.store import InMemoryCommentStore
from tmis.collaboration.evaluation.collector import WorkspaceMetricsCollector
from tmis.collaboration.evaluation.evaluator import CollaborationEvaluator
from tmis.collaboration.evaluation.metrics import OperationTiming
from tmis.collaboration.evaluation.timer import OperationTimer
from tmis.collaboration.members.service import MemberService
from tmis.collaboration.members.store import InMemoryMemberStore
from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.collaboration.tasks.service import TaskService
from tmis.collaboration.tasks.store import InMemoryTaskStore
from tmis.collaboration.workflow.engine import ConfigurableWorkflowEngine
from tmis.collaboration.workflow.schemas import WorkflowStatus


def test_evaluator_records_and_averages_operation_timings() -> None:
    evaluator = CollaborationEvaluator()
    evaluator.record_operation_timing(OperationTiming("task.create", 10.0, datetime.now(UTC)))
    evaluator.record_operation_timing(OperationTiming("task.create", 20.0, datetime.now(UTC)))

    assert evaluator.average_duration_ms("task.create") == 15.0
    assert evaluator.average_duration_ms("unknown.operation") == 0.0


def test_operation_timer_context_manager_records_a_timing() -> None:
    evaluator = CollaborationEvaluator()

    with OperationTimer(evaluator, "task.create"):
        pass

    assert len(evaluator.timings) == 1
    assert evaluator.timings[0].operation == "task.create"
    assert evaluator.timings[0].duration_ms >= 0.0


def test_workspace_metrics_collector_snapshot() -> None:
    member_store = InMemoryMemberStore()
    task_store = InMemoryTaskStore()
    comment_store = InMemoryCommentStore()
    approval_store = InMemoryApprovalStore()
    notification_engine = NotificationEngine()

    member_service = MemberService(member_store)
    task_service = TaskService(task_store, ConfigurableWorkflowEngine())
    comment_service = CommentService(comment_store)
    approval_engine = ApprovalEngine(approval_store)

    active = member_service.invite("ws-1", "a@cabinet.fr", "A")
    member_service.activate(active.id)
    member_service.invite("ws-1", "b@cabinet.fr", "B")

    task_service.create("ws-1", "Task 1")
    task2 = task_service.create("ws-1", "Task 2")
    for target in (
        WorkflowStatus.IN_PROGRESS,
        WorkflowStatus.IN_REVIEW,
        WorkflowStatus.TO_VALIDATE,
        WorkflowStatus.VALIDATED,
    ):
        task_service.update_status(task2.id, target)

    comment_service.add("ws-1", CommentTargetType.TASK, task2.id, "a", "Bien joué")

    approval = approval_engine.request(
        "ws-1", "task", task2.id, "a", ["b"], ApprovalMode.SINGLE
    )
    approval_engine.decide(approval.id, "b", ApprovalDecisionType.APPROVE)

    notification_engine.dispatch("ws-1", "a", "mention", {}, [])

    collector = WorkspaceMetricsCollector(
        member_store, task_store, comment_store, approval_store, notification_engine
    )
    snapshot = collector.snapshot("ws-1")

    assert snapshot.member_count == 2
    assert snapshot.active_member_count == 1
    assert snapshot.task_count == 2
    assert snapshot.validated_task_count == 1
    assert snapshot.comment_count == 1
    assert snapshot.approval_count == 1
    assert snapshot.pending_approval_count == 0
