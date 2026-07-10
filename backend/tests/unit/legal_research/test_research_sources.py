from tmis.legal_research.sources.registry import SourceRegistry
from tmis.legal_research.sources.schemas import SourceCategory, SourceDescriptor


def test_default_registry_knows_all_sprint_2_and_sprint_5_connectors() -> None:
    registry = SourceRegistry()
    known = {s.connector_name for s in registry.list_sources()}
    assert known == {
        "codes",
        "jurisprudence",
        "doctrine",
        "internal_documentation",
        "private_database",
    }


def test_authority_score_of_legislation_is_higher_than_doctrine() -> None:
    registry = SourceRegistry()
    assert registry.authority_score("codes") > registry.authority_score("doctrine")


def test_authority_score_falls_back_to_neutral_for_unknown_connector() -> None:
    registry = SourceRegistry()
    expected = SourceRegistry._DEFAULT_AUTHORITY_SCORE
    assert registry.authority_score("some_future_connector") == expected


def test_register_adds_a_new_source() -> None:
    registry = SourceRegistry()
    registry.register(
        SourceDescriptor(
            connector_name="custom",
            category=SourceCategory.DOCTRINE,
            display_name="Custom",
            authority_score=0.42,
        )
    )
    assert registry.authority_score("custom") == 0.42
    assert registry.get("custom") is not None
