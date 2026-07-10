from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OcrResult:
    text: str
    confidence: float
    engine: str
    language: str | None = None
