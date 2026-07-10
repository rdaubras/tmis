from typing import Protocol

from tmis.cabinet_os.administration.schemas import (
    ConnectorStatus,
    FirmRecord,
    FirmStatus,
    GlobalConfigEntry,
    MonitoringSnapshot,
)


class FirmRegistryPort(Protocol):
    def get(self, firm_id: str) -> FirmRecord | None: ...

    def save(self, firm: FirmRecord) -> None: ...

    def list_all(self) -> list[FirmRecord]: ...


class ConnectorRegistryPort(Protocol):
    def save(self, connector: ConnectorStatus) -> None: ...

    def list_all(self) -> list[ConnectorStatus]: ...


class GlobalConfigPort(Protocol):
    def get(self, key: str) -> GlobalConfigEntry | None: ...

    def save(self, entry: GlobalConfigEntry) -> None: ...

    def list_all(self) -> list[GlobalConfigEntry]: ...


class MonitoringPort(Protocol):
    """Extension point for a real metrics exporter — see
    docs/45-guide-administration.md."""

    def snapshot(self) -> MonitoringSnapshot: ...


class AdministrationEnginePort(Protocol):
    """Port implemented by every interchangeable administration
    engine."""

    def register_firm(self, name: str) -> FirmRecord: ...

    def set_firm_status(self, firm_id: str, status: FirmStatus) -> FirmRecord: ...

    def list_firms(self) -> list[FirmRecord]: ...

    def register_connector(self, name: str, connector_type: str) -> ConnectorStatus: ...

    def set_connector_enabled(self, name: str, enabled: bool) -> ConnectorStatus: ...

    def list_connectors(self) -> list[ConnectorStatus]: ...

    def set_global_config(self, key: str, value: str) -> GlobalConfigEntry: ...

    def get_global_config(self, key: str, default: str | None = None) -> str | None: ...

    def monitoring_snapshot(self) -> MonitoringSnapshot: ...
