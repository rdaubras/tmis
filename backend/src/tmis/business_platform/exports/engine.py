import json

from tmis.business_platform.exports.schemas import ExportFormat, ExportResult
from tmis.business_platform.reports.schemas import BusinessReport
from tmis.business_platform.usage.schemas import UsageSnapshot
from tmis.cabinet_os.reports.exporters import CsvReportExporter
from tmis.cabinet_os.reports.schemas import ReportTable


class ExportEngine:
    """CSV/JSON export for usage, billing and analytics data — reuses
    `cabinet_os.reports.exporters.CsvReportExporter` (Sprint 9) for
    the CSV path rather than re-implementing CSV writing; JSON export
    has no equivalent in `cabinet_os.reports` (it only offers
    CSV/HTML/PDF/Excel) so it is built fresh here."""

    def __init__(self) -> None:
        self._csv_exporter = CsvReportExporter()

    def export_table(self, table: ReportTable, export_format: ExportFormat) -> ExportResult:
        if export_format is ExportFormat.CSV:
            csv_result = self._csv_exporter.export(table)
            return ExportResult(
                format=ExportFormat.CSV,
                filename=csv_result.filename,
                content=csv_result.content,
                media_type=csv_result.media_type,
            )
        payload = {
            "title": table.title,
            "headers": table.headers,
            "rows": table.rows,
        }
        return ExportResult(
            format=ExportFormat.JSON,
            filename=f"{table.title}.json",
            content=json.dumps(payload, indent=2).encode("utf-8"),
            media_type="application/json",
        )

    def export_usage(
        self, firm_id: str, usage: list[UsageSnapshot], export_format: ExportFormat
    ) -> ExportResult:
        table = ReportTable(
            title=f"usage-{firm_id}",
            headers=["dimension", "used", "limit", "percent_used"],
            rows=[
                [
                    snapshot.dimension.value,
                    str(snapshot.used),
                    "" if snapshot.limit is None else str(snapshot.limit),
                    "" if snapshot.percent_used is None else f"{snapshot.percent_used:.2f}",
                ]
                for snapshot in usage
            ],
        )
        return self.export_table(table, export_format)

    def export_report(self, report: BusinessReport, export_format: ExportFormat) -> ExportResult:
        table = ReportTable(
            title=f"report-{report.id}",
            headers=["section", "value"],
            rows=[[key, value] for key, value in report.sections.items()],
        )
        return self.export_table(table, export_format)
