from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class WorkspaceSettings:
    """Per-workspace configuration — deliberately a small, extensible
    bag of fields rather than a rigid schema, so a firm can tune its
    workspace without a code change."""

    default_role: str = "collaborator"
    allow_client_comments: bool = False


@dataclass(slots=True)
class Workspace:
    """The primary logical boundary of the SaaS (see
    docs/33-legal-collaboration.md — Workspace Engine): a firm can own
    several workspaces, each scoping its own cases, users, teams,
    documents, tasks and conversations. `Workspace` only keeps *ids* —
    it never embeds `CaseProfile`, `Document`, etc.: those belong to
    their own bounded contexts (Sprints 3-7); the LCE only tracks which
    ones are visible in which workspace.
    """

    id: str
    firm_id: str
    name: str
    settings: WorkspaceSettings = field(default_factory=WorkspaceSettings)
    member_ids: set[str] = field(default_factory=set)
    case_ids: set[str] = field(default_factory=set)
    team_ids: set[str] = field(default_factory=set)
    document_ids: set[str] = field(default_factory=set)
    task_ids: set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
