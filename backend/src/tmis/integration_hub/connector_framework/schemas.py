from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ConnectorType(StrEnum):
    MESSAGING = "messaging"
    CALENDAR = "calendar"
    DOCUMENT_STORAGE = "document_storage"
    ESIGNATURE = "esignature"
    DMS = "dms"
    BILLING = "billing"
    CRM = "crm"
    OTHER = "other"


class ConnectorCapability(StrEnum):
    READ = "read"
    WRITE = "write"
    SYNC = "sync"


@dataclass(frozen=True, slots=True)
class ConnectorRecord:
    """One generic record read from or written to an external system —
    "aucune logique métier spécifique à un fournisseur" (sprint
    constraint): `data` is a plain string map, never a
    vendor-specific shape, normalized/mapped by `mapping`/
    `transformation` before it reaches any TMIS domain object."""

    external_id: str
    data: dict[str, str] = field(default_factory=dict)
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ConnectorWriteResult:
    success: bool
    external_id: str
    detail: str = ""


@dataclass(frozen=True, slots=True)
class ConnectorSyncResult:
    records_read: int = 0
    records_written: int = 0
    conflicts: int = 0
    errors: tuple[str, ...] = field(default_factory=tuple)
