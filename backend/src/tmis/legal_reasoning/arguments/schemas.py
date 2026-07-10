from dataclasses import dataclass


@dataclass(slots=True)
class Argument:
    """One argument supporting a hypothesis, always keeping its
    provenance (see docs/25-legal-reasoning.md — Argument Engine): the
    connector and reference it came from, plus the excerpt actually used.
    """

    id: str
    hypothesis_id: str
    claim: str
    source_connector: str
    source_reference: str
    excerpt: str
    confidence: float = 0.0
