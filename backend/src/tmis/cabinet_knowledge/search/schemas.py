from dataclasses import dataclass

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType


@dataclass(frozen=True, slots=True)
class SearchQuery:
    type: KnowledgeType | None = None
    status: KnowledgeStatus | None = None
    tag: str | None = None
    keyword: str | None = None
    published_only: bool = False
