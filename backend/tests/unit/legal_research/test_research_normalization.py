from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.normalization.normalizer import SourceNormalizer
from tmis.legal_research.search.schemas import RelevanceScores


def test_normalize_maps_connector_document_fields() -> None:
    doc = ConnectorDocument(
        id="civ-1240",
        title="Code civil, article 1240",
        content="Tout fait quelconque...",
        connector="codes",
        metadata={"article": "1240", "date": "1804-01-01"},
    )
    results = SourceNormalizer().normalize([doc])

    assert len(results) == 1
    result = results[0]
    assert result.id == "civ-1240"
    assert result.reference == "1240"
    assert result.date == "1804-01-01"
    assert result.connector == "codes"


def test_normalize_drops_exact_id_duplicates() -> None:
    doc = ConnectorDocument(
        id="dup-1", title="Title", content="Same content", connector="codes"
    )
    results = SourceNormalizer().normalize([doc, doc])
    assert len(results) == 1


def test_normalize_keeps_latest_version_of_duplicated_content() -> None:
    old = ConnectorDocument(
        id="v1",
        title="Article X",
        content="Identical body text.",
        connector="codes",
        metadata={"date": "2010-01-01"},
    )
    newer = ConnectorDocument(
        id="v2",
        title="Article X",
        content="Identical body text.",
        connector="codes",
        metadata={"date": "2022-01-01"},
    )
    results = SourceNormalizer().normalize([old, newer])

    assert len(results) == 1
    assert results[0].id == "v2"


def test_normalize_attaches_relevance_scores() -> None:
    doc = ConnectorDocument(id="d1", title="T", content="C", connector="codes")
    scores = {"d1": RelevanceScores(lexical_score=0.5, vector_score=0.8)}
    results = SourceNormalizer().normalize([doc], scores=scores)

    assert results[0].lexical_score == 0.5
    assert results[0].vector_score == 0.8


def test_normalize_truncates_long_excerpts() -> None:
    doc = ConnectorDocument(id="d1", title="T", content="x" * 1000, connector="codes")
    results = SourceNormalizer().normalize([doc])
    assert len(results[0].excerpt) == 400
