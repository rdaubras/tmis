from tmis.domain.shared.ports import LegalDocument


class CodesConnector:
    """Implements `LegalSourceConnectorPort` for legal codes and statutory texts."""

    connector_name = "codes"

    async def search(
        self, query: str, filters: dict[str, object] | None = None
    ) -> list[LegalDocument]:
        raise NotImplementedError("Codes connector wiring is scheduled for a future sprint.")

    async def fetch(self, document_id: str) -> LegalDocument | None:
        raise NotImplementedError("Codes connector wiring is scheduled for a future sprint.")
