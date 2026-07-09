from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Citation:
    """A traceable reference to a source passage, attached to any AI output
    that relies on retrieved content (see docs/06-strategie-rag.md)."""

    source_id: str
    connector: str
    excerpt: str
    reference: str


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A chunk of content returned by the retrieval pipeline, scored and
    ready to be reranked or turned into a `Citation`."""

    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict[str, str]

    def to_citation(self, connector: str, reference: str) -> Citation:
        return Citation(
            source_id=self.chunk_id,
            connector=connector,
            excerpt=self.content,
            reference=reference,
        )
