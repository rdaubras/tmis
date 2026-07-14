import httpx
import pytest

from tmis.ai.connectors.adapters.http_connector import HttpConnector
from tmis.ai.connectors.exceptions import ConnectorAuthenticationError, ConnectorError


def _client(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler)


@pytest.mark.asyncio
async def test_search_maps_json_results_into_connector_documents() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/search"
        assert request.url.params["q"] == "non-concurrence"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "doc-1",
                        "title": "Clause de non-concurrence",
                        "content": "Analyse de la clause.",
                        "metadata": {"year": "2023"},
                    }
                ]
            },
        )

    client = _client(httpx.MockTransport(handler))
    connector = HttpConnector(
        client, connector_name="doctrine", base_url="https://example.test/api"
    )

    results = await connector.search("non-concurrence")

    assert len(results) == 1
    assert results[0].id == "doc-1"
    assert results[0].connector == "doctrine"
    assert results[0].metadata == {"year": "2023"}


@pytest.mark.asyncio
async def test_search_accepts_a_bare_json_list() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"id": "1", "title": "t", "content": "c"}])

    client = _client(httpx.MockTransport(handler))
    connector = HttpConnector(client, connector_name="doctrine", base_url="https://example.test")

    results = await connector.search("q")
    assert len(results) == 1


@pytest.mark.asyncio
async def test_fetch_returns_none_on_404() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    client = _client(httpx.MockTransport(handler))
    connector = HttpConnector(client, connector_name="doctrine", base_url="https://example.test")

    assert await connector.fetch("missing") is None


@pytest.mark.asyncio
async def test_fetch_uses_the_configured_document_path_template() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/items/doc-42"
        return httpx.Response(200, json={"id": "doc-42", "title": "t", "content": "c"})

    client = _client(httpx.MockTransport(handler))
    connector = HttpConnector(
        client,
        connector_name="doctrine",
        base_url="https://example.test",
        document_path="/items/{id}",
    )

    document = await connector.fetch("doc-42")
    assert document is not None
    assert document.id == "doc-42"


@pytest.mark.asyncio
async def test_unauthorized_response_raises_authentication_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    client = _client(httpx.MockTransport(handler))
    connector = HttpConnector(client, connector_name="doctrine", base_url="https://example.test")

    with pytest.raises(ConnectorAuthenticationError):
        await connector.search("q")


@pytest.mark.asyncio
async def test_server_error_raises_connector_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = _client(httpx.MockTransport(handler))
    connector = HttpConnector(client, connector_name="doctrine", base_url="https://example.test")

    with pytest.raises(ConnectorError):
        await connector.search("q")


@pytest.mark.asyncio
async def test_api_key_is_sent_as_bearer_token() -> None:
    seen_headers = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(request.headers)
        return httpx.Response(200, json={"results": []})

    client = _client(httpx.MockTransport(handler))
    connector = HttpConnector(
        client, connector_name="doctrine", base_url="https://example.test", api_key="secret"
    )

    await connector.search("q")
    assert seen_headers.get("authorization") == "Bearer secret"
