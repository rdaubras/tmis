import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class KnowledgeType(StrEnum):
    PLAYBOOK = "playbook"
    CLAUSE = "clause"
    TEMPLATE = "template"
    REASONING_PATTERN = "reasoning_pattern"
    WRITING_STYLE = "writing_style"
    BEST_PRACTICE = "best_practice"
    LESSON_LEARNED = "lesson_learned"
    NOTE = "note"
    CHECKLIST = "checklist"
    GUIDE = "guide"
    INTERNAL_RULE = "internal_rule"
    JURISPRUDENCE_NOTE = "jurisprudence_note"
    COMMENT = "comment"
    DECISION = "decision"
    # Added in Sprint 25 (Legal Knowledge Graph) — a whole ingested
    # contract has no equivalent among the existing types (CLAUSE is
    # only ever one clause, never the whole document).
    CONTRACT = "contract"


class KnowledgeStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    VALIDATED = "validated"
    OBSOLETE = "obsolete"
    ARCHIVED = "archived"


def new_knowledge_id() -> str:
    return f"know-{uuid.uuid4()}"


@dataclass(slots=True)
class KnowledgeObject:
    """The generic, extensible unit of cabinet knowledge (see the
    sprint's "KNOWLEDGE OBJECT" spec). Every specialized concept
    (playbook, clause, template, reasoning pattern, ...) is stored as
    one of these, with `content` holding the type-specific payload —
    the specialized modules only add typed (de)serialization and
    business behavior on top, so the storage/versioning/governance/
    tenant-isolation machinery is never duplicated per type."""

    id: str
    firm_id: str
    type: KnowledgeType
    title: str
    content: dict[str, Any]
    author: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 1
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    quality_score: float = 0.0
    tags: frozenset[str] = field(default_factory=frozenset)
    relations: tuple[str, ...] = ()
    is_published: bool = False
    usage_count: int = 0
