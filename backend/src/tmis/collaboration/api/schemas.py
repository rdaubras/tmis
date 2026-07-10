from datetime import datetime

from pydantic import BaseModel


class CreateWorkspaceRequest(BaseModel):
    firm_id: str
    name: str
    actor_id: str


class WorkspaceResponse(BaseModel):
    id: str
    firm_id: str
    name: str
    member_ids: list[str]
    task_ids: list[str]
    created_at: datetime


class InviteMemberRequest(BaseModel):
    email: str
    display_name: str
    actor_id: str


class ChangeMemberStatusRequest(BaseModel):
    workspace_id: str
    target: str
    actor_id: str


class MemberResponse(BaseModel):
    id: str
    workspace_id: str
    email: str
    display_name: str
    status: str
    invited_at: datetime | None
    activated_at: datetime | None


class AssignRoleRequest(BaseModel):
    role: str
    actor_id: str


class CreateTaskRequest(BaseModel):
    title: str
    actor_id: str
    description: str = ""
    case_id: str | None = None
    assignee_id: str | None = None
    priority: str = "medium"
    due_date: datetime | None = None
    depends_on: list[str] = []


class UpdateTaskStatusRequest(BaseModel):
    workspace_id: str
    target: str
    actor_id: str


class TaskResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    description: str
    case_id: str | None
    assignee_id: str | None
    priority: str
    due_date: datetime | None
    status: str
    document_ids: list[str]
    comment_ids: list[str]
    depends_on: list[str]
    created_at: datetime | None
    updated_at: datetime | None


class AddCommentRequest(BaseModel):
    workspace_id: str
    target_type: str
    target_id: str
    author_id: str
    text: str
    attachment_ids: list[str] = []


class CommentResponse(BaseModel):
    id: str
    workspace_id: str
    target_type: str
    target_id: str
    author_id: str
    text: str
    parent_id: str | None
    attachment_ids: list[str]
    created_at: datetime | None


class RequestApprovalRequest(BaseModel):
    workspace_id: str
    target_type: str
    target_id: str
    requested_by: str
    approver_ids: list[str]
    mode: str = "single"


class DecideApprovalRequest(BaseModel):
    workspace_id: str
    approver_id: str
    decision: str
    actor_id: str
    comment: str | None = None


class ApprovalResponse(BaseModel):
    id: str
    workspace_id: str
    target_type: str
    target_id: str
    requested_by: str
    approver_ids: list[str]
    mode: str
    status: str


class NotificationResponse(BaseModel):
    id: str
    workspace_id: str
    recipient_id: str
    channel: str
    type: str
    payload: dict[str, str]
    created_at: datetime | None
    read_at: datetime | None


class ActivityEntryResponse(BaseModel):
    id: str
    workspace_id: str
    actor_id: str
    activity_type: str
    target_type: str
    target_id: str
    summary: str
    occurred_at: datetime
