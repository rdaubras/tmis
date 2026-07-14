from dataclasses import dataclass
from enum import StrEnum


class IngestionSourceType(StrEnum):
    """The six sources the Sprint 25 prompt asks the pipeline to
    support: documents internes, modèles, contrats, analyses, notes,
    jurisprudences importées."""

    INTERNAL_DOCUMENT = "internal_document"
    TEMPLATE = "template"
    CONTRACT = "contract"
    ANALYSIS = "analysis"
    NOTE = "note"
    IMPORTED_JURISPRUDENCE = "imported_jurisprudence"


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """What each step of Import→Extraction→Classification→
    Enrichment→Validation→Publication produced, for the caller (or a
    demo report) to inspect without re-querying every engine."""

    knowledge_object_id: str
    graph_node_id: str
    extracted_entity_labels: tuple[str, ...]
    classification_category: str
    classification_confidence: float
    validation_request_id: str
