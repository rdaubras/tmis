import uuid
from datetime import UTC, datetime

from tmis.cabinet_os.administration.ports import (
    ConnectorRegistryPort,
    FirmRegistryPort,
    GlobalConfigPort,
    MonitoringPort,
)
from tmis.cabinet_os.administration.schemas import (
    ConnectorStatus,
    FirmRecord,
    FirmStatus,
    GlobalConfigEntry,
    MonitoringSnapshot,
)


class AdministrationEngine:
    """Implements `AdministrationEnginePort` (see
    docs/45-guide-administration.md): firm/tenant management, connector
    catalog, global configuration and a monitoring snapshot. Firm
    subscriptions, member management and the audit trail are
    deliberately **not** reimplemented here — the admin portal composes
    `tmis.cabinet_os.subscriptions`, `tmis.collaboration.members` and
    `tmis.collaboration.audit` directly (see `bootstrap.py`) rather
    than duplicating them.
    """

    def __init__(
        self,
        firm_registry: FirmRegistryPort,
        connector_registry: ConnectorRegistryPort,
        global_config: GlobalConfigPort,
        monitoring: MonitoringPort,
    ) -> None:
        self._firms = firm_registry
        self._connectors = connector_registry
        self._config = global_config
        self._monitoring = monitoring

    def register_firm(self, name: str) -> FirmRecord:
        firm = FirmRecord(id=str(uuid.uuid4()), name=name, created_at=datetime.now(UTC))
        self._firms.save(firm)
        return firm

    def set_firm_status(self, firm_id: str, status: FirmStatus) -> FirmRecord:
        firm = self._firms.get(firm_id)
        if firm is None:
            raise ValueError(f"Unknown firm {firm_id!r}")
        firm.status = status
        self._firms.save(firm)
        return firm

    def list_firms(self) -> list[FirmRecord]:
        return self._firms.list_all()

    def register_connector(self, name: str, connector_type: str) -> ConnectorStatus:
        connector = ConnectorStatus(
            name=name, connector_type=connector_type, configured_at=datetime.now(UTC)
        )
        self._connectors.save(connector)
        return connector

    def set_connector_enabled(self, name: str, enabled: bool) -> ConnectorStatus:
        existing = next((c for c in self._connectors.list_all() if c.name == name), None)
        if existing is None:
            raise ValueError(f"Unknown connector {name!r}")
        existing.enabled = enabled
        self._connectors.save(existing)
        return existing

    def list_connectors(self) -> list[ConnectorStatus]:
        return self._connectors.list_all()

    def set_global_config(self, key: str, value: str) -> GlobalConfigEntry:
        entry = GlobalConfigEntry(key=key, value=value, updated_at=datetime.now(UTC))
        self._config.save(entry)
        return entry

    def get_global_config(self, key: str, default: str | None = None) -> str | None:
        entry = self._config.get(key)
        return entry.value if entry is not None else default

    def monitoring_snapshot(self) -> MonitoringSnapshot:
        return self._monitoring.snapshot()
