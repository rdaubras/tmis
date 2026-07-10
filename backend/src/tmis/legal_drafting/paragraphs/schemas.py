from dataclasses import dataclass, field


@dataclass(slots=True)
class Paragraph:
    """One generated paragraph — always keeping full traceability (see
    docs/28-legal-drafting.md — Paragraph Engine): where it came from,
    and every fact, research reference, evidence link and hypothesis
    that justifies its content. A paragraph with none of these is
    exactly what `review.HeuristicReviewEngine` flags as unjustified.
    """

    id: str
    section_key: str
    order: int
    text: str
    origin: str
    fact_ids: tuple[str, ...] = field(default_factory=tuple)
    reference_ids: tuple[str, ...] = field(default_factory=tuple)
    evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    hypothesis_ids: tuple[str, ...] = field(default_factory=tuple)
