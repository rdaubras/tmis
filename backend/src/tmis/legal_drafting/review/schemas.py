from dataclasses import dataclass
from enum import Enum


class ReviewFindingType(str, Enum):
    REPETITION = "repetition"
    CONTRADICTION = "contradiction"
    INCOMPLETE_SECTION = "incomplete_section"
    MISSING_REFERENCE = "missing_reference"
    UNJUSTIFIED_PARAGRAPH = "unjustified_paragraph"


@dataclass(frozen=True, slots=True)
class ReviewFinding:
    """One issue the Review Engine surfaces — never auto-corrected, only
    reported for the avocat to act on (see docs/28-legal-drafting.md —
    Review Engine)."""

    id: str
    type: ReviewFindingType
    description: str
    section_id: str | None = None
    paragraph_id: str | None = None
