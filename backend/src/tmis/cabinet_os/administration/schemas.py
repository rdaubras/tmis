from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class FirmStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"


@dataclass(slots=True)
class FirmRecord:
    """A minimal platform-level record of a firm/cabinet — just enough
    for the administration portal to list, suspend and reactivate
    tenants (see docs/45-guide-administration.md). The fuller `Firm`
    aggregate (billing address, legal entity details, branding...)
    belongs to the future Identity & Firm sprint; this is not it."""

    id: str
    name: str
    status: FirmStatus = FirmStatus.TRIAL
    created_at: datetime | None = None


@dataclass(slots=True)
class ConnectorStatus:
    """An admin-visible entry in the connector catalog — metadata only:
    the actual connector implementations live in their own engines
    (e.g. `tmis.legal_research.connectors`); this just tracks which
    ones are known and enabled platform-wide."""

    name: str
    connector_type: str
    enabled: bool = True
    configured_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class GlobalConfigEntry:
    """A platform-wide configuration value — visible to every firm,
    distinct from `tmis.cabinet_os.settings` (per-firm settings)."""

    key: str
    value: str
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class MonitoringSnapshot:
    """A point-in-time platform health snapshot. Architecture only this
    sprint (see docs/39-cabinet-os.md — Portée du Sprint 9): real
    values come from a future exporter (Prometheus/OpenTelemetry,
    Sprint 28 Observabilité complète)."""

    cpu_percent: float
    memory_percent: float
    request_latency_ms_p50: float
    request_latency_ms_p95: float
    error_rate: float
    computed_at: datetime
