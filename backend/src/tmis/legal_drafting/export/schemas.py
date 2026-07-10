from dataclasses import dataclass
from enum import Enum


class ExportFormat(str, Enum):
    DOCX = "docx"
    PDF = "pdf"
    HTML = "html"


@dataclass(frozen=True, slots=True)
class ExportResult:
    """The bytes of one exported draft, ready to be returned by the API
    (see docs/32-guide-exports.md). Every export preserves the section
    structure and the citations — never just a flattened wall of text.
    """

    format: ExportFormat
    filename: str
    content: bytes
    media_type: str
