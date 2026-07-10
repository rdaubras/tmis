import re
from collections import Counter

from tmis.document_intelligence.schemas.layout import BlockType, LayoutBlock

_PAGE_BREAK = "\x0c"

_LIST_RE = re.compile(r"^\s*([-*•]|\d+[.)]|[a-z][.)])\s+")
_SUBTITLE_RE = re.compile(r"^\s*(\d+(\.\d+)+|[A-Z]\.)\s+\S")
_TABLE_RE = re.compile(r"(\t|\s{3,}).+(\t|\s{3,})")
_FOOTNOTE_RE = re.compile(r"^\s*\(\d+\)\s+\S")
_SIGNATURE_RE = re.compile(
    r"\b(fait\s+à|lu\s+et\s+approuvé|signature|signé\s+par|pour\s+valoir\s+ce\s+que\s+de\s+droit)\b",
    re.IGNORECASE,
)
_ANNEX_RE = re.compile(r"^\s*(annexe|pièce\s+jointe|appendix)\b", re.IGNORECASE)

_MAX_TITLE_WORDS = 10


class HeuristicLayoutAnalyzer:
    """Implements `LayoutAnalyzerPort` with dependency-free pattern
    matching over plain text.

    A machine-learned layout model (operating on the original PDF/image
    geometry) is a natural future replacement behind the same port; this
    heuristic is enough to exercise classification, chunking and the
    knowledge graph end-to-end today (see docs/14-document-intelligence.md).
    """

    def analyze(self, text: str) -> list[LayoutBlock]:
        pages = text.split(_PAGE_BREAK)
        header_candidates, footer_candidates = self._repeated_edge_lines(pages)

        blocks: list[LayoutBlock] = []
        order = 0
        for page_number, page in enumerate(pages, start=1):
            lines = [line for line in page.splitlines() if line.strip()]
            for index, line in enumerate(lines):
                stripped = line.strip()
                block_type = self._classify_line(
                    stripped,
                    is_first_line=index == 0,
                    is_last_line=index == len(lines) - 1,
                    header_candidates=header_candidates,
                    footer_candidates=footer_candidates,
                )
                blocks.append(
                    LayoutBlock(
                        order=order,
                        type=block_type,
                        content=stripped,
                        page_number=page_number,
                    )
                )
                order += 1
        return blocks

    def _repeated_edge_lines(self, pages: list[str]) -> tuple[set[str], set[str]]:
        if len(pages) < 2:
            return set(), set()
        first_lines: Counter[str] = Counter()
        last_lines: Counter[str] = Counter()
        for page in pages:
            lines = [line.strip() for line in page.splitlines() if line.strip()]
            if lines:
                first_lines[lines[0]] += 1
                last_lines[lines[-1]] += 1
        headers = {line for line, count in first_lines.items() if count >= 2}
        footers = {line for line, count in last_lines.items() if count >= 2}
        return headers, footers

    def _classify_line(
        self,
        line: str,
        *,
        is_first_line: bool,
        is_last_line: bool,
        header_candidates: set[str],
        footer_candidates: set[str],
    ) -> BlockType:
        if is_first_line and line in header_candidates:
            return BlockType.HEADER
        if is_last_line and line in footer_candidates:
            return BlockType.FOOTER
        if _SIGNATURE_RE.search(line):
            return BlockType.SIGNATURE
        if _ANNEX_RE.match(line):
            return BlockType.ANNEX
        if _FOOTNOTE_RE.match(line):
            return BlockType.FOOTNOTE
        if _LIST_RE.match(line):
            return BlockType.LIST
        if _TABLE_RE.search(line):
            return BlockType.TABLE
        if _SUBTITLE_RE.match(line):
            return BlockType.SUBTITLE
        word_count = len(line.split())
        has_letters = any(c.isalpha() for c in line)
        if has_letters and word_count <= _MAX_TITLE_WORDS and not line.endswith((".", ",", ";")):
            if line.isupper() or line.istitle():
                return BlockType.TITLE
        return BlockType.PARAGRAPH
