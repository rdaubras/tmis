from tmis.cabinet_os.reports.exporters import (
    CsvReportExporter,
    ExcelReportExporter,
    HtmlReportExporter,
    PdfReportExporter,
)
from tmis.cabinet_os.reports.ports import ReportExporterPort
from tmis.cabinet_os.reports.schemas import ReportFormat, ReportResult, ReportTable

_DEFAULT_EXPORTERS: dict[ReportFormat, ReportExporterPort] = {
    ReportFormat.PDF: PdfReportExporter(),
    ReportFormat.EXCEL: ExcelReportExporter(),
    ReportFormat.CSV: CsvReportExporter(),
    ReportFormat.HTML: HtmlReportExporter(),
}


class ReportEngine:
    """Implements `ReportEnginePort`: extensible over formats — register
    a new `ReportExporterPort` for a `ReportFormat` (or an entirely new
    format value) without touching this class (see
    docs/43-guide-rapports.md)."""

    def __init__(self, exporters: dict[ReportFormat, ReportExporterPort] | None = None) -> None:
        self._exporters: dict[ReportFormat, ReportExporterPort] = (
            exporters if exporters is not None else dict(_DEFAULT_EXPORTERS)
        )

    def generate(self, table: ReportTable, report_format: ReportFormat) -> ReportResult:
        exporter = self._exporters.get(report_format)
        if exporter is None:
            raise ValueError(f"No exporter registered for format {report_format!r}")
        return exporter.export(table)
