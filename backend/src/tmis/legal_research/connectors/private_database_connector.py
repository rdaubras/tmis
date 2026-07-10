from tmis.ai.connectors._fixture_search import search_fixture
from tmis.ai.connectors.exceptions import ConnectorAuthenticationError
from tmis.ai.schemas.connector import ConnectorDocument

_FIXTURE: list[ConnectorDocument] = [
    ConnectorDocument(
        id="private-db-arret-2021-4521",
        title="Cass. soc., 9 juin 2021, n° 19-24.354",
        content=(
            "Décision d'une base de jurisprudence privée sous licence : "
            "précision sur l'appréciation du caractère proportionné d'une "
            "clause de non-concurrence au regard de l'activité du salarié."
        ),
        connector="private_database",
        metadata={"jurisdiction": "Cass. soc.", "date": "2021-06-09"},
    ),
]


class PrivateDatabaseConnector:
    """Implements `ConnectorPort` for a licensed private jurisprudence/
    doctrine database the firm has contracted access to.

    Sprint 5 scope: a tiny in-memory fixture (see
    `InternalDocumentationConnector` for the rationale); real wiring to a
    licensed provider is future work, behind the same port.
    """

    connector_name = "private_database"

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
