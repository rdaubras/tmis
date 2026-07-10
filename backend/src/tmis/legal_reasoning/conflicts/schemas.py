from dataclasses import dataclass
from enum import Enum


class ConflictType(str, Enum):
    DOCUMENT_CONTRADICTION = "document_contradiction"
    TEMPORAL_CONTRADICTION = "temporal_contradiction"
    FACT_INCONSISTENCY = "fact_inconsistency"
    DUPLICATE = "duplicate"


@dataclass(frozen=True, slots=True)
class Conflict:
    """One detected contradiction/inconsistency/duplicate, always
    explained (see docs/25-legal-reasoning.md — Conflict Detector)."""

    id: str
    type: ConflictType
    description: str
    explanation: str
    involved_ids: tuple[str, ...]
