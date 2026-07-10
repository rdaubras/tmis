from dataclasses import dataclass

from tmis.collaboration.event_bus import CollaborationEvent


@dataclass(frozen=True, kw_only=True)
class WorkspaceCreated(CollaborationEvent):
    pass


@dataclass(frozen=True, kw_only=True)
class MemberInvited(CollaborationEvent):
    member_id: str


@dataclass(frozen=True, kw_only=True)
class MemberStatusChanged(CollaborationEvent):
    member_id: str
    from_status: str
    to_status: str


@dataclass(frozen=True, kw_only=True)
class RoleAssigned(CollaborationEvent):
    member_id: str
    role: str


@dataclass(frozen=True, kw_only=True)
class TaskCreated(CollaborationEvent):
    task_id: str
    case_id: str | None


@dataclass(frozen=True, kw_only=True)
class TaskStatusChanged(CollaborationEvent):
    task_id: str
    from_status: str
    to_status: str


@dataclass(frozen=True, kw_only=True)
class CommentAdded(CollaborationEvent):
    comment_id: str
    target_type: str
    target_id: str


@dataclass(frozen=True, kw_only=True)
class MentionCreated(CollaborationEvent):
    mention_id: str
    comment_id: str
    mentioned_type: str
    mentioned_id: str


@dataclass(frozen=True, kw_only=True)
class ApprovalRequested(CollaborationEvent):
    approval_id: str
    target_type: str
    target_id: str


@dataclass(frozen=True, kw_only=True)
class ApprovalDecided(CollaborationEvent):
    approval_id: str
    status: str


@dataclass(frozen=True, kw_only=True)
class NotificationDispatched(CollaborationEvent):
    notification_id: str
    recipient_id: str
    channel: str


@dataclass(frozen=True, kw_only=True)
class ActivityRecorded(CollaborationEvent):
    activity_id: str
    action: str


@dataclass(frozen=True, kw_only=True)
class ShareLinkCreated(CollaborationEvent):
    share_id: str
    target_type: str
    target_id: str


@dataclass(frozen=True, kw_only=True)
class ShareLinkRevoked(CollaborationEvent):
    share_id: str
