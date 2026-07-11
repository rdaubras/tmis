from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from tmis.ai_team.capabilities.schemas import LegalDomain


class MissionComplexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(slots=True)
class Team:
    """A composed group of agent ids ready to work a mission together
    (see docs/54-guide-creation-equipe.md). Holds only ids, never
    agent instances — the registry/bootstrap layer resolves ids to
    runtime agents."""

    id: str
    name: str
    member_agent_ids: list[str]
    domain: LegalDomain = LegalDomain.GENERAL
    is_custom: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
