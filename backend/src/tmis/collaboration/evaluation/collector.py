from datetime import UTC, datetime

from tmis.collaboration.approvals.ports import ApprovalStorePort
from tmis.collaboration.approvals.schemas import ApprovalStatus
from tmis.collaboration.comments.ports import CommentStorePort
from tmis.collaboration.evaluation.metrics import WorkspaceActivityMetrics
from tmis.collaboration.members.ports import MemberStorePort
from tmis.collaboration.members.schemas import MemberStatus
from tmis.collaboration.notifications.ports import NotificationEnginePort
from tmis.collaboration.tasks.ports import TaskStorePort
from tmis.collaboration.workflow.schemas import WorkflowStatus


class WorkspaceMetricsCollector:
    """Composes the read-only counting ports of every LCE module to
    produce a `WorkspaceActivityMetrics` snapshot — the "nombre de
    tâches, validations, commentaires, notifications" observability
    requirement from the sprint brief. Depends only on ports, never on
    concrete stores."""

    def __init__(
        self,
        member_store: MemberStorePort,
        task_store: TaskStorePort,
        comment_store: CommentStorePort,
        approval_store: ApprovalStorePort,
        notification_engine: NotificationEnginePort,
    ) -> None:
        self._member_store = member_store
        self._task_store = task_store
        self._comment_store = comment_store
        self._approval_store = approval_store
        self._notification_engine = notification_engine

    def snapshot(self, workspace_id: str) -> WorkspaceActivityMetrics:
        members = self._member_store.list_for_workspace(workspace_id)
        tasks = self._task_store.list_for_workspace(workspace_id)
        comments = self._comment_store.list_for_workspace(workspace_id)
        approvals = self._approval_store.list_for_workspace(workspace_id)
        notifications = self._notification_engine.list_for_workspace(workspace_id)
        return WorkspaceActivityMetrics(
            workspace_id=workspace_id,
            member_count=len(members),
            active_member_count=sum(1 for m in members if m.status is MemberStatus.ACTIVE),
            task_count=len(tasks),
            validated_task_count=sum(
                1 for t in tasks if t.status is WorkflowStatus.VALIDATED
            ),
            comment_count=len(comments),
            approval_count=len(approvals),
            pending_approval_count=sum(
                1 for a in approvals if a.status is ApprovalStatus.PENDING
            ),
            notification_count=len(notifications),
            computed_at=datetime.now(UTC),
        )
