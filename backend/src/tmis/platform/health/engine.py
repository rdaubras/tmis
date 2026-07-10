from tmis.platform.health.ports import HealthCheckPort
from tmis.platform.health.schemas import ComponentHealth, HealthStatus, SystemHealth


class HealthCheckEngine:
    """Implements `HealthCheckEnginePort` (see
    docs/49-guide-supervision.md — Health Checks).

    `liveness()` never probes a dependency — per Kubernetes
    conventions, a liveness probe should only ask "is this process
    alive and not deadlocked", never "can it reach the database"
    (that would make Kubernetes restart every pod during a database
    outage, turning one incident into an avoidable cascade).
    `readiness()` runs every registered check and aggregates: any
    `DOWN` makes the whole system `DOWN`; otherwise any `DEGRADED`
    makes it `DEGRADED`; otherwise `UP`.
    """

    def __init__(self) -> None:
        self._checks: list[HealthCheckPort] = []

    def register(self, check: HealthCheckPort) -> None:
        self._checks.append(check)

    def liveness(self) -> SystemHealth:
        return SystemHealth(status=HealthStatus.UP, components=[])

    def readiness(self) -> SystemHealth:
        components: list[ComponentHealth] = [check.check() for check in self._checks]
        status = HealthStatus.UP
        if any(c.status is HealthStatus.DOWN for c in components):
            status = HealthStatus.DOWN
        elif any(c.status is HealthStatus.DEGRADED for c in components):
            status = HealthStatus.DEGRADED
        return SystemHealth(status=status, components=components)
