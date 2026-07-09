from tmis.ai.schemas.connector import ConnectorDocument


def search_fixture(query: str, fixture: list[ConnectorDocument]) -> list[ConnectorDocument]:
    """Naive substring search over an in-memory fixture, shared by the
    Sprint 2 connector placeholders (see docs/09-roadmap-30-sprints.md)."""
    needle = query.lower()
    return [doc for doc in fixture if needle in doc.content.lower() or needle in doc.title.lower()]
