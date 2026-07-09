import pytest

from tmis.ai.connectors.codes_connector import CodesConnector
from tmis.ai.connectors.exceptions import ConnectorAuthenticationError, ConnectorError
from tmis.ai.connectors.manager import ConnectorManager
from tmis.ai.connectors.ports import ConnectorPort
from tmis.ai.schemas.connector import ConnectorDocument


@pytest.mark.asyncio
async def test_codes_connector_search_matches_content() -> None:
    connector = CodesConnector()
    results = await connector.search("dommage")
    assert any("1240" in doc.title for doc in results)


@pytest.mark.asyncio
async def test_codes_connector_fetch_by_id() -> None:
    connector = CodesConnector()
    doc = await connector.fetch("civ-1240")
    assert doc is not None
    assert doc.connector == "codes"


@pytest.mark.asyncio
async def test_connector_without_api_key_raises_authentication_error() -> None:
    connector = CodesConnector(api_key=None)
    with pytest.raises(ConnectorAuthenticationError):
        await connector.search("dommage")


@pytest.mark.asyncio
async def test_manager_search_fans_out_to_all_enabled_connectors() -> None:
    manager = ConnectorManager()
    results = await manager.search("dommage")
    assert any(doc.connector == "codes" for doc in results)


@pytest.mark.asyncio
async def test_manager_disable_excludes_connector_from_search() -> None:
    manager = ConnectorManager()
    manager.disable("codes")
    results = await manager.search("dommage")
    assert all(doc.connector != "codes" for doc in results)
    assert manager.is_enabled("codes") is False

    manager.enable("codes")
    assert manager.is_enabled("codes") is True


class _AlwaysFailingConnector:
    connector_name = "flaky"

    async def search(
        self, query: str, filters: dict[str, object] | None = None
    ) -> list[ConnectorDocument]:
        raise ConnectorError(self.connector_name, "upstream is down")

    async def fetch(self, document_id: str) -> ConnectorDocument | None:
        raise ConnectorError(self.connector_name, "upstream is down")


@pytest.mark.asyncio
async def test_manager_search_isolates_a_failing_connector() -> None:
    manager = ConnectorManager()
    manager.register("flaky", _AlwaysFailingConnector())

    # Should not raise, and should still return results from healthy connectors.
    results = await manager.search("dommage")

    assert any(doc.connector == "codes" for doc in results)


def test_manager_lists_default_connectors() -> None:
    manager = ConnectorManager()
    assert set(manager.list_connectors()) == {"codes", "jurisprudence", "doctrine"}


def test_connector_port_is_structurally_satisfied_by_codes_connector() -> None:
    connector: ConnectorPort = CodesConnector()
    assert connector.connector_name == "codes"
