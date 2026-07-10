"""OCR abstraction: engines, language detection and rotation detection are
all interfaces first (see docs/16-guide-nouveau-moteur-ocr.md).

Sprint 3 scope: no proprietary/cloud OCR engine is wired yet — `engines/`
ships a passthrough engine (for documents that already have extractable
text) and a null engine (placeholder for scanned images), so the pipeline
handles OCR uniformly regardless of source, ready for a real engine to be
plugged in later without touching the pipeline.
"""
