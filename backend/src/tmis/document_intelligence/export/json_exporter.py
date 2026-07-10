import dataclasses
import json
from enum import Enum
from typing import Any

from tmis.document_intelligence.schemas.record import DocumentRecord


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, bytes):
        return f"<{len(value)} bytes>"
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _to_jsonable(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }
    if isinstance(value, list | tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


class JsonExporter:
    """Implements `ExportPort` as pretty-printed JSON.

    `raw_bytes` is never included in the export (only its length) — the
    export is meant for readable debugging/API consumption, not as a
    second copy of document storage (see
    docs/14-document-intelligence.md).
    """

    def export(self, record: DocumentRecord) -> str:
        return json.dumps(_to_jsonable(record), ensure_ascii=False, indent=2)
