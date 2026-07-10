from fastapi import APIRouter, Depends, HTTPException

from tmis.collaboration.activity.ports import ActivityFeedPort
from tmis.collaboration.activity.schemas import ActivityEntry, ActivityType
from tmis.collaboration.api.schemas import (
    ActivityEntryResponse,
    AddCommentRequest,
    ApprovalResponse,
    AssignRoleRequest,
    ChangeMemberStatusRequest,
    CommentResponse,
    CreateTaskRequest,
    CreateWorkspaceRequest,
    DecideApprovalRequest,
    InviteMemberRequest,
    MemberResponse,
    NotificationResponse,
    RequestApprovalRequest,
    TaskResponse,
    UpdateTaskStatusRequest,
    WorkspaceResponse,
)
from tmis.collaboration.approvals.schemas import ApprovalDecisionType, ApprovalMode, ApprovalRequest
from tmis.collaboration.bootstrap import (
    get_activity_feed,
    get_notification_engine,
    get_workspace_engine,
)
from tmis.collaboration.comments.schemas import Comment, CommentTargetType
from tmis.collaboration.members.schemas import Member
from tmis.collaboration.notifications.ports import NotificationEnginePort
from tmis.collaboration.roles.schemas import Role
from tmis.collaboration.tasks.schemas import Task, TaskPriority
from tmis.collaboration.workflow.schemas import WorkflowStatus
from tmis.collaboration.workspace.engine import WorkspaceEngine
from tmis.collaboration.workspace.schemas import Workspace

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


def _parse_enum(enum_cls: type, raw: str, label: str) -> object:
    try:
        return enum_cls(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown {label}: {raw!r}") from exc


def _to_workspace_response(workspace: Workspace) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=workspace.id,
        firm_id=workspace.firm_id,
        name=workspace.name,
        member_ids=list(workspace.member_ids),
        task_ids=list(workspace.task_ids),
        created_at=workspace.created_at,
    )


def _to_member_response(member: Member) -> MemberResponse:
    return MemberResponse(
        id=member.id,
        workspace_id=member.workspace_id,
        email=member.email,
        display_name=member.display_name,
        status=member.status.value,
        invited_at=member.invited_at,
        activated_at=member.activated_at,
    )


def _to_task_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        workspace_id=task.workspace_id,
        title=task.title,
        description=task.description,
        case_id=task.case_id,
        assignee_id=task.assignee_id,
        priority=task.priority.value,
        due_date=task.due_date,
        status=task.status.value,
        document_ids=list(task.document_ids),
        comment_ids=list(task.comment_ids),
        depends_on=list(task.depends_on),
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _to_comment_response(comment: Comment) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        workspace_id=comment.workspace_id,
        target_type=comment.target_type.value,
        target_id=comment.target_id,
        author_id=comment.author_id,
        text=comment.text,
        parent_id=comment.parent_id,
        attachment_ids=list(comment.attachment_ids),
        created_at=comment.created_at,
    )


def _to_approval_response(approval: ApprovalRequest) -> ApprovalResponse:
    return ApprovalResponse(
        id=approval.id,
        workspace_id=approval.workspace_id,
        target_type=approval.target_type,
        target_id=approval.target_id,
        requested_by=approval.requested_by,
        approver_ids=list(approval.approver_ids),
        mode=approval.mode.value,
        status=approval.status.value,
    )


def _to_activity_response(entry: ActivityEntry) -> ActivityEntryResponse:
    return ActivityEntryResponse(
        id=entry.id,
        workspace_id=entry.workspace_id,
        actor_id=entry.actor_id,
        activity_type=entry.activity_type.value,
        target_type=entry.target_type,
        target_id=entry.target_id,
        summary=entry.summary,
        occurred_at=entry.occurred_at,
    )


