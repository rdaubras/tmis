class DocumentValidationError(Exception):
    """Raised when an uploaded file fails validation (size, empty content,
    unrecognized/unsupported content type) before entering the pipeline."""


class VirusDetectedError(Exception):
    """Raised by a `VirusScanPort` implementation when a file is flagged
    as malicious. The default `NullVirusScanner` never raises this — it
    only proves the interface (see docs/14-document-intelligence.md)."""

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(f"Virus scan rejected {filename!r}: {reason}")
        self.filename = filename
        self.reason = reason


class UnsupportedContentTypeError(Exception):
    """Raised when no registered parser supports a given content type."""

    def __init__(self, content_type: str) -> None:
        super().__init__(f"No parser registered for content type {content_type!r}")
        self.content_type = content_type
