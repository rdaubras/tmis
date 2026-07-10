from tmis.document_intelligence.ingestion.exceptions import DocumentValidationError

DEFAULT_MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class DocumentValidator:
    """First pipeline stage: rejects empty files and files over the
    configured size limit before any parsing/OCR/AI work is spent on
    them."""

    def __init__(self, max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES) -> None:
        self._max_size_bytes = max_size_bytes

    def validate(self, filename: str, raw_bytes: bytes) -> None:
        if not raw_bytes:
            raise DocumentValidationError(f"{filename!r} is empty")
        if len(raw_bytes) > self._max_size_bytes:
            raise DocumentValidationError(
                f"{filename!r} exceeds the maximum size of "
                f"{self._max_size_bytes} bytes ({len(raw_bytes)} bytes)"
            )
