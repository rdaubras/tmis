from tmis.business_platform.exports.engine import ExportEngine as BusinessExportEngine
from tmis.business_platform.exports.schemas import ExportFormat, ExportResult
from tmis.cabinet_os.reports.schemas import ReportTable
from tmis.cloud_operations.incident_management.schemas import Incident
from tmis.cloud_operations.metrics.schemas import MetricEvent


class ObservabilityExportEngine:
    """CSV/JSON export for observability data — delegates the actual
    CSV/JSON branching to `business_platform.exports.ExportEngine.
    export_table` (Sprint 20) rather than a third reimplementation of
    that logic; this engine only shapes observability records into a
    generic `cabinet_os.reports.schemas.ReportTable`."""

    def __init__(self, export_engine: BusinessExportEngine) -> None:
        self._export_engine = export_engine

    def export_metrics(
        self, events: list[MetricEvent], export_format: ExportFormat
    ) -> ExportResult:
        table = ReportTable(
            title="metrics",
            headers=["category", "name", "value", "firm_id", "recorded_at"],
            rows=[
                [
                    e.category.value,
                    e.name,
                    str(e.value),
                    e.firm_id or "",
                    e.recorded_at.isoformat(),
                ]
                for e in events
            ],
        )
        return self._export_engine.export_table(table, export_format)

    def export_incidents(
        self, incidents: list[Incident], export_format: ExportFormat
    ) -> ExportResult:
        table = ReportTable(
            title="incidents",
            headers=["id", "title", "severity", "status", "firm_id", "opened_at"],
            rows=[
                [
                    i.id,
                    i.title,
                    i.severity.value,
                    i.status.value,
                    i.firm_id or "",
                    i.opened_at.isoformat(),
                ]
                for i in incidents
            ],
        )
        return self._export_engine.export_table(table, export_format)
