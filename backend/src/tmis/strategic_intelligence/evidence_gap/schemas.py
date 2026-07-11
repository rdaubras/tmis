from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvidenceGap:
    """One missing piece of evidence, always paired with why it matters
    and what obtaining it could change — never a bare list of missing
    items."""

    missing_evidence: str
    interest: str
    potential_impact: str
