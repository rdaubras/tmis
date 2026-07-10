import uuid
from datetime import datetime

from tmis.collaboration.activity.ports import ActivityFeedPort
from tmis.collaboration.activity.schemas import ActivityType
from tmis.collaboration.approvals.ports import ApprovalEnginePort
from tmis.collaboration.approvals.schemas import (
    ApprovalDecisionType,
    ApprovalMode,
    ApprovalRequest,
)
from tmis.collaboration.audit.ports import AuditTrailPort
from tmis.collaboration.comments.ports import CommentServicePort
from tmis.collaboration.comments.schemas import Comment, CommentTargetType
from tmis.collaboration.event_bus import CollaborationEventBus
from tmis.collaboration.events import (
    ApprovalDecided,
    ApprovalRequested,
    CommentAdded,
    MemberInvited,
    MemberStatusChanged,
    RoleAssigned,
    ShareLinkCreated,
    ShareLinkRevoked,
    TaskCreated,
    TaskStatusChanged,
    WorkspaceCreated,
)
from tmis.collaboration.members.ports import MemberServicePort
from tmis.collaboration.members.schemas import Member
from tmis.collaboration.mentions.ports import MentionEnginePort
from tmis.collaboration.permissions.ports import PermissionEnginePort
from tmis.collaboration.permissions.schemas import Permission
from tmis.collaboration.roles.ports import RoleAssignmentStorePort
from tmis.collaboration.roles.schemas import Role
from tmis.collaboration.sharing.ports import SharingEnginePort
from tmis.collaboration.sharing.schemas import InternalShare, ShareLink, SharePermission
from tmis.collaboration.tasks.ports import TaskServicePort
from tmis.collaboration.tasks.schemas import Task, TaskPriority
from tmis.collaboration.workflow.schemas import WorkflowStatus
from tmis.collaboration.workspace.ports import WorkspaceStorePort
from tmis.collaboration.workspace.schemas import Workspace, WorkspaceSettings


