import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from tmis.knowledge_graph.federation.schemas import GraphOrigin


class ResolutionStatus(StrEnum):
    """CONFIRMED: confidence met the threshold, no human involved.
    PENDING_VALIDATION: below threshold, routed to
    `HumanValidationEngine` and awaiting its decision. REJECTED: a
    human validator decided the occurrences are not the same entity."""

    CONFIRMED = "confirmed"
    PENDING_VALIDATION = "pending_validation"
    REJECTED = "rejected"


def new_resolved_entity_id() -> str:
    return f"resent-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class EntityOccurrence:
    """One graph's reference to what may be a real-world entity —
    `origin` reuses `federation.GraphOrigin` rather than a second
    "which graph" vocabulary."""

    origin: GraphOrigin
    node_id: str
    label: str


@dataclass(slots=True)
class ResolvedEntity:
    """A canonical entity plus every occurrence that was matched to
    it. `occurrences` is never a copy of graph data beyond the
    (origin, node_id, label) triple needed to identify *where* to look
    — the actual node content is always fetched fresh through
    `federation.FederationQueryEngine`."""

    id: str
    firm_id: str
    occurrences: tuple[EntityOccurrence, ...]
    confidence: float
    status: ResolutionStatus
    validation_request_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
