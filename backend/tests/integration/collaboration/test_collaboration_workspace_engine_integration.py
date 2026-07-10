import asyncio

import pytest

from tmis.collaboration.activity.feed import ActivityFeed
from tmis.collaboration.activity.store import InMemoryActivityStore
from tmis.collaboration.approvals.engine import ApprovalEngine
from tmis.collaboration.approvals.schemas import ApprovalDecisionType, ApprovalMode, ApprovalStatus
from tmis.collaboration.approvals.store import InMemoryApprovalStore
from tmis.collaboration.audit.store import InMemoryAuditStore
from tmis.collaboration.audit.trail import AuditTrail
from tmis.collaboration.comments.schemas import CommentTargetType
from tmis.collaboration.comments.service import CommentService
from tmis.collaboration.comments.store import InMemoryCommentStore
from tmis.collaboration.event_bus import CollaborationEventBus
from tmis.collaboration.events import CommentAdded, MemberInvited, TaskCreated, WorkspaceCreated
from tmis.collaboration.members.service import MemberService
from tmis.collaboration.members.store import InMemoryMemberStore
from tmis.collaboration.mentions.engine import MentionEngine
from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.collaboration.permissions.engine import ConfigurablePermissionEngine
from tmis.collaboration.permissions.schemas import Permission
from tmis.collaboration.roles.schemas import Role
from tmis.collaboration.roles.store import InMemoryRoleAssignmentStore
from tmis.collaboration.sharing.engine import SharingEngine
from tmis.collaboration.sharing.schemas import SharePermission
from tmis.collaboration.sharing.store import InMemorySharingStore
from tmis.collaboration.tasks.schemas import TaskPriority
from tmis.collaboration.tasks.service import TaskService
from tmis.collaboration.tasks.store import InMemoryTaskStore
from tmis.collaboration.workflow.engine import ConfigurableWorkflowEngine
from tmis.collaboration.workflow.schemas import WorkflowStatus
from tmis.collaboration.workspace.engine import WorkspaceEngine
from tmis.collaboration.workspace.store import InMemoryWorkspaceStore


@pytest.fixture
def engine() -> WorkspaceEngine:
    notification_engine = NotificationEngine()
    return WorkspaceEngine(
        workspace_store=InMemoryWorkspaceStore(),
        member_service=MemberService(InMemoryMemberStore()),
        role_store=InMemoryRoleAssignmentStore(),
        permission_engine=ConfigurablePermissionEngine(),
        task_service=TaskService(InMemoryTaskStore(), ConfigurableWorkflowEngine()),
        comment_service=CommentService(InMemoryCommentStore()),
        mention_engine=MentionEngine(notification_engine),
        approval_engine=ApprovalEngine(InMemoryApprovalStore()),
        sharing_engine=SharingEngine(InMemorySharingStore()),
        activity_feed=ActivityFeed(InMemoryActivityStore()),
        audit_trail=AuditTrail(InMemoryAuditStore()),
        event_bus=CollaborationEventBus(),
    )


def test_full_workspace_lifecycle_end_to_end(engine: WorkspaceEngine) -> None:
    async def scenario() -> None:
        workspace = await engine.create_workspace("firm-1", "Cabinet Durand", "founder-1")
        member = await engine.invite_member(
            workspace.id, "avocat@cabinet.fr", "Jane Avocat", "founder-1"
        )
        await engine.change_member_status(workspace.id, member.id, "active", "founder-1")
        await engine.assign_role(workspace.id, member.id, Role.ASSOCIATE, "founder-1")

        assert engine.has_permission(workspace.id, member.id, Permission.CASE_WRITE)
        assert not engine.has_permission(workspace.id, member.id, Permission.WORKSPACE_MANAGE)

        task = await engine.create_task(
            workspace.id,
            "Rédiger la mise en demeure",
            "founder-1",
            assignee_id=member.id,
            priority=TaskPriority.HIGH,
        )
        await engine.update_task_status(
            workspace.id, task.id, WorkflowStatus.IN_PROGRESS, member.id
        )

        comment = await engine.add_comment(
            workspace.id,
            CommentTargetType.TASK,
            task.id,
            member.id,
            f"Pour avis @user:{'founder-1'}",
        )

        approval = await engine.request_approval(
            workspace.id, "task", task.id, member.id, ["founder-1"], ApprovalMode.SINGLE
        )
        decided = await engine.decide_approval(
            workspace.id, approval.id, "founder-1", ApprovalDecisionType.APPROVE, "founder-1"
        )

        link = await engine.create_share_link(
            workspace.id, "task", task.id, SharePermission.READ, "founder-1"
        )

        return workspace, member, task, comment, approval, decided, link

    workspace, member, task, comment, approval, decided, link = asyncio.run(scenario())

    reloaded_workspace = engine.get_workspace(workspace.id)
    assert member.id in reloaded_workspace.member_ids
    assert task.id in reloaded_workspace.task_ids

    assert engine.get_task(task.id).status is WorkflowStatus.IN_PROGRESS
    assert decided.status is ApprovalStatus.APPROVED
    assert engine.get_approval(approval.id).status is ApprovalStatus.APPROVED

    comments_on_task = engine.list_comments_for_target(CommentTargetType.TASK, task.id)
    assert comment in comments_on_task

    resolved_link = engine._sharing.resolve_link(link.token)  # noqa: SLF001
    assert resolved_link is not None

    event_types = {type(e) for e in engine._event_bus.history}  # noqa: SLF001
    assert {WorkspaceCreated, MemberInvited, TaskCreated, CommentAdded} <= event_types

    activity = engine._activity.query(workspace.id)  # noqa: SLF001
    assert len(activity) >= 6

    audit_entries = engine._audit.list_for_workspace(workspace.id)  # noqa: SLF001
    assert len(audit_entries) >= 6


def test_permission_revoke_override_blocks_a_member_despite_their_role(
    engine: WorkspaceEngine,
) -> None:
    async def scenario() -> None:
        workspace = await engine.create_workspace("firm-1", "Cabinet Durand", "founder-1")
        member = await engine.invite_member(
            workspace.id, "avocat@cabinet.fr", "Jane Avocat", "founder-1"
        )
        await engine.assign_role(workspace.id, member.id, Role.ASSOCIATE, "founder-1")
        return workspace, member

    workspace, member = asyncio.run(scenario())

    assert engine.has_permission(workspace.id, member.id, Permission.CASE_WRITE)

    engine._permissions.revoke_override(workspace.id, member.id, Permission.CASE_WRITE)  # noqa: SLF001

    assert not engine.has_permission(workspace.id, member.id, Permission.CASE_WRITE)


def test_mention_in_a_comment_generates_a_notification(engine: WorkspaceEngine) -> None:
    async def scenario() -> None:
        workspace = await engine.create_workspace("firm-1", "Cabinet Durand", "founder-1")
        await engine.add_comment(
            workspace.id, CommentTargetType.CASE, "case-1", "member-1", "Voir @user:member-2"
        )
        return workspace

    asyncio.run(scenario())

    inbox = engine._mentions._notification_engine.list_for_recipient("member-2")  # noqa: SLF001
    assert len(inbox) == 1
