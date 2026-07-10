from dataclasses import dataclass, field

from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.search.schemas import RelevanceScores


@dataclass(frozen=True, slots=True)
class ResearchCacheConfig:
    """Per-layer expiration rules (see docs/21-legal-research.md — Cache).

    Raw connector results change least often relative to how expensive
    they are to re-fetch, so they get the longest TTL; rankings depend on
    caller-supplied weights and are cheap to recompute, so they expire
    fastest.
    """

    raw_search_ttl_seconds: int = 600
    normalized_ttl_seconds: int = 300
    ranking_ttl_seconds: int = 120


@dataclass(frozen=True, slots=True)
class RawSearchCacheEntry:
    documents: tuple[ConnectorDocument, ...]
    connectors_used: tuple[str, ...]
    scores: dict[str, RelevanceScores] = field(default_factory=dict)
