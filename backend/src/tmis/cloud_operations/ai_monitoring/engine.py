from collections.abc import Callable

from tmis.ai_fabric.telemetry.engine import TelemetryDashboard
from tmis.ai_fabric.telemetry.schemas import FabricTelemetry
from tmis.ai_governance.bias_detection.engine import BiasDetectionEngine
from tmis.ai_governance.hallucination_detection.engine import HallucinationDetectionEngine
from tmis.cloud_operations.ai_monitoring.ports import AIQualityIncidentStorePort
from tmis.cloud_operations.ai_monitoring.schemas import (
    AIQualityIncident,
    AIQualityIssueKind,
    new_ai_quality_incident_id,
)
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory


class AIMonitoringEngine:
    """The sprint's specialized AI monitoring surface: coût par
    modèle/latence/qualité/taux de fallback compose `ai_fabric.
    telemetry.TelemetryDashboard` (Sprint 14) directly rather than a
    second cost/latency ledger — `cloud_operations.dashboards.
    DashboardsEngine.ai_dashboard` already exposes the same
    `FabricTelemetry` for the general dashboards use case; this
    engine adds the one genuinely new piece: historizing hallucination/
    bias findings from `ai_governance.hallucination_detection`/
    `.bias_detection` (Sprint 15), which only ever return an in-memory
    list for a single scan."""

    def __init__(
        self,
        hallucination: HallucinationDetectionEngine,
        bias: BiasDetectionEngine,
        store: AIQualityIncidentStorePort,
        metrics: MetricsEngine,
        telemetry_dashboard_factory: Callable[[str], TelemetryDashboard],
    ) -> None:
        self._hallucination = hallucination
        self._bias = bias
        self._store = store
        self._metrics = metrics
        self._telemetry_dashboard_factory = telemetry_dashboard_factory

    def scan_and_record(self, text: str, firm_id: str | None = None) -> list[AIQualityIncident]:
        incidents: list[AIQualityIncident] = []
        for alert in self._hallucination.scan(text):
            incidents.append(
                AIQualityIncident(
                    id=new_ai_quality_incident_id(),
                    kind=AIQualityIssueKind.HALLUCINATION,
                    excerpt=alert.excerpt,
                    detail=alert.reason,
                    firm_id=firm_id,
                )
            )
        for finding in self._bias.scan(text):
            incidents.append(
                AIQualityIncident(
                    id=new_ai_quality_incident_id(),
                    kind=AIQualityIssueKind.BIAS,
                    excerpt=finding.excerpt,
                    detail=finding.description,
                    firm_id=firm_id,
                )
            )
        for incident in incidents:
            self._store.save(incident)
            self._metrics.record(
                MetricCategory.ERRORS, f"ai_quality.{incident.kind.value}", 1.0, firm_id=firm_id
            )
        return incidents

    def recent_incidents(self, limit: int = 50) -> list[AIQualityIncident]:
        return self._store.list_recent(limit)

    def model_snapshot(self, firm_id: str) -> FabricTelemetry:
        return self._telemetry_dashboard_factory(firm_id).snapshot()
