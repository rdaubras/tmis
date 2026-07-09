from tmis.domain.shared.ports import LegalDocument


class DoctrineConnector:
    """Implements `LegalSourceConnectorPort` for legal doctrine and commentary."""

    connector_name = "doctrine"

    async def search(
        self, query: str, filters: dict[str, object] | None = None
    ) -> list[LegalDocument]:
        raise NotImplementedError("Doctrine connector wiring is scheduled for a future sprint.")

    async def fetch(self, document_id: str) -> LegalDocument | None:
        raise NotImplementedError("Doctrine connector wiring is scheduled for a future sprint.")
