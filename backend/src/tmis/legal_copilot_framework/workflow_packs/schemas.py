from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.ai_team.capabilities.schemas import LegalDomain


@dataclass(frozen=True, slots=True)
class WorkflowPack:
    """A named, versioned set of `workflow_automation.template_library.
    WorkflowTemplate` ids — the primitive already there is reused
    directly, never a second workflow-definition schema."""

    id: str
    name: str
    domain: LegalDomain
    version: int
    workflow_template_ids: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
