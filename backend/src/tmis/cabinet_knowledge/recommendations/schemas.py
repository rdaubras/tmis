from dataclasses import dataclass

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType


@dataclass(frozen=True, slots=True)
class RecommendationContext:
    domain_tag: str | None = None
    keywords: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Recommendation:
    knowledge_object_id: str
    object_type: KnowledgeType
    title: str
    score: float
    explanation: str
