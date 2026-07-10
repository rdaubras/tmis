from dataclasses import dataclass, field
from enum import Enum


class BlockType(str, Enum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    SIGNATURE = "signature"
    ANNEX = "annex"
    FOOTNOTE = "footnote"
    HEADER = "header"
    FOOTER = "footer"


@dataclass(frozen=True, slots=True)
class LayoutBlock:
    """A single structural unit of a document, in reading order."""

    order: int
    type: BlockType
    content: str
    page_number: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)
