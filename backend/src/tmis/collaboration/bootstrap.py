from functools import lru_cache

from tmis.collaboration.activity.feed import ActivityFeed
from tmis.collaboration.activity.store import InMemoryActivityStore
from tmis.collaboration.approvals.engine import ApprovalEngine
from tmis.collaboration.approvals.store import InMemoryApprovalStore
from tmis.collaboration.audit.store import InMemoryAuditStore
from tmis.collaboration.audit.trail import AuditTrail
from tmis.collaboration.comments.service import CommentService
from tmis.collaboration.comments.store import InMemoryCommentStore
from tmis.collaboration.evaluation.collector import WorkspaceMetricsCollector
from tmis.collaboration.evaluation.evaluator import CollaborationEvaluator
from tmis.collaboration.event_bus import CollaborationEventBus
from tmis.collaboration.members.service import MemberService
from tmis.collaboration.members.store import InMemoryMemberStore
from tmis.collaboration.mentions.engine import MentionEngine
from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.collaboration.permissions.engine import ConfigurablePermissionEngine
from tmis.collaboration.presence.locking import InMemoryOptimisticLockService
from tmis.collaboration.presence.service import InMemoryPresenceTracker
from tmis.collaboration.roles.store import InMemoryRoleAssignmentStore
from tmis.collaboration.sharing.engine import SharingEngine
from tmis.collaboration.sharing.store import InMemorySharingStore
from tmis.collaboration.tasks.service import TaskService
from tmis.collaboration.tasks.store import InMemoryTaskStore
from tmis.collaboration.timeline.service import TimelineService
from tmis.collaboration.workflow.engine import ConfigurableWorkflowEngine
from tmis.collaboration.workspace.engine import WorkspaceEngine
from tmis.collaboration.workspace.store import InMemoryWorkspaceStore


@lru_cache
def get_collaboration_event_bus() -> CollaborationEventBus:
    """Process-wide `CollaborationEventBus` singleton — the only channel
    an AI module needs to subscribe to in order to react to collaboration
    activity, without the LCE ever importing `tmis.ai` (see
    docs/33-legal-collaboration.md)."""
    return CollaborationEventBus()


@lru_cache
def get_activity_feed() -> ActivityFeed:
    return ActivityFeed(InMemoryActivityStore())


@lru_cache
def get_audit_trail() -> AuditTrail:
    return AuditTrail(InMemoryAuditStore())


@lru_cache
def get_notification_engine() -> NotificationEngine:
    return NotificationEngine()


@lru_cache
def get_collaboration_evaluator() -> CollaborationEvaluator:
    return CollaborationEvaluator()


@lru_cache
def get_member_store() -> InMemoryMemberStore:
    return InMemoryMemberStore()


@lru_cache
def get_task_store() -> InMemoryTaskStore:
    return InMemoryTaskStore()


@lru_cache
def get_comment_store() -> InMemoryCommentStore:
    return InMemoryCommentStore()


@lru_cache
def get_approval_store() -> InMemoryApprovalStore:
    return InMemoryApprovalStore()


@lru_cache
def get_workspace_engine() -> WorkspaceEngine:
    """Process-wide `WorkspaceEngine` singleton (see
    docs/33-legal-collaboration.md). Built entirely from LCE modules —
    no import from `tmis.ai`/`TMISKernel` anywhere in this call graph,
    which is exactly the sprint's independence constraint.
    """
    notification_engine = get_notification_engine()

    return WorkspaceEngine(
        workspace_store=InMemoryWorkspaceStore(),
        member_service=MemberService(get_member_store()),
        role_store=InMemoryRoleAssignmentStore(),
        permission_engine=ConfigurablePermissionEngine(),
        task_service=TaskService(get_task_store(), ConfigurableWorkflowEngine()),
        comment_service=CommentService(get_comment_store()),
        mention_engine=MentionEngine(notification_engine),
        approval_engine=ApprovalEngine(get_approval_store()),
        sharing_engine=SharingEngine(InMemorySharingStore()),
        activity_feed=get_activity_feed(),
        audit_trail=get_audit_trail(),
        event_bus=get_collaboration_event_bus(),
    )


@lru_cache
def get_timeline_service() -> TimelineService:
    return TimelineService(get_activity_feed())


@lru_cache
def get_presence_tracker() -> InMemoryPresenceTracker:
    return InMemoryPresenceTracker()


@lru_cache
def get_optimistic_lock_service() -> InMemoryOptimisticLockService:
    return InMemoryOptimisticLockService()


@lru_cache
def get_workspace_metrics_collector() -> WorkspaceMetricsCollector:
    return WorkspaceMetricsCollector(
        member_store=get_member_store(),
        task_store=get_task_store(),
        comment_store=get_comment_store(),
        approval_store=get_approval_store(),
        notification_engine=get_notification_engine(),
    )
