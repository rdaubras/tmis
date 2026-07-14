from tmis.ai.embeddings.ports import EmbeddingProviderPort
from tmis.ai.embeddings.similarity import cosine_similarity
from tmis.document_intelligence.classification.ports import ClassifierPort
from tmis.document_intelligence.schemas.classification import ClassificationResult
from tmis.legal_knowledge_graph.semantic_engine.schemas import SemanticMatch


class SemanticEngine:
    """The Sprint 25 "semantic layer": intent search, context
    understanding, concept matching, similarity detection and
    classification — all as an orchestration layer over engines that
    already exist (`ai.embeddings.HashingEmbeddingProvider`, `ai.
    embeddings.similarity.cosine_similarity`, `document_intelligence.
    classification`). Never a second embedding model or vector store:
    the in-memory index below is the same brute-force cosine search
    `ai.rag.InMemoryVectorIndex` already uses, adapted to graph node
    ids instead of document chunks."""

    def __init__(
        self, embedding_provider: EmbeddingProviderPort, classifier: ClassifierPort
    ) -> None:
        self._embedding_provider = embedding_provider
        self._classifier = classifier
        self._vectors: dict[str, tuple[str, list[float]]] = {}

    async def index_node(self, firm_id: str, node_id: str, text: str) -> None:
        [vector] = await self._embedding_provider.embed([text])
        self._vectors[node_id] = (firm_id, vector)

    async def search_by_intent(
        self, firm_id: str, query: str, top_k: int = 5
    ) -> list[SemanticMatch]:
        [query_vector] = await self._embedding_provider.embed([query])
        return self._ranked_matches(firm_id, query_vector, top_k, exclude_node_id=None)

    async def similar_to(self, firm_id: str, node_id: str, top_k: int = 5) -> list[SemanticMatch]:
        entry = self._vectors.get(node_id)
        if entry is None:
            raise KeyError(node_id)
        _, vector = entry
        return self._ranked_matches(firm_id, vector, top_k, exclude_node_id=node_id)

    def classify(self, text: str) -> ClassificationResult:
        return self._classifier.classify(text)

    def _ranked_matches(
        self, firm_id: str, query_vector: list[float], top_k: int, exclude_node_id: str | None
    ) -> list[SemanticMatch]:
        scored = [
            SemanticMatch(node_id=node_id, score=cosine_similarity(query_vector, vector))
            for node_id, (node_firm_id, vector) in self._vectors.items()
            if node_firm_id == firm_id and node_id != exclude_node_id
        ]
        scored.sort(key=lambda match: match.score, reverse=True)
        return scored[:top_k]
