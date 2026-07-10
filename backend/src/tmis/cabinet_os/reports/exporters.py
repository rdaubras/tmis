import csv
import io
from html import escape

from tmis.cabinet_os.reports.schemas import ReportFormat, ReportResult, ReportTable
from tmis.cabinet_os.reports.xlsx_writer import build_minimal_xlsx
from tmis.legal_drafting.export.pdf_writer import build_minimal_pdf


class CsvReportExporter:
    """Implements `ReportExporterPort` for CSV."""

    def export(self, table: ReportTable) -> ReportResult:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(table.headers)
        writer.writerows(table.rows)
        return ReportResult(
            format=ReportFormat.CSV,
            filename=f"{table.title}.csv",
            content=buffer.getvalue().encode("utf-8"),
            media_type="text/csv",
        )


class HtmlReportExporter:
    """Implements `ReportExporterPort` for a self-contained HTML table."""

    def export(self, table: ReportTable) -> ReportResult:
        header_cells = "".join(f"<th>{escape(h)}</th>" for h in table.headers)
        body_rows = "".join(
            "<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>"
            for row in table.rows
        )
        html = (
            f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{escape(table.title)}</title></head><body>"
            f"<h1>{escape(table.title)}</h1>"
            f"<table border='1'><thead><tr>{header_cells}</tr></thead>"
            f"<tbody>{body_rows}</tbody></table></body></html>"
        )
        return ReportResult(
            format=ReportFormat.HTML,
            filename=f"{table.title}.html",
            content=html.encode("utf-8"),
            media_type="text/html",
        )


class PdfReportExporter:
    """Implements `ReportExporterPort` via the hand-rolled minimal PDF
    writer already built for `tmis.legal_drafting.export` — reused
    as-is rather than duplicated (see docs/43-guide-rapports.md)."""

    def export(self, table: ReportTable) -> ReportResult:
        lines = [table.title, "", " | ".join(table.headers)]
        lines.extend(" | ".join(str(cell) for cell in row) for row in table.rows)
        content = build_minimal_pdf(lines)
        return ReportResult(
            format=ReportFormat.PDF,
            filename=f"{table.title}.pdf",
            content=content,
            media_type="application/pdf",
        )


class ExcelReportExporter:
    """Implements `ReportExporterPort` via the hand-rolled minimal XLSX
    writer (see `xlsx_writer.py`)."""

    def export(self, table: ReportTable) -> ReportResult:
        content = build_minimal_xlsx(table.headers, table.rows)
        return ReportResult(
            format=ReportFormat.EXCEL,
            filename=f"{table.title}.xlsx",
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
