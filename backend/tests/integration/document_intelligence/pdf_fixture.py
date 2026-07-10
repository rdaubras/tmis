# Intentionally duplicated verbatim in
# tests/integration/document_intelligence/pdf_fixture.py: with no
# __init__.py in the test tree, pytest's rootless import mode requires
# every test module basename to be unique process-wide, so a helper used
# from two test directories is simplest kept local to each rather than
# imported across a `tests.*` package path.
import io


def build_minimal_pdf(text: str) -> bytes:
    """Hand-builds a minimal, well-formed single-page PDF with `text` as
    its content stream — avoids depending on a PDF-writing library (only
    `pypdf`, a reader/manipulator, is a project dependency)."""
    content_stream = f"BT /F1 24 Tf 100 700 Td ({text}) Tj ET".encode()
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>"
        b"/MediaBox[0 0 612 792]/Contents 5 0 R>>",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
        b"<</Length " + str(len(content_stream)).encode() + b">>\nstream\n"
        + content_stream
        + b"\nendstream",
    ]

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{index} 0 obj".encode() + obj + b"endobj\n")

    xref_offset = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.write(f"{offset:010d} 00000 n \n".encode())
    out.write(b"trailer\n")
    out.write(f"<</Size {len(objects) + 1}/Root 1 0 R>>\n".encode())
    out.write(b"startxref\n")
    out.write(f"{xref_offset}\n".encode())
    out.write(b"%%EOF")
    return out.getvalue()
