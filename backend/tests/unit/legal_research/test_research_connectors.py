import pytest

from tmis.ai.connectors.manager import ConnectorManager
from tmis.legal_research.connectors.internal_documentation_connector import (
    InternalDocumentationConnector,
)
from tmis.legal_research.connectors.private_database_connector import PrivateDatabaseConnector
from tmis.legal_research.connectors.registration import register_legal_research_connectors


@pytest.mark.asyncio
async def test_internal_documentation_connector_search_matches_content() -> None:
    connector = InternalDocumentationConnector()
    results = await connector.search("non-concurrence")
    assert results
    assert all(r.connector == "internal_documentation" for r in results)


@pytest.mark.asyncio
async def test_internal_documentation_connector_fetch_unknown_returns_none() -> None:
    connector = InternalDocumentationConnector()
    assert await connector.fetch("does-not-exist") is None


@pytest.mark.asyncio
async def test_private_database_connector_search_matches_content() -> None:
    connector = PrivateDatabaseConnector()
    results = await connector.search("non-concurrence")
    assert results
    assert results[0].connector == "private_database"


@pytest.mark.asyncio
async def test_private_database_connector_fetch_known_document() -> None:
    connector = PrivateDatabaseConnector()
    document = await connector.fetch("private-db-arret-2021-4521")
    assert document is not None
    assert document.title.startswith("Cass. soc.")


def test_register_legal_research_connectors_adds_both_to_manager() -> None:
    manager = ConnectorManager()
    register_legal_research_connectors(manager)
    assert "internal_documentation" in manager.list_connectors()
    assert "private_database" in manager.list_connectors()
    assert manager.is_enabled("internal_documentation")
    assert manager.is_enabled("private_database")


@pytest.mark.asyncio
async def test_registered_connectors_are_reachable_through_the_manager() -> None:
    manager = ConnectorManager()
    register_legal_research_connectors(manager)
    results = await manager.search("non-concurrence", connector_names=["internal_documentation"])
    assert results
    assert results[0].connector == "internal_documentation"
