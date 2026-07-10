from dataclasses import dataclass
from enum import Enum


class DocumentCategory(str, Enum):
    CONTRACT = "contract"
    JUDGMENT = "judgment"
    WRIT_OF_SUMMONS = "writ_of_summons"
    PLEADINGS = "pleadings"
    LETTER = "letter"
    EXHIBIT = "exhibit"
    INVOICE = "invoice"
    EMAIL = "email"
    CASE_LAW = "case_law"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    category: DocumentCategory
    confidence: float
    matched_keywords: tuple[str, ...] = ()
