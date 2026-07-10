from datetime import UTC, datetime

from tmis.cabinet_os.administration.schemas import MonitoringSnapshot


class StaticMonitoringAdapter:
    """Implements `MonitoringPort` as a stub (see
    docs/45-guide-administration.md): reports a fixed, zeroed snapshot
    rather than fake numbers, until a real exporter (Prometheus/
    OpenTelemetry) is wired in — see Sprint 28 "Observabilité
    complète"."""

    def snapshot(self) -> MonitoringSnapshot:
        return MonitoringSnapshot(
            cpu_percent=0.0,
            memory_percent=0.0,
            request_latency_ms_p50=0.0,
            request_latency_ms_p95=0.0,
            error_rate=0.0,
            computed_at=datetime.now(UTC),
        )
