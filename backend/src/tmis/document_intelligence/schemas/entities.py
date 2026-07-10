from dataclasses import dataclass
from enum import Enum


class EntityType(str, Enum):
    PERSON = "person"
    COMPANY = "company"
    JURISDICTION = "jurisdiction"
    ADDRESS = "address"
    DATE = "date"
    AMOUNT = "amount"
    REFERENCE = "reference"
    NUMBER = "number"
    LAW_ARTICLE = "law_article"
    DECISION_REFERENCE = "decision_reference"


@dataclass(frozen=True, slots=True)
class ExtractedEntity:
    type: EntityType
    value: str
    confidence: float
    span_start: int | None = None
    span_end: int | None = None
