from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    """The six roles the Sprint 8 prompt asks for (see
    docs/34-guide-roles.md)."""

    ADMINISTRATOR = "administrator"
    ASSOCIATE = "associate"
    COLLABORATOR = "collaborator"
    JURIST = "jurist"
    ASSISTANT = "assistant"
    CLIENT = "client"


@dataclass(frozen=True, slots=True)
class RoleAssignment:
    workspace_id: str
    member_id: str
    role: Role
