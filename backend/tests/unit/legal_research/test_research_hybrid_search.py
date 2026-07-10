import pytest

from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.queries.engine import HeuristicQueryEngine
from tmis.legal_research.search.hybrid_search import HybridResearchSearch

_DOC_LICENCIEMENT = ConnectorDocument(
    id="d1",
    title="Licenciement abusif",
    content="Le licenciement doit être justifié par une cause réelle et sérieuse.",
    connector="codes",
)
_DOC_BAIL = ConnectorDocument(
    id="d2",
    title="Bail commercial",
    content="Contrat de location d'un local commercial.",
    connector="jurisprudence",
)


class _FakeKernel:
    def __init__(self, documents: list[ConnectorDocument]) -> None:
        self._documents = documents
        self.last_query: str | None = None

    async def search_connectors(
        self,
        query: str,
        *,
        connector_names: list[str] | None = None,
        filters: dict[str, object] | None = None,
        use_cache: bool = True,
    ) -> list[ConnectorDocument]:
        self.last_query = query
        return self._documents

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] if "licenciement" in t.lower() else [0.0, 1.0] for t in texts]


@pytest.mark.asyncio
async def test_execute_returns_documents_from_the_kernel() -> None:
    kernel = _FakeKernel([_DOC_LICENCIEMENT, _DOC_BAIL])
    search = HybridResearchSearch(kernel)
    query = HeuristicQueryEngine().build("licenciement")

    documents, used, scores = await search.execute(query)

    assert documents == [_DOC_LICENCIEMENT, _DOC_BAIL]
    assert used == ["codes", "jurisprudence"]
    assert set(scores) == {"d1", "d2"}


@pytest.mark.asyncio
async def test_execute_scores_matching_document_higher_on_both_axes() -> None:
    kernel = _FakeKernel([_DOC_LICENCIEMENT, _DOC_BAIL])
    search = HybridResearchSearch(kernel)
    query = HeuristicQueryEngine().build("licenciement")

    _documents, _used, scores = await search.execute(query)

    assert scores["d1"].lexical_score == 1.0
    assert scores["d1"].vector_score == 1.0
    assert scores["d2"].lexical_score == 0.0
    assert scores["d2"].vector_score == 0.0


@pytest.mark.asyncio
async def test_execute_with_no_results_returns_empty_scores() -> None:
    kernel = _FakeKernel([])
    search = HybridResearchSearch(kernel, default_connectors=["codes"])
    query = HeuristicQueryEngine().build("licenciement")

    documents, used, scores = await search.execute(query)

    assert documents == []
    assert used == ["codes"]
    assert scores == {}


@pytest.mark.asyncio
async def test_execute_sends_the_normalized_text_to_the_kernel_not_the_expanded_one() -> None:
    """Connectors do a naive substring match, so the query sent to
    `search_connectors` must stay unexpanded — see `HybridResearchSearch`
    docstring for why appending synonyms would break that match."""
    kernel = _FakeKernel([])
    search = HybridResearchSearch(kernel)
    query = HeuristicQueryEngine().build("licenciement")

    await search.execute(query)

    assert kernel.last_query == query.normalized_text
