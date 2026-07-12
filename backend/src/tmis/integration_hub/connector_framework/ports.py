from typing import Protocol

from tmis.integration_hub.connector_framework.schemas import (
    ConnectorCapability,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)


class ConnectorPort(Protocol):
    """The common interface every LIH connector implements —
    authentification, lecture, écriture, synchronisation, gestion des
    erreurs (sprint's minimal function list). Deliberately distinct
    from `platform_sdk.connector_sdk.BaseConnectorPlugin` (Sprint 13),
    which is a **search-only** plugin bound to the Plugin System's
    `PluginContext`/pagination/cache — this port supports full
    CRUD-style read/write/sync against an external system, tenant by
    tenant, gated by `authentication`/`security`, never through the
    Plugin System. Same architectural role ("a connector"), two
    distinct scopes — documented, not merged."""

    connector_type: ConnectorType
    capabilities: frozenset[ConnectorCapability]

    async def authenticate(self, config: dict[str, str]) -> bool: ...

    async def read(
        self, config: dict[str, str], since: str | None = None
    ) -> list[ConnectorRecord]: ...

    async def write(
        self, config: dict[str, str], record: ConnectorRecord
    ) -> ConnectorWriteResult: ...


class ConnectorMetricsRecorderPort(Protocol):
    """Narrow contract `ConnectorInvoker` depends on instead of
    importing `monitoring.engine` directly — decoupled-input
    convention, keeps this module free of a forward dependency."""

    def record(
        self,
        connector_id: str,
        firm_id: str,
        operation: str,
        *,
        success: bool,
        duration_ms: float,
        record_count: int = 0,
        error: str | None = None,
    ) -> None: ...
