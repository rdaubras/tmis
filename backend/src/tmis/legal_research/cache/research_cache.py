import dataclasses
import json
import uuid

from tmis.ai.cache.ports import CachePort
from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.cache.schemas import RawSearchCacheEntry, ResearchCacheConfig
from tmis.legal_research.ranking.schemas import RankingWeights
from tmis.legal_research.search.schemas import RelevanceScores, ResearchResult


class ResearchCache:
    """Extends the Kernel's `CachePort` with three explicit layers (see
    docs/21-legal-research.md — Cache): raw connector search results,
    normalized results, and ranked results. Each layer is (de)serialized
    manually rather than through a generic recursive serializer, since
    the three payload shapes differ enough that a generic serializer
    would need to reverse-engineer which dataclass to rebuild.

    ADR-RESEARCH-01 (see docs/21-legal-research.md): `firm_id` is
    prefixed into every key this class builds, at all three layers. Some
    connectors (`private_database`, a firm's own licensed source) can
    return results a cabinet has no right to see outside its own
    subscription — a cache entry keyed only by `(search_text,
    connector_names, weights)` would serve cabinet A's private-connector
    results to cabinet B on the next identical query. That is a leak, not
    an optimization, so there is no code path in this class that builds a
    key without `firm_id`.
    """

    def __init__(
        self,
        cache: CachePort,
        firm_id: uuid.UUID | str,
        config: ResearchCacheConfig | None = None,
    ) -> None:
        self._cache = cache
        self._firm_id = str(firm_id)
        self._config = config or ResearchCacheConfig()

    # ------------------------------------------------------------------
    # Layer 1 — raw connector search results
    # ------------------------------------------------------------------
    async def get_raw_search(
        self, search_text: str, connector_names: list[str] | None
    ) -> RawSearchCacheEntry | None:
        raw = await self._cache.get(self._raw_key(search_text, connector_names))
        if raw is None:
            return None
        payload = json.loads(raw)
        return RawSearchCacheEntry(
            documents=tuple(ConnectorDocument(**doc) for doc in payload["documents"]),
            connectors_used=tuple(payload["connectors_used"]),
            scores={
                doc_id: RelevanceScores(**scores) for doc_id, scores in payload["scores"].items()
            },
        )

    async def set_raw_search(
        self, search_text: str, connector_names: list[str] | None, entry: RawSearchCacheEntry
    ) -> None:
        payload = {
            "documents": [dataclasses.asdict(doc) for doc in entry.documents],
            "connectors_used": list(entry.connectors_used),
            "scores": {
                doc_id: dataclasses.asdict(scores) for doc_id, scores in entry.scores.items()
            },
        }
        await self._cache.set(
            self._raw_key(search_text, connector_names),
            json.dumps(payload),
            ttl_seconds=self._config.raw_search_ttl_seconds,
        )

    # ------------------------------------------------------------------
    # Layer 2 — normalized results
    # ------------------------------------------------------------------
    async def get_normalized(
        self, search_text: str, connector_names: list[str] | None
    ) -> list[ResearchResult] | None:
        raw = await self._cache.get(self._normalized_key(search_text, connector_names))
        if raw is None:
            return None
        return [ResearchResult(**item) for item in json.loads(raw)]

    async def set_normalized(
        self,
        search_text: str,
        connector_names: list[str] | None,
        results: list[ResearchResult],
    ) -> None:
        await self._cache.set(
            self._normalized_key(search_text, connector_names),
            json.dumps([dataclasses.asdict(r) for r in results]),
            ttl_seconds=self._config.normalized_ttl_seconds,
        )

    # ------------------------------------------------------------------
    # Layer 3 — ranked results (depend on the weights used)
    # ------------------------------------------------------------------
    async def get_ranking(
        self,
        search_text: str,
        connector_names: list[str] | None,
        weights: RankingWeights,
    ) -> list[ResearchResult] | None:
        raw = await self._cache.get(self._ranking_key(search_text, connector_names, weights))
        if raw is None:
            return None
        return [ResearchResult(**item) for item in json.loads(raw)]

    async def set_ranking(
        self,
        search_text: str,
        connector_names: list[str] | None,
        weights: RankingWeights,
        results: list[ResearchResult],
    ) -> None:
        await self._cache.set(
            self._ranking_key(search_text, connector_names, weights),
            json.dumps([dataclasses.asdict(r) for r in results]),
            ttl_seconds=self._config.ranking_ttl_seconds,
        )

    # ------------------------------------------------------------------
    # Key helpers
    # ------------------------------------------------------------------
    def _connector_key(self, connector_names: list[str] | None) -> str:
        return ",".join(sorted(connector_names)) if connector_names else "*"

    def _raw_key(self, search_text: str, connector_names: list[str] | None) -> str:
        return (
            f"legal_research:{self._firm_id}:raw:{search_text}:"
            f"{self._connector_key(connector_names)}"
        )

    def _normalized_key(self, search_text: str, connector_names: list[str] | None) -> str:
        return (
            f"legal_research:{self._firm_id}:normalized:{search_text}:"
            f"{self._connector_key(connector_names)}"
        )

    def _ranking_key(
        self, search_text: str, connector_names: list[str] | None, weights: RankingWeights
    ) -> str:
        weights_key = f"{weights.lexical}:{weights.vector}:{weights.authority}:{weights.freshness}"
        return (
            f"legal_research:{self._firm_id}:ranking:{search_text}:"
            f"{self._connector_key(connector_names)}:{weights_key}"
        )