@router.post("/workspaces", response_model=WorkspaceResponse)
async def create_workspace(
    payload: CreateWorkspaceRequest,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> WorkspaceResponse:
    workspace = await engine.create_workspace(payload.firm_id, payload.name, payload.actor_id)
    return _to_workspace_response(workspace)


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: str,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> WorkspaceResponse:
    try:
        workspace = engine.get_workspace(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_workspace_response(workspace)


@router.post("/workspaces/{workspace_id}/members", response_model=MemberResponse)
async def invite_member(
    workspace_id: str,
    payload: InviteMemberRequest,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> MemberResponse:
    member = await engine.invite_member(
        workspace_id, payload.email, payload.display_name, payload.actor_id
    )
    return _to_member_response(member)


@router.post("/members/{member_id}/status", response_model=MemberResponse)
async def change_member_status(
    member_id: str,
    payload: ChangeMemberStatusRequest,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> MemberResponse:
    try:
        member = await engine.change_member_status(
            payload.workspace_id, member_id, payload.target, payload.actor_id
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_member_response(member)


@router.post("/workspaces/{workspace_id}/members/{member_id}/role", status_code=204)
async def assign_role(
    workspace_id: str,
    member_id: str,
    payload: AssignRoleRequest,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> None:
    role = _parse_enum(Role, payload.role, "role")
    await engine.assign_role(workspace_id, member_id, role, payload.actor_id)  # type: ignore[arg-type]


@router.post("/workspaces/{workspace_id}/tasks", response_model=TaskResponse)
async def create_task(
    workspace_id: str,
    payload: CreateTaskRequest,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> TaskResponse:
    priority = _parse_enum(TaskPriority, payload.priority, "priority")
    task = await engine.create_task(
        workspace_id,
        payload.title,
        payload.actor_id,
        payload.description,
        case_id=payload.case_id,
        assignee_id=payload.assignee_id,
        priority=priority,  # type: ignore[arg-type]
        due_date=payload.due_date,
        depends_on=set(payload.depends_on),
    )
    return _to_task_response(task)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> TaskResponse:
    try:
        task = engine.get_task(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_task_response(task)


@router.post("/tasks/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    payload: UpdateTaskStatusRequest,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> TaskResponse:
    target = _parse_enum(WorkflowStatus, payload.target, "workflow status")
    try:
        task = await engine.update_task_status(
            payload.workspace_id, task_id, target, payload.actor_id  # type: ignore[arg-type]
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_task_response(task)


@router.post("/comments", response_model=CommentResponse)
async def add_comment(
    payload: AddCommentRequest,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> CommentResponse:
    target_type = _parse_enum(CommentTargetType, payload.target_type, "comment target type")
    comment = await engine.add_comment(
        payload.workspace_id,
        target_type,  # type: ignore[arg-type]
        payload.target_id,
        payload.author_id,
        payload.text,
        attachment_ids=tuple(payload.attachment_ids),
    )
    return _to_comment_response(comment)


@router.get("/comments", response_model=list[CommentResponse])
def list_comments(
    target_type: str,
    target_id: str,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> list[CommentResponse]:
    parsed_type = _parse_enum(CommentTargetType, target_type, "comment target type")
    comments = engine.list_comments_for_target(parsed_type, target_id)  # type: ignore[arg-type]
    return [_to_comment_response(c) for c in comments]


@router.post("/approvals", response_model=ApprovalResponse)
async def request_approval(
    payload: RequestApprovalRequest,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> ApprovalResponse:
    mode = _parse_enum(ApprovalMode, payload.mode, "approval mode")
    approval = await engine.request_approval(
        payload.workspace_id,
        payload.target_type,
        payload.target_id,
        payload.requested_by,
        payload.approver_ids,
        mode,  # type: ignore[arg-type]
    )
    return _to_approval_response(approval)


@router.get("/approvals/{approval_id}", response_model=ApprovalResponse)
def get_approval(
    approval_id: str,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> ApprovalResponse:
    try:
        approval = engine.get_approval(approval_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_approval_response(approval)


@router.post("/approvals/{approval_id}/decide", response_model=ApprovalResponse)
async def decide_approval(
    approval_id: str,
    payload: DecideApprovalRequest,
    engine: WorkspaceEngine = Depends(get_workspace_engine),
) -> ApprovalResponse:
    decision = _parse_enum(ApprovalDecisionType, payload.decision, "approval decision")
    try:
        approval = await engine.decide_approval(
            payload.workspace_id,
            approval_id,
            payload.approver_id,
            decision,  # type: ignore[arg-type]
            payload.actor_id,
            payload.comment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_approval_response(approval)


@router.get("/notifications/{recipient_id}", response_model=list[NotificationResponse])
def list_notifications(
    recipient_id: str,
    notification_engine: NotificationEnginePort = Depends(get_notification_engine),
) -> list[NotificationResponse]:
    notifications = notification_engine.list_for_recipient(recipient_id)
    return [
        NotificationResponse(
            id=n.id,
            workspace_id=n.workspace_id,
            recipient_id=n.recipient_id,
            channel=n.channel.value,
            type=n.type,
            payload=n.payload,
            created_at=n.created_at,
            read_at=n.read_at,
        )
        for n in notifications
    ]


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: str,
    notification_engine: NotificationEnginePort = Depends(get_notification_engine),
) -> NotificationResponse:
    try:
        notification = notification_engine.mark_read(notification_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return NotificationResponse(
        id=notification.id,
        workspace_id=notification.workspace_id,
        recipient_id=notification.recipient_id,
        channel=notification.channel.value,
        type=notification.type,
        payload=notification.payload,
        created_at=notification.created_at,
        read_at=notification.read_at,
    )


@router.get("/workspaces/{workspace_id}/activity", response_model=list[ActivityEntryResponse])
def list_activity(
    workspace_id: str,
    activity_type: str | None = None,
    actor_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    activity_feed: ActivityFeedPort = Depends(get_activity_feed),
) -> list[ActivityEntryResponse]:
    parsed_type = (
        _parse_enum(ActivityType, activity_type, "activity type") if activity_type else None
    )
    entries = activity_feed.query(
        workspace_id,
        activity_type=parsed_type,  # type: ignore[arg-type]
        actor_id=actor_id,
        target_type=target_type,
        target_id=target_id,
    )
    return [_to_activity_response(e) for e in entries]
