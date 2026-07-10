from dataclasses import dataclass
from enum import Enum


class ReferenceTargetType(str, Enum):
    """Every kind of source a paragraph's claim can be traced back to —
    see docs/28-legal-drafting.md — Paragraph Engine / Citation Engine.
    """

    FACT = "fact"
    RESEARCH_RESULT = "research_result"
    EVIDENCE = "evidence"
    HYPOTHESIS = "hypothesis"


@dataclass(frozen=True, slots=True)
class ReferenceLink:
    """A resolved, human-readable pointer from a paragraph back to one
    of the upstream engines (Case Intelligence, Legal Research, Legal
    Reasoning) — the raw ids a `Paragraph` carries, turned into
    something a citation or a reviewer can actually read."""

    id: str
    target_type: ReferenceTargetType
    target_id: str
    label: str
    excerpt: str
