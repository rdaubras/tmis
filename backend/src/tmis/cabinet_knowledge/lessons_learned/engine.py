from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.lessons_learned.schemas import (
    LessonLearned,
    lesson_from_knowledge_object,
    lesson_to_content,
)


class LessonLearnedEngine:
    def __init__(self, knowledge_space: KnowledgeSpace) -> None:
        self._knowledge_space = knowledge_space

    def create(
        self,
        firm_id: str,
        title: str,
        context: str,
        outcome: str,
        recommendation: str,
        author: str,
        related_case_reference: str | None = None,
    ) -> LessonLearned:
        shell = LessonLearned(
            id="",
            title=title,
            context=context,
            outcome=outcome,
            recommendation=recommendation,
            related_case_reference=related_case_reference,
        )
        obj = self._knowledge_space.create(
            firm_id,
            KnowledgeType.LESSON_LEARNED,
            title,
            lesson_to_content(shell),
            author,
        )
        return lesson_from_knowledge_object(obj)

    def get(self, firm_id: str, lesson_id: str) -> LessonLearned:
        obj = self._knowledge_space.get(firm_id, lesson_id)
        if obj is None:
            raise KeyError(lesson_id)
        return lesson_from_knowledge_object(obj)

    def list(self, firm_id: str, keyword: str | None = None) -> list[LessonLearned]:
        objects = self._knowledge_space.list(firm_id, type_=KnowledgeType.LESSON_LEARNED)
        lessons = [lesson_from_knowledge_object(obj) for obj in objects]
        if keyword is not None:
            needle = keyword.lower()
            lessons = [
                lesson
                for lesson in lessons
                if needle in lesson.title.lower() or needle in lesson.context.lower()
            ]
        return lessons
