import time

from tmis.ai.connectors.factory import (
    codes_connector_status,
    doctrine_connector_status,
    jurisprudence_connector_status,
)
from tmis.legal_research.connectors.factory import (
    internal_documentation_connector_status,
    private_database_connector_status,
)
from tmis.platform.health.schemas import ComponentHealth, HealthStatus


class ConnectorBackendHealthCheck:
    """Implements `HealthCheckPort`: surfaces which connectors are running
    on their Sprint 2/5 in-memory fixture for lack of configuration,
    instead of only logging it once at startup (see
    docs/154-guide-configuration-connecteurs.md — "signaler clairement au
    démarrage (log + health check)").

    A connector on its fixture is fully functional, just not backed by
    real data, so this reports DEGRADED rather than DOWN — the same
    convention `HealthCheckEngine.readiness()` already uses to distinguish
    "impaired" from "broken".
    """

    name = "connector_backends"

    def check(self) -> ComponentHealth:
        start = time.perf_counter()
        statuses = {
            "codes": codes_connector_status(),
            "jurisprudence": jurisprudence_connector_status(),
            "doctrine": doctrine_connector_status(),
            "internal_documentation": internal_documentation_connector_status(),
            "private_database": private_database_connector_status(),
        }
        latency_ms = (time.perf_counter() - start) * 1000

        on_fixture = [name for name, (configured, _) in statuses.items() if not configured]
        if not on_fixture:
            return ComponentHealth(name=self.name, status=HealthStatus.UP, latency_ms=latency_ms)

        detail = "; ".join(f"{name}: {statuses[name][1]}" for name in on_fixture)
        return ComponentHealth(
            name=self.name, status=HealthStatus.DEGRADED, detail=detail, latency_ms=latency_ms
        )
