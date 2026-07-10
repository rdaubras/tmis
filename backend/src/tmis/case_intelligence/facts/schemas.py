from dataclasses import dataclass, field


@dataclass
class Fact:
    """A fact asserted by at least one document of the case.

    Mutable: `FactEngine` adds corroborating/contradicting document ids
    in place as new documents are processed.
    """

    id: str
    description: str
    confidence: float
    dates: tuple[str, ...] = ()
    source_document_ids: set[str] = field(default_factory=set)
    confirming_document_ids: set[str] = field(default_factory=set)
    contradicting_document_ids: set[str] = field(default_factory=set)
