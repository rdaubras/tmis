import re
import unicodedata

from tmis.ai.rag.ports import RawDocument

_WHITESPACE_RE = re.compile(r"\s+")


class WhitespaceNormalizingCleaner:
    """Implements `CleanerPort`: Unicode normalization and whitespace
    collapsing, the two normalizations every source needs regardless of
    its origin (OCR artifacts are handled upstream)."""

    def clean(self, document: RawDocument) -> RawDocument:
        normalized = unicodedata.normalize("NFKC", document.content)
        collapsed = _WHITESPACE_RE.sub(" ", normalized).strip()
        return RawDocument(id=document.id, content=collapsed, metadata=document.metadata)
