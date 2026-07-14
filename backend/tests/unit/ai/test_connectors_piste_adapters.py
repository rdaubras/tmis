import httpx
import pytest

from tmis.ai.connectors.adapters.judilibre_connector import JudilibreConnector
from tmis.ai.connectors.adapters.legifrance_connector import LegifranceConnector
from tmis.ai.connectors.adapters.piste_oauth import PisteOAuthTokenProvider
from tmis.ai.connectors.exceptions import ConnectorAuthenticationError, ConnectorError


@pytest.mark.asyncio
async def test_token_provider_fetches_and_caches_the_token() -> None:
    token_requests = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_requests
        token_requests += 1
        return httpx.Response(200, json={"access_token": "tok-1", "expires_in": 3600})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = PisteOAuthTokenProvider(
        client, token_url="https://oauth.test/token", client_id="id", client_secret="secret"
    )

    token1 = await provider.get_token("codes")
    token2 = await provider.get_token("codes")

    assert token1 == token2 == "tok-1"
    assert token_requests == 1


@pytest.mark.asyncio
async def test_token_provider_raises_authentication_error_on_401() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = PisteOAuthTokenProvider(
        client, token_url="https://oauth.test/token", client_id="id", client_secret="wrong"
    )

    with pytest.raises(ConnectorAuthenticationError):
        await provider.get_token("codes")


def _oauth_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"access_token": "tok", "expires_in": 3600})


@pytest.mark.asyncio
async def test_legifrance_connector_search_maps_results() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth.test":
            return _oauth_handler(request)
        assert request.url.path == "/search"
        assert request.headers["authorization"] == "Bearer tok"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "civ-1240",
                        "titre": "Code civil, article 1240",
                        "extracts": [{"values": ["Tout fait quelconque..."]}],
                        "nature": "CODE",
                        "date": "2020-01-01",
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    token_provider = PisteOAuthTokenProvider(
        client, token_url="https://oauth.test/token", client_id="id", client_secret="secret"
    )
    connector = LegifranceConnector(client, token_provider, base_url="https://legifrance.test")

    results = await connector.search("dommage")

    assert len(results) == 1
    assert results[0].id == "civ-1240"
    assert results[0].connector == "codes"
    assert "Tout fait" in results[0].content


@pytest.mark.asyncio
async def test_legifrance_connector_fetch_returns_none_on_404() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth.test":
            return _oauth_handler(request)
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    token_provider = PisteOAuthTokenProvider(
        client, token_url="https://oauth.test/token", client_id="id", client_secret="secret"
    )
    connector = LegifranceConnector(client, token_provider, base_url="https://legifrance.test")

    assert await connector.fetch("does-not-exist") is None


@pytest.mark.asyncio
async def test_legifrance_connector_wraps_server_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth.test":
            return _oauth_handler(request)
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    token_provider = PisteOAuthTokenProvider(
        client, token_url="https://oauth.test/token", client_id="id", client_secret="secret"
    )
    connector = LegifranceConnector(client, token_provider, base_url="https://legifrance.test")

    with pytest.raises(ConnectorError):
        await connector.search("dommage")


@pytest.mark.asyncio
async def test_judilibre_connector_search_maps_results() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth.test":
            return _oauth_handler(request)
        assert request.url.path == "/search"
        assert request.url.params["query"] == "responsabilité"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "cass-civ1-2019-01",
                        "numero": "Cass. civ. 1re, 12 janvier 2019",
                        "summary": "Décision de principe.",
                        "jurisdiction": "Cour de cassation",
                        "chamber": "civile 1",
                        "decision_date": "2019-01-12",
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    token_provider = PisteOAuthTokenProvider(
        client, token_url="https://oauth.test/token", client_id="id", client_secret="secret"
    )
    connector = JudilibreConnector(client, token_provider, base_url="https://judilibre.test")

    results = await connector.search("responsabilité")

    assert len(results) == 1
    assert results[0].id == "cass-civ1-2019-01"
    assert results[0].connector == "jurisprudence"
    assert results[0].metadata["jurisdiction"] == "Cour de cassation"


@pytest.mark.asyncio
async def test_judilibre_connector_fetch_returns_none_on_404() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth.test":
            return _oauth_handler(request)
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    token_provider = PisteOAuthTokenProvider(
        client, token_url="https://oauth.test/token", client_id="id", client_secret="secret"
    )
    connector = JudilibreConnector(client, token_provider, base_url="https://judilibre.test")

    assert await connector.fetch("does-not-exist") is None
