from dataclasses import dataclass
from enum import Enum


class EvidenceConfidence(str, Enum):
    """How strongly a document supports a fact."""

    DIRECT = "direct"
    CORROBORATING = "corroborating"
    CIRCUMSTANTIAL = "circumstantial"
    WEAK = "weak"


@dataclass(frozen=True, slots=True)
class EvidenceLink:
    fact_id: str
    document_id: str
    confidence: EvidenceConfidence
