class NullVirusScanner:
    """Implements `VirusScanPort` as a no-op.

    Sprint 3 scope: the pipeline always runs a virus scan step, but no
    real antivirus engine is connected yet (see
    docs/14-document-intelligence.md). Swapping in a real engine (e.g.
    ClamAV) means writing one more class behind `VirusScanPort` — no
    pipeline change required.
    """

    def scan(self, filename: str, raw_bytes: bytes) -> None:
        return None
