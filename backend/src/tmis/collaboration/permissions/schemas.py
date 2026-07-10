from enum import Enum


class Permission(str, Enum):
    """Granular permissions checked throughout the LCE (see
    docs/35-guide-permissions.md). Every permission is independently
    configurable per role and per member — this enum only names the
    checks, `permissions.engine.ConfigurablePermissionEngine` owns the
    actual matrix.
    """

    WORKSPACE_MANAGE = "workspace.manage"
    MEMBER_INVITE = "member.invite"
    MEMBER_MANAGE = "member.manage"
    ROLE_ASSIGN = "role.assign"
    CASE_READ = "case.read"
    CASE_WRITE = "case.write"
    DOCUMENT_READ = "document.read"
    DOCUMENT_WRITE = "document.write"
    DOCUMENT_DELETE = "document.delete"
    TASK_CREATE = "task.create"
    TASK_ASSIGN = "task.assign"
    TASK_UPDATE = "task.update"
    COMMENT_WRITE = "comment.write"
    APPROVAL_REQUEST = "approval.request"
    APPROVAL_DECIDE = "approval.decide"
    SHARING_CREATE_LINK = "sharing.create_link"
    SHARING_REVOKE_LINK = "sharing.revoke_link"