class WorkspaceEngine:
    """Composition root for the Legal Collaboration Engine (see
    docs/33-legal-collaboration.md — Architecture). Ties every LCE
    module together: it never re-implements a rule already owned by a
    module (roles, permissions, workflow transitions, ...) — it just
    sequences calls, then records the result as activity/audit and
    publishes a `CollaborationEvent` so AI modules can react without the
    LCE ever importing `tmis.ai`.
    """

    def __init__(
        self,
        workspace_store: WorkspaceStorePort,
        member_service: MemberServicePort,
        role_store: RoleAssignmentStorePort,
        permission_engine: PermissionEnginePort,
        task_service: TaskServicePort,
        comment_service: CommentServicePort,
        mention_engine: MentionEnginePort,
        approval_engine: ApprovalEnginePort,
        sharing_engine: SharingEnginePort,
        activity_feed: ActivityFeedPort,
        audit_trail: AuditTrailPort,
        event_bus: CollaborationEventBus,
    ) -> None:
        self._workspaces = workspace_store
        self._members = member_service
        self._roles = role_store
        self._permissions = permission_engine
        self._tasks = task_service
        self._comments = comment_service
        self._mentions = mention_engine
        self._approvals = approval_engine
        self._sharing = sharing_engine
        self._activity = activity_feed
        self._audit = audit_trail
        self._event_bus = event_bus

    async def create_workspace(
        self,
        firm_id: str,
        name: str,
        actor_id: str,
        settings: WorkspaceSettings | None = None,
    ) -> Workspace:
        workspace = Workspace(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            name=name,
            settings=settings or WorkspaceSettings(),
        )
        self._workspaces.save(workspace)
        self._activity.record(
            workspace.id, actor_id, ActivityType.WORKSPACE, "workspace", workspace.id,
            f"Workspace {name!r} created",
        )
        self._audit.record(
            workspace.id, actor_id, "workspace.create", "workspace", workspace.id,
            new_state={"name": name, "firm_id": firm_id},
        )
        await self._event_bus.publish(WorkspaceCreated(workspace_id=workspace.id))
        return workspace

    def get_workspace(self, workspace_id: str) -> Workspace:
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            raise ValueError(f"Unknown workspace {workspace_id!r}")
        return workspace

    async def invite_member(
        self, workspace_id: str, email: str, display_name: str, actor_id: str
    ) -> Member:
        member = self._members.invite(workspace_id, email, display_name)
        workspace = self.get_workspace(workspace_id)
        workspace.member_ids.add(member.id)
        self._workspaces.save(workspace)
        self._activity.record(
            workspace_id, actor_id, ActivityType.MEMBER, "member", member.id,
            f"{display_name} invited",
        )
        self._audit.record(
            workspace_id, actor_id, "member.invite", "member", member.id,
            new_state={"email": email, "status": member.status.value},
        )
        await self._event_bus.publish(MemberInvited(workspace_id=workspace_id, member_id=member.id))
        return member

    async def change_member_status(
        self, workspace_id: str, member_id: str, target: str, actor_id: str
    ) -> Member:
        transition = {
            "active": self._members.activate,
            "suspended": self._members.suspend,
            "deactivated": self._members.deactivate,
        }[target]
        member = transition(member_id, actor_id)
        from_status = member.history[-1].from_status
        self._activity.record(
            workspace_id, actor_id, ActivityType.MEMBER, "member", member_id,
            f"Member status changed to {member.status.value}",
        )
        self._audit.record(
            workspace_id, actor_id, "member.status_change", "member", member_id,
            old_state={"status": from_status.value if from_status else ""},
            new_state={"status": member.status.value},
        )
        await self._event_bus.publish(
            MemberStatusChanged(
                workspace_id=workspace_id,
                member_id=member_id,
                from_status=from_status.value if from_status else "",
                to_status=member.status.value,
            )
        )
        return member

    async def assign_role(
        self, workspace_id: str, member_id: str, role: Role, actor_id: str
    ) -> None:
        self._roles.assign(workspace_id, member_id, role)
        self._activity.record(
            workspace_id, actor_id, ActivityType.MEMBER, "member", member_id,
            f"Role {role.value} assigned",
        )
        self._audit.record(
            workspace_id, actor_id, "role.assign", "member", member_id,
            new_state={"role": role.value},
        )
        await self._event_bus.publish(
            RoleAssigned(workspace_id=workspace_id, member_id=member_id, role=role.value)
        )

    def has_permission(self, workspace_id: str, member_id: str, permission: Permission) -> bool:
        role = self._roles.get_role(workspace_id, member_id)
        if role is None:
            return False
        return self._permissions.has_permission(workspace_id, member_id, role, permission)

    def get_task(self, task_id: str) -> Task:
        task = self._tasks.get(task_id)
        if task is None:
            raise ValueError(f"Unknown task {task_id!r}")
        return task

    def list_comments_for_target(
        self, target_type: CommentTargetType, target_id: str
    ) -> list[Comment]:
        return self._comments.list_for_target(target_type, target_id)

    def get_approval(self, approval_id: str) -> ApprovalRequest:
        return self._approvals.get(approval_id)

    async def create_task(
        self,
        workspace_id: str,
        title: str,
        actor_id: str,
        description: str = "",
        *,
        case_id: str | None = None,
        assignee_id: str | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: datetime | None = None,
        depends_on: set[str] | None = None,
    ) -> Task:
        task = self._tasks.create(
            workspace_id, title, description,
            case_id=case_id, assignee_id=assignee_id, priority=priority,
            due_date=due_date, depends_on=depends_on,
        )
        workspace = self.get_workspace(workspace_id)
        workspace.task_ids.add(task.id)
        self._workspaces.save(workspace)
        self._activity.record(
            workspace_id, actor_id, ActivityType.TASK, "task", task.id, f"Task {title!r} created"
        )
        self._audit.record(
            workspace_id, actor_id, "task.create", "task", task.id,
            new_state={"title": title, "status": task.status.value},
        )
        await self._event_bus.publish(
            TaskCreated(workspace_id=workspace_id, task_id=task.id, case_id=case_id)
        )
        return task

    async def update_task_status(
        self, workspace_id: str, task_id: str, target: WorkflowStatus, actor_id: str
    ) -> Task:
        before = self._tasks.get(task_id)
        from_status = before.status if before else None
        task = self._tasks.update_status(task_id, target)
        self._activity.record(
            workspace_id, actor_id, ActivityType.TASK, "task", task_id,
            f"Task status changed to {target.value}",
        )
        self._audit.record(
            workspace_id, actor_id, "task.status_change", "task", task_id,
            old_state={"status": from_status.value if from_status else ""},
            new_state={"status": target.value},
        )
        await self._event_bus.publish(
            TaskStatusChanged(
                workspace_id=workspace_id,
                task_id=task_id,
                from_status=from_status.value if from_status else "",
                to_status=target.value,
            )
        )
        return task

    async def add_comment(
        self,
        workspace_id: str,
        target_type: CommentTargetType,
        target_id: str,
        author_id: str,
        text: str,
        *,
        attachment_ids: tuple[str, ...] = (),
    ) -> Comment:
        comment = self._comments.add(
            workspace_id, target_type, target_id, author_id, text,
            attachment_ids=attachment_ids,
        )
        self._mentions.process(comment)
        self._activity.record(
            workspace_id, author_id, ActivityType.COMMENT, target_type.value, target_id,
            "Comment added",
        )
        self._audit.record(
            workspace_id, author_id, "comment.add", target_type.value, target_id,
            new_state={"comment_id": comment.id},
        )
        await self._event_bus.publish(
            CommentAdded(
                workspace_id=workspace_id,
                comment_id=comment.id,
                target_type=target_type.value,
                target_id=target_id,
            )
        )
        return comment

    async def request_approval(
        self,
        workspace_id: str,
        target_type: str,
        target_id: str,
        requested_by: str,
        approver_ids: list[str],
        mode: ApprovalMode,
    ) -> ApprovalRequest:
        approval = self._approvals.request(
            workspace_id, target_type, target_id, requested_by, approver_ids, mode
        )
        self._activity.record(
            workspace_id, requested_by, ActivityType.APPROVAL, target_type, target_id,
            "Approval requested",
        )
        self._audit.record(
            workspace_id, requested_by, "approval.request", target_type, target_id,
            new_state={"approval_id": approval.id, "status": approval.status.value},
        )
        await self._event_bus.publish(
            ApprovalRequested(
                workspace_id=workspace_id,
                approval_id=approval.id,
                target_type=target_type,
                target_id=target_id,
            )
        )
        return approval

    async def decide_approval(
        self,
        workspace_id: str,
        approval_id: str,
        approver_id: str,
        decision: ApprovalDecisionType,
        actor_id: str,
        comment: str | None = None,
    ) -> ApprovalRequest:
        approval = self._approvals.decide(approval_id, approver_id, decision, comment)
        self._activity.record(
            workspace_id, actor_id, ActivityType.APPROVAL, approval.target_type,
            approval.target_id, f"Approval decision: {decision.value}",
        )
        self._audit.record(
            workspace_id, actor_id, "approval.decide", approval.target_type, approval.target_id,
            new_state={"status": approval.status.value},
        )
        await self._event_bus.publish(
            ApprovalDecided(
                workspace_id=workspace_id, approval_id=approval.id, status=approval.status.value
            )
        )
        return approval

    async def create_share_link(
        self,
        workspace_id: str,
        target_type: str,
        target_id: str,
        permission: SharePermission,
        actor_id: str,
        expires_in_seconds: int | None = None,
    ) -> ShareLink:
        link = self._sharing.create_link(
            workspace_id, target_type, target_id, permission, actor_id, expires_in_seconds
        )
        self._activity.record(
            workspace_id, actor_id, ActivityType.SHARING, target_type, target_id,
            "Share link created",
        )
        self._audit.record(
            workspace_id, actor_id, "sharing.create_link", target_type, target_id,
            new_state={"share_id": link.id},
        )
        await self._event_bus.publish(
            ShareLinkCreated(
                workspace_id=workspace_id, share_id=link.id,
                target_type=target_type, target_id=target_id,
            )
        )
        return link

    async def revoke_share_link(self, workspace_id: str, token: str, actor_id: str) -> ShareLink:
        link = self._sharing.revoke_link(token)
        self._activity.record(
            workspace_id, actor_id, ActivityType.SHARING, link.target_type, link.target_id,
            "Share link revoked",
        )
        self._audit.record(
            workspace_id, actor_id, "sharing.revoke_link", link.target_type, link.target_id,
            old_state={"revoked": "false"}, new_state={"revoked": "true"},
        )
        await self._event_bus.publish(ShareLinkRevoked(workspace_id=workspace_id, share_id=link.id))
        return link

    def share_internally(
        self,
        workspace_id: str,
        target_type: str,
        target_id: str,
        shared_with_member_id: str,
        permission: SharePermission,
        actor_id: str,
    ) -> InternalShare:
        return self._sharing.share_internally(
            workspace_id, target_type, target_id, shared_with_member_id, permission, actor_id
        )
