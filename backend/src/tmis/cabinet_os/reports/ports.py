from typing import Protocol

from tmis.cabinet_os.reports.schemas import ReportFormat, ReportResult, ReportTable


class ReportExporterPort(Protocol):
    """Port implemented by every interchangeable single-format
    exporter — adding a format means adding an exporter, never
    touching `ReportEngine` (see docs/43-guide-rapports.md)."""

    def export(self, table: ReportTable) -> ReportResult: ...


class ReportEnginePort(Protocol):
    """Port implemented by every interchangeable report engine."""

    def generate(self, table: ReportTable, report_format: ReportFormat) -> ReportResult: ...
