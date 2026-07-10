from tmis.document_intelligence.schemas.document import IngestedDocument


class EmlParser:
    """Implements `DocumentParserPort` for `.eml` email files.

    Preparation only, per Sprint 3 scope (see
    docs/09-roadmap-30-sprints.md): the interface and registration slot
    exist so email ingestion can be wired in a future sprint without
    touching the `IngestionRegistry` or the pipeline.
    """

    content_types: tuple[str, ...] = ("message/rfc822",)

    def supports(self, content_type: str) -> bool:
        return content_type in self.content_types

    def parse(self, document_id: str, filename: str, raw_bytes: bytes) -> IngestedDocument:
        raise NotImplementedError(
            "EML ingestion is prepared but not implemented yet (see "
            "docs/09-roadmap-30-sprints.md)."
        )
