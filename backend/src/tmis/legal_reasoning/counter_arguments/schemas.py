from dataclasses import dataclass


@dataclass(slots=True)
class CounterArgument:
    """An element susceptible to contradict one `Argument` — always kept
    alongside it so the reasoning presents both sides (see
    docs/25-legal-reasoning.md — Counter Argument Engine)."""

    id: str
    argument_id: str
    claim: str
    source_connector: str
    source_reference: str
    excerpt: str
    confidence: float = 0.0
