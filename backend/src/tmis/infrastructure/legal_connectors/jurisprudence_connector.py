from tmis.domain.shared.ports import LegalDocument


class JurisprudenceConnector:
    """Implements `LegalSourceConnectorPort` for case-law databases."""

    connector_name = "jurisprudence"

    async def search(
        self, query: str, filters: dict[str, object] | None = None
    ) -> list[LegalDocument]:
        raise NotImplementedError(
            "Jurisprudence connector wiring is scheduled for a future sprint."
        )

    async def fetch(self, document_id: str) -> LegalDocument | None:
        raise NotImplementedError(
            "Jurisprudence connector wiring is scheduled for a future sprint."
        )
