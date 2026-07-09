import re
from dataclasses import dataclass
from enum import Enum

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        if not _EMAIL_RE.match(self.value):
            raise ValueError(f"Invalid email address: {self.value!r}")


class Role(str, Enum):
    LAWYER = "lawyer"
    COLLABORATOR = "collaborator"
    FIRM_ADMIN = "firm_admin"
    PLATFORM_ADMIN = "platform_admin"


class Permission(str, Enum):
    CASE_READ = "case:read"
    CASE_WRITE = "case:write"
    DOCUMENT_READ = "document:read"
    DOCUMENT_WRITE = "document:write"
    FIRM_MANAGE = "firm:manage"
    PLATFORM_MANAGE = "platform:manage"


DEFAULT_ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.LAWYER: frozenset(
        {
            Permission.CASE_READ,
            Permission.CASE_WRITE,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_WRITE,
        }
    ),
    Role.COLLABORATOR: frozenset({Permission.CASE_READ, Permission.DOCUMENT_READ}),
    Role.FIRM_ADMIN: frozenset(
        {
            Permission.CASE_READ,
            Permission.CASE_WRITE,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_WRITE,
            Permission.FIRM_MANAGE,
        }
    ),
    Role.PLATFORM_ADMIN: frozenset(set(Permission)),
}
