from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CommentTargetType(str, Enum):
    CASE = "case"
    DOCUMENT = "document"
    SECTION = "section"
    PARAGRAPH = "paragraph"
    TASK = "task"


@dataclass(slots=True)
class Comment:
    """A comment attached to any addressable target in TMIS — a
    dossier, a document, a section, a paragraph, or a task (see
    docs/33-legal-collaboration.md — Comment Engine). `parent_id` makes
    a comment a reply, forming a thread; `attachment_ids` are opaque
    references to files uploaded elsewhere."""

    id: str
    workspace_id: str
    target_type: CommentTargetType
    target_id: str
    author_id: str
    text: str
    parent_id: str | None = None
    attachment_ids: tuple[str, ...] = field(default_factory=tuple)
    created_at: datetime | None = None
