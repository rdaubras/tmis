from dataclasses import dataclass
from enum import Enum


class SearchResultKind(str, Enum):
    DOCUMENT = "document"
    FACT = "fact"
    ACTOR = "actor"
    EVENT = "event"
    METADATA = "metadata"
    REFERENCE = "reference"


@dataclass(frozen=True, slots=True)
class CaseSearchResult:
    kind: SearchResultKind
    id: str
    label: str
    score: float
