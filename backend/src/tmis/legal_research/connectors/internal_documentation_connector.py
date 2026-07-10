from tmis.ai.connectors._fixture_search import search_fixture
from tmis.ai.connectors.exceptions import ConnectorAuthenticationError
from tmis.ai.schemas.connector import ConnectorDocument

_FIXTURE: list[ConnectorDocument] = [
    ConnectorDocument(
        id="cabinet-note-2023-014",
        title="Note interne — clause de non-concurrence",
        content=(
            "Note du cabinet rappelant les critères de validité d'une clause "
            "de non-concurrence en droit du travail français : limitation "
            "dans le temps, l'espace, l'activité, et contrepartie financière."
        ),
        connector="internal_documentation",
        metadata={"category": "note_interne", "year": "2023"},
    ),
    ConnectorDocument(
        id="cabinet-memo-2022-007",
        title="Mémo — clauses résolutoires en matière de bail commercial",
        content=(
            "Mémorandum interne sur la mise en œuvre d'une clause résolutoire "
            "de bail commercial et le formalisme du commandement de payer."
        ),
        connector="internal_documentation",
        metadata={"category": "memo", "year": "2022"},
    ),
]


class InternalDocumentationConnector:
    """Implements `ConnectorPort` for the cabinet's own internal
    documentation (notes, memos, precedent drafts).

    Sprint 5 scope: a tiny in-memory fixture stands in for the firm's
    real document base (see docs/21-legal-research.md); wiring an actual
    internal search index is future work, behind the same port.
    """

    connector_name = "internal_documentation"

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
