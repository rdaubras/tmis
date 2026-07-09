from tmis.ai.connectors._fixture_search import search_fixture
from tmis.ai.connectors.exceptions import ConnectorAuthenticationError
from tmis.ai.schemas.connector import ConnectorDocument

_FIXTURE: list[ConnectorDocument] = [
    ConnectorDocument(
        id="civ-1240",
        title="Code civil, article 1240",
        content=(
            "Tout fait quelconque de l'homme, qui cause à autrui un dommage, "
            "oblige celui par la faute duquel il est arrivé à le réparer."
        ),
        connector="codes",
        metadata={"code": "civil", "article": "1240"},
    ),
    ConnectorDocument(
        id="trav-l1231-1",
        title="Code du travail, article L1231-1",
        content=(
            "Le contrat de travail à durée indéterminée peut être rompu à "
            "l'initiative de l'employeur ou du salarié."
        ),
        connector="codes",
        metadata={"code": "travail", "article": "L1231-1"},
    ),
]


class CodesConnector:
    """Implements `ConnectorPort` for legal codes and statutory texts.

    Sprint 2 scope: a tiny in-memory fixture stands in for the real
    connector (see docs/09-roadmap-30-sprints.md, Sprint 8) so the
    Connector Manager and the Kernel can be exercised end-to-end without
    reaching any external service.
    """

    connector_name = "codes"

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
