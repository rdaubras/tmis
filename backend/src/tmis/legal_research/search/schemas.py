from dataclasses import dataclass, field


@dataclass(slots=True)
class ResearchResult:
    """One normalized, ranked result of a legal research query (see
    docs/21-legal-research.md — Source Normalizer / Ranking Engine).

    Mutable (unlike most TMIS schemas) because ranking rewrites
    `final_score` in place as results flow through the pipeline.
    """

    id: str
    title: str
    excerpt: str
    connector: str
    document_type: str
    reference: str
    date: str | None
    lexical_score: float = 0.0
    vector_score: float = 0.0
    authority_score: float = 0.0
    freshness_score: float = 0.0
    final_score: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RelevanceScores:
    """The two raw textual-relevance signals computed for one document by
    a `ResearchSearchPort`, before the Ranking Engine combines them with
    authority and freshness."""

    lexical_score: float = 0.0
    vector_score: float = 0.0


@dataclass(frozen=True, slots=True)
class ResearchResponse:
    """The full, traceable outcome of one research run, returned by the
    `ResearchOrchestrator` and served by the API."""

    search_id: str
    query: str
    results: tuple[ResearchResult, ...]
    connectors_used: tuple[str, ...]
    duration_ms: float
    cache_hit: bool = False
