from dataclasses import dataclass
from enum import StrEnum


class ExportFormat(StrEnum):
    CSV = "csv"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class ExportResult:
    format: ExportFormat
    filename: str
    content: bytes
    media_type: str
