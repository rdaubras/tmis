"""A minimal, dependency-free single-sheet XLSX byte writer.

TMIS has no Excel-authoring dependency (only `pypdf`/`python-docx` for
PDF/DOCX). Rather than add one for a mock-scope report export, this
writes the smallest valid OOXML spreadsheet package by hand — one
workbook, one worksheet, inline strings (no `sharedStrings.xml`) — the
same "hand-rolled, no new dependency" choice already made for PDF in
`tmis.legal_drafting.export.pdf_writer` (see docs/43-guide-rapports.md).
"""

# ruff: noqa: E501 — the OOXML template constants below are fixed XML
# content; wrapping them would only add fragile string concatenation.

import io
import zipfile
from xml.sax.saxutils import escape, quoteattr

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""

_ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

_WORKBOOK = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""

_WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

_COLUMN_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _column_ref(index: int) -> str:
    letters = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = _COLUMN_LETTERS[remainder] + letters
    return letters


def _cell_xml(column: int, row: int, value: str) -> str:
    ref = f"{_column_ref(column)}{row}"
    try:
        float(value)
    except ValueError:
        return f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
    return f'<c r="{ref}"><v>{escape(value)}</v></c>'


def build_minimal_xlsx(headers: list[str], rows: list[list[str]]) -> bytes:
    all_rows = [headers, *rows]
    row_xml = []
    for row_index, row in enumerate(all_rows, start=1):
        cells = "".join(_cell_xml(col, row_index, str(value)) for col, value in enumerate(row))
        row_xml.append(f'<row r="{row_index}">{cells}</row>')
    dimension = f"A1:{_column_ref(max(len(r) for r in all_rows) - 1)}{len(all_rows)}"
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<dimension ref={quoteattr(dimension)}/>"
        f"<sheetData>{''.join(row_xml)}</sheetData>"
        "</worksheet>"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _CONTENT_TYPES)
        archive.writestr("_rels/.rels", _ROOT_RELS)
        archive.writestr("xl/workbook.xml", _WORKBOOK)
        archive.writestr("xl/_rels/workbook.xml.rels", _WORKBOOK_RELS)
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return buffer.getvalue()
