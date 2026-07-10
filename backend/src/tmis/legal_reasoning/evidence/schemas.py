from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReasoningEvidenceLink:
    """Connects one piece of evidence to a fact, a document, a hypothesis
    and — when applicable — the argument it grounds, with a reliability
    score (see docs/25-legal-reasoning.md — Evidence Engine). Any of the
    id fields may be `None` when that dimension doesn't apply (e.g. a
    fact with no single source document)."""

    id: str
    fact_id: str | None
    document_id: str | None
    hypothesis_id: str | None
    argument_id: str | None
    reliability_score: float
