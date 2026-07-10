import hashlib

from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.search.schemas import RelevanceScores, ResearchResult

_EXCERPT_MAX_CHARS = 400


class SourceNormalizer:
    """Implements `SourceNormalizerPort` (see docs/21-legal-research.md —
    Source Normalizer):

    - unifies each connector's ad-hoc `metadata` dict into the common
      `ResearchResult` fields (document type, reference, date);
    - drops exact id duplicates (the same connector returning the same
      document twice);
    - collapses near-duplicates (identical content reached through
      different ids, e.g. two connectors mirroring the same text) and
      keeps only the most recent version, using the `date` metadata field
      as the version marker.
    """

    def normalize(
        self,
        documents: list[ConnectorDocument],
        *,
        scores: dict[str, RelevanceScores] | None = None,
    ) -> list[ResearchResult]:
        scores = scores or {}
        seen_ids: set[str] = set()
        by_content_hash: dict[str, ResearchResult] = {}

        for doc in documents:
            if doc.id in seen_ids:
                continue
            seen_ids.add(doc.id)

            result = self._to_result(doc, scores.get(doc.id, RelevanceScores()))
            content_hash = self._content_hash(doc.content)
            existing = by_content_hash.get(content_hash)
            if existing is None or (result.date or "") > (existing.date or ""):
                by_content_hash[content_hash] = result

        return list(by_content_hash.values())

    def _content_hash(self, content: str) -> str:
        return hashlib.sha256(content.strip().lower().encode()).hexdigest()

    def _to_result(self, doc: ConnectorDocument, relevance: RelevanceScores) -> ResearchResult:
        metadata = dict(doc.metadata)
        reference = (
            metadata.get("reference")
            or metadata.get("article")
            or metadata.get("jurisdiction")
            or doc.id
        )
        date = metadata.get("date") or metadata.get("year")
        return ResearchResult(
            id=doc.id,
            title=doc.title,
            excerpt=doc.content[:_EXCERPT_MAX_CHARS],
            connector=doc.connector,
            document_type=metadata.get("category", doc.connector),
            reference=reference,
            date=date,
            lexical_score=relevance.lexical_score,
            vector_score=relevance.vector_score,
            metadata=metadata,
        )
