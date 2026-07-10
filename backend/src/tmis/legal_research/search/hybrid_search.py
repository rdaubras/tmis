from tmis.ai.embeddings.similarity import cosine_similarity
from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.providers.ports import ResearchKernelPort
from tmis.legal_research.queries.schemas import ResearchQuery
from tmis.legal_research.search.schemas import RelevanceScores


class HybridResearchSearch:
    """Implements `ResearchSearchPort` by combining the LRE connectors'
    lexical search (via `TMISKernel.search_connectors`) with a vector
    re-score computed from `TMISKernel.embed`.

    Connectors return plain lexical matches with no score attached, so
    this class computes both signals itself: a keyword-overlap ratio for
    "lexical", and a cosine similarity between freshly-computed query/
    document embeddings for "vector" — since results are not pre-indexed
    in a vector store (see docs/21-legal-research.md — Query Engine).

    The connector call itself uses `query.normalized_text`, not the
    synonym-expanded `query.search_text`: the Sprint 2 connectors do a
    naive substring match, so appending several expansion terms to one
    query string would make it match nothing. The expanded text is only
    used for the vector re-score, where broadening the embedded text is
    a legitimate way to widen semantic recall.
    """

    def __init__(
        self,
        kernel: ResearchKernelPort,
        *,
        default_connectors: list[str] | None = None,
    ) -> None:
        self._kernel = kernel
        self._default_connectors = default_connectors

    async def execute(
        self, query: ResearchQuery, *, connector_names: list[str] | None = None
    ) -> tuple[list[ConnectorDocument], list[str], dict[str, RelevanceScores]]:
        targets = connector_names or self._default_connectors
        documents = await self._kernel.search_connectors(
            query.normalized_text,
            connector_names=targets,
            filters=query.filters or None,
        )
        vector_scores = await self._vector_scores(query.search_text, documents)
        lexical_scores = self._lexical_scores(query, documents)
        scores = {
            doc.id: RelevanceScores(
                lexical_score=lexical_scores.get(doc.id, 0.0),
                vector_score=vector_scores.get(doc.id, 0.0),
            )
            for doc in documents
        }
        used = sorted({doc.connector for doc in documents}) if documents else list(targets or [])
        return documents, used, scores

    def _lexical_scores(
        self, query: ResearchQuery, documents: list[ConnectorDocument]
    ) -> dict[str, float]:
        keywords = query.keywords
        if not keywords:
            return {}
        scores: dict[str, float] = {}
        for doc in documents:
            haystack = f"{doc.title} {doc.content}".lower()
            hits = sum(1 for kw in keywords if kw in haystack)
            scores[doc.id] = hits / len(keywords)
        return scores

    async def _vector_scores(
        self, search_text: str, documents: list[ConnectorDocument]
    ) -> dict[str, float]:
        if not documents:
            return {}
        texts = [search_text, *[f"{doc.title} {doc.content}" for doc in documents]]
        vectors = await self._kernel.embed(texts)
        query_vector, doc_vectors = vectors[0], vectors[1:]
        return {
            doc.id: cosine_similarity(query_vector, vector)
            for doc, vector in zip(documents, doc_vectors, strict=True)
        }
