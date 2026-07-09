from tmis.ai.connectors._fixture_search import search_fixture
from tmis.ai.connectors.exceptions import ConnectorAuthenticationError
from tmis.ai.schemas.connector import ConnectorDocument

_FIXTURE: list[ConnectorDocument] = [
    ConnectorDocument(
        id="doctrine-resp-civile-2020",
        title="Chronique de responsabilité civile",
        content=(
            "Analyse doctrinale des évolutions récentes de la responsabilité "
            "civile délictuelle."
        ),
        connector="doctrine",
        metadata={"year": "2020"},
    ),
]


class DoctrineConnector:
    """Implements `ConnectorPort` for legal doctrine and commentary.

    Sprint 2 scope: a tiny in-memory fixture (see `CodesConnector` for the
    rationale); real wiring lands in a future sprint.
    """

    connector_name = "doctrine"

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
