from dataclasses import dataclass, field

from tmis.document_intelligence.schemas.classification import ClassificationResult
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.entities import ExtractedEntity
from tmis.document_intelligence.schemas.layout import LayoutBlock
from tmis.document_intelligence.schemas.metadata import DocumentMetadata
from tmis.document_intelligence.schemas.timeline import TimelineEvent


@dataclass
class DocumentRecord:
    """Everything the pipeline persists for a document (see
    docs/14-document-intelligence.md — Storage): original bytes, OCR text,
    structure, metadata, entities, timeline, chunk references (the actual
    vectors live in the vector store — only their chunk ids are kept
    here) and the processing status.
    """

    document_id: str
    filename: str
    status: ProcessingStatus
    raw_bytes: bytes
    ocr_text: str = ""
    layout_blocks: list[LayoutBlock] = field(default_factory=list)
    classification: ClassificationResult | None = None
    metadata: DocumentMetadata | None = None
    entities: list[ExtractedEntity] = field(default_factory=list)
    timeline_events: list[TimelineEvent] = field(default_factory=list)
    chunk_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
