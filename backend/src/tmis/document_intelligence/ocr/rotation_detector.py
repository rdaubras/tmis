class NullRotationDetector:
    """Implements `RotationDetectorPort` as a placeholder.

    Sprint 3 scope: always reports 0 degrees. Real rotation detection
    (e.g. via image gradient analysis) is deferred — see
    docs/14-document-intelligence.md — but the pipeline already calls
    this port, so plugging in a real detector later needs no pipeline
    change.
    """

    def detect_rotation(self, raw_bytes: bytes) -> int:
        return 0
