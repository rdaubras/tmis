from dataclasses import dataclass
from typing import Any

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeType


@dataclass(frozen=True, slots=True)
class LessonLearned:
    id: str
    title: str
    context: str
    outcome: str
    recommendation: str
    related_case_reference: str | None = None


def lesson_to_content(lesson: LessonLearned) -> dict[str, Any]:
    return {
        "context": lesson.context,
        "outcome": lesson.outcome,
        "recommendation": lesson.recommendation,
        "related_case_reference": lesson.related_case_reference,
    }


def lesson_from_knowledge_object(obj: KnowledgeObject) -> LessonLearned:
    if obj.type is not KnowledgeType.LESSON_LEARNED:
        raise ValueError(f"{obj.id} is not a lesson learned (type={obj.type.value})")
    return LessonLearned(
        id=obj.id,
        title=obj.title,
        context=obj.content["context"],
        outcome=obj.content["outcome"],
        recommendation=obj.content["recommendation"],
        related_case_reference=obj.content.get("related_case_reference"),
    )
