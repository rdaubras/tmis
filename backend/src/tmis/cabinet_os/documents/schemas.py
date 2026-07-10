from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DocumentCategory(str, Enum):
    CONTRACT = "contract"
    CORRESPONDENCE = "correspondence"
    PLEADING = "pleading"
    EVIDENCE = "evidence"
    INVOICE = "invoice"
    IDENTITY = "identity"
    OTHER = "other"


@dataclass(slots=True)
class CabinetDocument:
    """A business-facing document record — which client/dossier a file
    belongs to, its storage pointer and category (see
    docs/39-cabinet-os.md — Documents). This is deliberately a thin
    registry, distinct from `tmis.document_intelligence`: the DIE
    *analyzes* document content (OCR, entities, chunking...), this
    module only tracks *ownership and categorization* for the business
    layer. `die_record_id` optionally links the two by id."""

    id: str
    firm_id: str
    client_id: str
    filename: str
    storage_ref: str
    category: DocumentCategory = DocumentCategory.OTHER
    case_id: str | None = None
    die_record_id: str | None = None
    uploaded_by: str = ""
    size_bytes: int = 0
    uploaded_at: datetime | None = None
