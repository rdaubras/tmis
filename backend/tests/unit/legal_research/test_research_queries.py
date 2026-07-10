from tmis.legal_research.queries.engine import HeuristicQueryEngine


def test_build_normalizes_whitespace() -> None:
    query = HeuristicQueryEngine().build("  quelle   est la  procédure  de licenciement ?  ")
    assert query.normalized_text == "quelle est la procédure de licenciement ?"


def test_build_detects_french() -> None:
    query = HeuristicQueryEngine().build("quelle est la procédure de licenciement")
    assert query.language == "fr"


def test_build_detects_english() -> None:
    query = HeuristicQueryEngine().build("what is the procedure for this contract")
    assert query.language == "en"


def test_build_extracts_keywords_without_stopwords() -> None:
    query = HeuristicQueryEngine().build("quelle est la procédure de licenciement")
    assert "licenciement" in query.keywords
    assert "de" not in query.keywords
    assert "la" not in query.keywords


def test_build_expands_known_legal_terms() -> None:
    query = HeuristicQueryEngine().build("procédure de licenciement")
    assert "rupture du contrat de travail" in query.expanded_terms


def test_build_returns_empty_expansion_for_unknown_terms() -> None:
    query = HeuristicQueryEngine().build("xyzzy plugh")
    assert query.expanded_terms == ()


def test_search_text_appends_expansion_terms_not_already_present() -> None:
    query = HeuristicQueryEngine().build("licenciement")
    assert "rupture du contrat de travail" in query.search_text
    assert query.normalized_text in query.search_text


def test_build_carries_filters_through() -> None:
    query = HeuristicQueryEngine().build("bail commercial", {"jurisdiction": "Paris"})
    assert query.filters == {"jurisdiction": "Paris"}
