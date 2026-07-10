import zipfile
from io import BytesIO

import pytest

from tmis.cabinet_os.reports.engine import ReportEngine
from tmis.cabinet_os.reports.schemas import ReportFormat, ReportTable
from tmis.cabinet_os.settings.engine import SettingsEngine
from tmis.cabinet_os.settings.schemas import SettingsCategory
from tmis.cabinet_os.settings.store import InMemorySettingsStore

_TABLE = ReportTable(
    title="Revenue", headers=["Client", "Amount"], rows=[["Acme", "100"], ["Beta", "250.5"]]
)


def test_csv_export_contains_headers_and_rows() -> None:
    engine = ReportEngine()
    result = engine.generate(_TABLE, ReportFormat.CSV)

    text = result.content.decode("utf-8")
    assert "Client,Amount" in text
    assert "Acme,100" in text


def test_html_export_escapes_and_wraps_a_table() -> None:
    engine = ReportEngine()
    result = engine.generate(_TABLE, ReportFormat.HTML)

    html = result.content.decode("utf-8")
    assert "<table" in html
    assert "Acme" in html


def test_pdf_export_produces_a_valid_pdf_header() -> None:
    engine = ReportEngine()
    result = engine.generate(_TABLE, ReportFormat.PDF)

    assert result.content.startswith(b"%PDF-1.4")
    assert result.media_type == "application/pdf"


def test_excel_export_produces_a_valid_zip_package() -> None:
    engine = ReportEngine()
    result = engine.generate(_TABLE, ReportFormat.EXCEL)

    archive = zipfile.ZipFile(BytesIO(result.content))
    assert "xl/worksheets/sheet1.xml" in archive.namelist()
    sheet_xml = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "Acme" in sheet_xml


def test_unknown_format_raises() -> None:
    engine = ReportEngine(exporters={})
    with pytest.raises(ValueError, match="No exporter registered"):
        engine.generate(_TABLE, ReportFormat.PDF)


def test_settings_get_returns_default_when_unset() -> None:
    engine = SettingsEngine(InMemorySettingsStore())

    value = engine.get("firm-1", SettingsCategory.AI, "default_model", default="gpt")

    assert value == "gpt"


def test_settings_set_then_get_returns_the_value() -> None:
    engine = SettingsEngine(InMemorySettingsStore())

    engine.set("firm-1", SettingsCategory.NOTIFICATIONS, "channel", "email")

    assert engine.get("firm-1", SettingsCategory.NOTIFICATIONS, "channel") == "email"


def test_settings_are_scoped_per_firm_and_category() -> None:
    engine = SettingsEngine(InMemorySettingsStore())
    engine.set("firm-1", SettingsCategory.SECURITY, "mfa_required", "true")
    engine.set("firm-2", SettingsCategory.SECURITY, "mfa_required", "false")

    assert engine.get("firm-1", SettingsCategory.SECURITY, "mfa_required") == "true"
    assert engine.get("firm-2", SettingsCategory.SECURITY, "mfa_required") == "false"


def test_list_category_returns_only_that_categorys_entries() -> None:
    engine = SettingsEngine(InMemorySettingsStore())
    engine.set("firm-1", SettingsCategory.BILLING, "currency", "EUR")
    engine.set("firm-1", SettingsCategory.AI, "default_model", "gpt")

    billing_entries = engine.list_category("firm-1", SettingsCategory.BILLING)

    assert len(billing_entries) == 1
    assert billing_entries[0].key == "currency"


def test_list_all_returns_every_category() -> None:
    engine = SettingsEngine(InMemorySettingsStore())
    engine.set("firm-1", SettingsCategory.BILLING, "currency", "EUR")
    engine.set("firm-1", SettingsCategory.AI, "default_model", "gpt")

    assert len(engine.list_all("firm-1")) == 2
