from tmis.document_intelligence.ingestion.docx_parser import DocxParser
from tmis.document_intelligence.ingestion.eml_parser import EmlParser
from tmis.document_intelligence.ingestion.exceptions import UnsupportedContentTypeError
from tmis.document_intelligence.ingestion.image_parser import ImageParser
from tmis.document_intelligence.ingestion.pdf_parser import PdfParser
from tmis.document_intelligence.ingestion.ports import DocumentParserPort
from tmis.document_intelligence.ingestion.txt_parser import TxtParser
from tmis.document_intelligence.schemas.document import IngestedDocument


class IngestionRegistry:
    """Dispatches a raw file to the parser that supports its content type.

    See docs/15-guide-nouveau-parser.md for how to register a new one.
    """

    def __init__(self, parsers: list[DocumentParserPort] | None = None) -> None:
        self._parsers: list[DocumentParserPort] = parsers or [
            PdfParser(),
            DocxParser(),
            TxtParser(),
            ImageParser(),
            EmlParser(),
        ]

    def register(self, parser: DocumentParserPort) -> None:
        self._parsers.append(parser)

    def parse(
        self, document_id: str, filename: str, content_type: str, raw_bytes: bytes
    ) -> IngestedDocument:
        for parser in self._parsers:
            if parser.supports(content_type):
                return parser.parse(document_id, filename, raw_bytes)
        raise UnsupportedContentTypeError(content_type)

    def supported_content_types(self) -> list[str]:
        return [ct for parser in self._parsers for ct in parser.content_types]
