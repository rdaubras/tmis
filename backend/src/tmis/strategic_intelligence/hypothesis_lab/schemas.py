"""Historized lifecycle for strategic hypotheses.

Unlike `tmis.legal_reasoning.hypotheses.Hypothesis` (simple
generate/validate/reject, no persisted history), the hypothesis lab
needs create/compare/merge/invalidate/archive with a full audit trail —
so it follows the append-only state-machine pattern already used by
`tmis.cabinet_knowledge.governance` rather than reusing that simpler
schema.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class HypothesisStatus(StrEnum):
    PROPOSED = "proposed"
    SUPPORTED = "supported"
    MERGED = "merged"
    INVALIDATED = "invalidated"
    ARCHIVED = "archived"


ALLOWED_TRANSITIONS: dict[HypothesisStatus, frozenset[HypothesisStatus]] = {
    HypothesisStatus.PROPOSED: frozenset(
        {
            HypothesisStatus.SUPPORTED,
            HypothesisStatus.MERGED,
            HypothesisStatus.INVALIDATED,
            HypothesisStatus.ARCHIVED,
        }
    ),
    HypothesisStatus.SUPPORTED: frozenset(
        {
            HypothesisStatus.MERGED,
            HypothesisStatus.INVALIDATED,
            HypothesisStatus.ARCHIVED,
        }
    ),
    HypothesisStatus.MERGED: frozenset({HypothesisStatus.ARCHIVED}),
    HypothesisStatus.INVALIDATED: frozenset({HypothesisStatus.ARCHIVED}),
    HypothesisStatus.ARCHIVED: frozenset(),
}


class InvalidHypothesisTransitionError(ValueError):
    def __init__(self, from_status: HypothesisStatus, to_status: HypothesisStatus) -> None:
        super().__init__(f"Cannot transition from {from_status.value} to {to_status.value}")
        self.from_status = from_status
        self.to_status = to_status


def new_hypothesis_id() -> str:
    return f"hyp-{uuid.uuid4().hex[:12]}"


def new_hypothesis_event_id() -> str:
    return f"hyp-evt-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class StrategicHypothesis:
    id: str
    case_id: str
    description: str
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    parent_ids: tuple[str, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class HypothesisEvent:
    id: str
    firm_id: str
    hypothesis_id: str
    from_status: HypothesisStatus
    to_status: HypothesisStatus
    actor: str
    reason: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class HypothesisComparison:
    hypothesis_a_id: str
    hypothesis_b_id: str
    similarity: float
    shared_terms: tuple[str, ...]
    differences: tuple[str, ...]
