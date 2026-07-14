import pytest

from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.document_intelligence.classification.keyword_classifier import KeywordClassifier
from tmis.document_intelligence.schemas.classification import DocumentCategory
from tmis.legal_knowledge_graph.semantic_engine.engine import SemanticEngine

FIRM = "firm-a"
OTHER_FIRM = "firm-b"


def _engine() -> SemanticEngine:
    return SemanticEngine(HashingEmbeddingProvider(), KeywordClassifier())


async def test_search_by_intent_ranks_indexed_nodes() -> None:
    engine = _engine()
    await engine.index_node(FIRM, "node-clause", "clause de confidentialité")
    await engine.index_node(FIRM, "node-unrelated", "facture impayée du mois de mars")

    matches = await engine.search_by_intent(FIRM, "clause de confidentialité")

    assert matches[0].node_id == "node-clause"
    assert matches[0].score >= matches[-1].score


async def test_search_by_intent_is_scoped_per_firm() -> None:
    engine = _engine()
    await engine.index_node(FIRM, "node-a", "clause de confidentialité")
    await engine.index_node(OTHER_FIRM, "node-b", "clause de confidentialité")

    matches = await engine.search_by_intent(FIRM, "clause de confidentialité")

    assert [m.node_id for m in matches] == ["node-a"]


async def test_similar_to_excludes_the_queried_node_itself() -> None:
    engine = _engine()
    await engine.index_node(FIRM, "node-a", "bonne foi contractuelle")
    await engine.index_node(FIRM, "node-b", "bonne foi contractuelle et loyauté")

    matches = await engine.similar_to(FIRM, "node-a")

    assert "node-a" not in [m.node_id for m in matches]
    assert "node-b" in [m.node_id for m in matches]


async def test_similar_to_raises_key_error_for_unindexed_node() -> None:
    engine = _engine()

    with pytest.raises(KeyError):
        await engine.similar_to(FIRM, "unknown-node")


def test_classify_delegates_to_the_injected_classifier() -> None:
    engine = _engine()

    result = engine.classify("Le tribunal juge que le contrat est résilié par jugement du 12 mars.")

    assert result.category is DocumentCategory.JUDGMENT
