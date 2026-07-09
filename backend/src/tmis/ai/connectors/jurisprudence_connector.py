from tmis.ai.connectors._fixture_search import search_fixture
from tmis.ai.connectors.exceptions import ConnectorAuthenticationError
from tmis.ai.schemas.connector import ConnectorDocument

_FIXTURE: list[ConnectorDocument] = [
    ConnectorDocument(
        id="cass-civ1-2019-01",
        title="Cass. civ. 1re, 12 janvier 2019",
        content="Décision de principe sur la responsabilité contractuelle en cas d'inexécution.",
        connector="jurisprudence",
        metadata={"jurisdiction": "Cour de cassation", "chamber": "civile 1"},
    ),
]


class JurisprudenceConnector:
    """Implements `ConnectorPort` for case-law databases.

    Sprint 2 scope: a tiny in-memory fixture (see `CodesConnector` for the
    rationale); real wiring lands in Sprint 16.
    """

    connector_name = "jurisprudence"

    def __init__(self, api_key: str | None = "demo-key") -> None:
        self._api_key = api_key

    def _require_auth(self) -> None:
        if not self._api_key:
            raise ConnectorAuthenticationError(self.connector_name, "missing API key")

    async def search(
        self, query: str, filters: dict[str, object] | None = None
    ) -> list[ConnectorDocument]:
        self._require_auth()
        return search_fixture(query, _FIXTURE)

    async def fetch(self, document_id: str) -> ConnectorDocument | None:
        self._require_auth()
        return next((doc for doc in _FIXTURE if doc.id == document_id), None)
