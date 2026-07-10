from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.case_intelligence.actors.schemas import Actor, CaseActorRole
from tmis.case_intelligence.evidence.schemas import EvidenceLink
from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.issues.schemas import LegalIssue
from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry, TimelineInconsistency


@dataclass
class CaseTask:
    id: str
    description: str
    done: bool = False


@dataclass
class CaseProfile:
    """The living case object: everything the CIE knows about a dossier,
    aggregated from every document processed for it (see
    docs/19-case-intelligence.md).
    """

    case_id: str
    title: str
    actors: list[Actor] = field(default_factory=list)
    actor_roles: dict[str, CaseActorRole] = field(default_factory=dict)
    document_ids: set[str] = field(default_factory=set)
    timeline: list[CaseTimelineEntry] = field(default_factory=list)
    timeline_inconsistencies: list[TimelineInconsistency] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)
    evidence_links: list[EvidenceLink] = field(default_factory=list)
    legal_issues: list[LegalIssue] = field(default_factory=list)
    tasks: list[CaseTask] = field(default_factory=list)
    ai_history: list[str] = field(default_factory=list)
    is_deleted: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def actors_with_role(self, role: CaseActorRole) -> list[Actor]:
        return [actor for actor in self.actors if self.actor_roles.get(actor.id) == role]

    @property
    def clients(self) -> list[Actor]:
        return self.actors_with_role(CaseActorRole.CLIENT)

    @property
    def opposing_parties(self) -> list[Actor]:
        return self.actors_with_role(CaseActorRole.OPPOSING_PARTY)

    @property
    def lawyers(self) -> list[Actor]:
        return self.actors_with_role(CaseActorRole.LAWYER)

    @property
    def jurisdictions(self) -> list[Actor]:
        return self.actors_with_role(CaseActorRole.JURISDICTION)

    def record_ai_action(self, action: str) -> None:
        self.ai_history.append(f"{datetime.now(UTC).isoformat()}: {action}")
