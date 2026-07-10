"""A minimal, dependency-free single/multi-page PDF byte writer.

TMIS already depends on `pypdf` (Sprint 3) for *reading* PDFs, but
nothing in the dependency set can *author* one from scratch (no
`reportlab`/`fpdf`). Rather than add a new dependency for a mock-scope
export, this writes the smallest valid PDF object graph by hand: one
Catalog, one Pages tree, one Page + one content stream per page, and a
shared Helvetica font — enough for `pypdf.PdfReader` (or any compliant
reader) to parse it back and extract the text (see
docs/32-guide-exports.md).
"""

import io

_PAGE_WIDTH = 612
_PAGE_HEIGHT = 792
_FONT_SIZE = 11
_LINE_HEIGHT = 14
_MARGIN_LEFT = 50
_TOP_Y = 750


def _escape(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return escaped.encode("latin-1", errors="replace")


def build_minimal_pdf(lines: list[str], *, lines_per_page: int = 45) -> bytes:
    pages_lines = [lines[i : i + lines_per_page] for i in range(0, len(lines), lines_per_page)]
    if not pages_lines:
        pages_lines = [[]]
    num_pages = len(pages_lines)

    page_obj_nums = [3 + 2 * i for i in range(num_pages)]
    content_obj_nums = [4 + 2 * i for i in range(num_pages)]
    font_obj_num = 3 + 2 * num_pages

    kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
    bodies: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: f"<< /Type /Pages /Kids [{kids}] /Count {num_pages} >>".encode(),
    }

    for i, page_lines in enumerate(pages_lines):
        page_num = page_obj_nums[i]
        content_num = content_obj_nums[i]
        bodies[page_num] = (
            f"<< /Type /Page /Parent 2 0 R "
            f"/Resources << /Font << /F1 {font_obj_num} 0 R >> >> "
            f"/MediaBox [0 0 {_PAGE_WIDTH} {_PAGE_HEIGHT}] /Contents {content_num} 0 R >>"
        ).encode()

        stream_parts = [
            b"BT",
            f"/F1 {_FONT_SIZE} Tf".encode(),
            f"{_MARGIN_LEFT} {_TOP_Y} Td".encode(),
        ]
        for index, line in enumerate(page_lines):
            if index > 0:
                stream_parts.append(f"0 -{_LINE_HEIGHT} Td".encode())
            stream_parts.append(b"(" + _escape(line) + b") Tj")
        stream_parts.append(b"ET")
        stream_body = b"\n".join(stream_parts)
        bodies[content_num] = (
            f"<< /Length {len(stream_body)} >>\nstream\n".encode() + stream_body + b"\nendstream"
        )

    bodies[font_obj_num] = (
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
    )

    max_obj_num = font_obj_num
    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n")
    offsets: dict[int, int] = {}
    for obj_num in range(1, max_obj_num + 1):
        offsets[obj_num] = buffer.tell()
        buffer.write(f"{obj_num} 0 obj\n".encode())
        buffer.write(bodies[obj_num])
        buffer.write(b"\nendobj\n")

    xref_offset = buffer.tell()
    buffer.write(f"xref\n0 {max_obj_num + 1}\n".encode())
    buffer.write(b"0000000000 65535 f \n")
    for obj_num in range(1, max_obj_num + 1):
        buffer.write(f"{offsets[obj_num]:010d} 00000 n \n".encode())
    trailer = (
        f"trailer\n<< /Size {max_obj_num + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    )
    buffer.write(trailer.encode())
    return buffer.getvalue()
