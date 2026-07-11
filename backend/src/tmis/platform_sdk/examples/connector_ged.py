"""The sprint's "Connecteur GED" example plugin — demonstrates
`tmis.platform_sdk.connector_sdk`'s pagination/cache/normalization on
a fictional, in-memory "gestion électronique de documents" source."""

from tmis.platform_sdk.connector_sdk.base import BaseConnectorPlugin
from tmis.platform_sdk.connector_sdk.schemas import ConnectorPage

PLUGIN_ID = "connector-ged"

_PAGE_SIZE = 2
_FAKE_GED_DOCUMENTS = (
    {"doc_id": "ged-1", "titre": "Contrat de bail commercial", "type": "contrat"},
    {"doc_id": "ged-2", "titre": "Statuts SASU Exemplia", "type": "statuts"},
    {"doc_id": "ged-3", "titre": "Avenant contrat de travail", "type": "contrat"},
    {"doc_id": "ged-4", "titre": "Procès-verbal AG 2025", "type": "pv"},
)


class ConnectorGedPlugin(BaseConnectorPlugin):
    def __init__(self) -> None:
        super().__init__(plugin_id=PLUGIN_ID)

    async def fetch_page(self, query: str, page: int) -> ConnectorPage:
        matches = [d for d in _FAKE_GED_DOCUMENTS if query.lower() in d["titre"].lower()]
        start = (page - 1) * _PAGE_SIZE
        end = start + _PAGE_SIZE
        page_items = matches[start:end]
        return ConnectorPage(items=tuple(page_items), has_next=end < len(matches))

    def normalize(self, item: dict[str, object]) -> dict[str, object]:
        return {"id": item["doc_id"], "title": item["titre"], "category": item["type"]}
