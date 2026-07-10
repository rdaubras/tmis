from typing import Protocol

from tmis.document_intelligence.schemas.classification import ClassificationResult


class ClassifierPort(Protocol):
    """Port implemented by every interchangeable document classifier."""

    def classify(self, text: str) -> ClassificationResult: ...
